"""通用聊天节点：把「调用 LLM(绑定工具)、维护 messages/history」的逻辑抽出来供各图复用。

提供两种子图构建器：
1. build_tool_loop: 简单 chatbot ⇄ tools 循环
2. build_reason_loop: 带推理和动作执行的复杂循环
"""

import json
from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt
from pydantic import BaseModel, Field


def make_chat_node(llm_with_tools):
    def chat_node(state: dict) -> dict:
        messages = state.get("messages") or []
        if messages and isinstance(messages[-1], ToolMessage):
            state["history"] = (state.get("history") or []) + [messages[-1]]
        # 判断是链（需要 dict）还是原始 LLM（需要 messages 列表）
        try:
            out = llm_with_tools.invoke(state)
        except TypeError:
            out = llm_with_tools.invoke(messages)
        state["messages"] = [out]
        state["history"] = (state.get("history") or []) + [out]
        return state
    return chat_node


# ════════════════════════════════════════════════════════════════
# 推理循环专用 State
# ════════════════════════════════════════════════════════════════

class ReasonState(TypedDict, total=False):
    """推理循环状态：带调用次数限制和动作执行。"""
    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]
    task: str
    findings: str                    # 全局发现
    call_count: int                  # 当前调用次数
    max_calls: int                   # 最大调用次数
    is_complete: bool                # 任务是否完成
    pending_actions: List[dict]      # 待执行的动作列表
    current_observations: List[str]  # 本轮观测结果


class ActionOutput(BaseModel):
    """LLM 输出的动作集合。"""
    actions: list[dict] = Field(
        default_factory=list,
        description="动作列表，每个动作包含 type(query/ask) 和 content",
    )
    reasoning: str = Field(
        default="",
        description="推理过程说明",
    )
    is_complete: bool = Field(
        default=False,
        description="是否已完成任务",
    )


# ════════════════════════════════════════════════════════════════
# 推理循环构建器
# ════════════════════════════════════════════════════════════════

def build_reason_loop(
    name: str,
    tool_names: list[str],
    llm: ChatOpenAI,
    tools: list[BaseTool],
    state_cls: type,
    project_dir: str = "",
    max_calls: int = 10,
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """构建带推理和动作执行的循环子图。

    流程：
        check_limit → llm_reason → execute_actions → collect → analyze → check_complete
            → 完成 → generate_conclusion → END
            → 未完成 → check_limit（循环）

    Args:
        state_cls: 子图专用 State 类（必须传入）。
        project_dir: 项目目录路径。
        max_calls: 最大调用次数。
    """
    picked = [t for t in tools if t.name in set(tool_names)]
    _project_dir = project_dir

    def init_state(state: dict) -> dict:
        """初始化状态：设置项目目录。"""
        if _project_dir:
            state["project_dir"] = _project_dir
        if "call_count" not in state or state["call_count"] is None:
            state["call_count"] = 0
        if "max_calls" not in state or state["max_calls"] is None:
            state["max_calls"] = max_calls
        if "findings" not in state or state["findings"] is None:
            state["findings"] = ""
        if "is_complete" not in state or state["is_complete"] is None:
            state["is_complete"] = False
        if "pending_actions" not in state or state["pending_actions"] is None:
            state["pending_actions"] = []
        if "current_observations" not in state or state["current_observations"] is None:
            state["current_observations"] = []
        return state

    def check_limit(state: dict) -> dict:
        """检查调用次数是否超限。"""
        call_count = state.get("call_count", 0)
        if call_count >= max_calls:
            state["is_complete"] = True  # 强制结束
        return state

    def route_after_check(state: dict) -> str:
        if state.get("is_complete"):
            return f"{name}_conclusion"
        return f"{name}_reason"

    def llm_reason(state: dict) -> dict:
        """LLM 思考并输出动作集合。"""
        findings = state.get("findings", "")
        task = state.get("task", "")
        history = state.get("history") or []
        messages = state.get("messages") or []

        # 构建 prompt
        system_prompt = f"""你是{task}的执行助手。
当前发现：{findings}

可用工具：{[t.name for t in picked]}

请分析当前情况，决定下一步动作：
1. 如果需要查询信息，输出 query 类型动作
2. 如果需要问用户，输出 ask 类型动作
3. 如果任务完成，设置 is_complete=true"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{messages}"),
        ])

        try:
            llm_with_structured = prompt | llm.with_structured_output(ActionOutput)
            result = llm_with_structured.invoke({"messages": messages + history})
            state["pending_actions"] = [a for a in result.actions] if result.actions else []
            state["is_complete"] = result.is_complete
        except Exception as e:
            # LLM 调用失败时，标记完成并记录错误
            state["is_complete"] = True
            state["findings"] = f"LLM 调用失败: {e}"

        state["call_count"] = state.get("call_count", 0) + 1

        return state

    def execute_actions(state: dict) -> dict:
        """执行动作（查询或提问）。"""
        actions = state.get("pending_actions", []) or []
        observations = []

        for action in actions:
            action_type = action.get("type", "query")
            content = action.get("content", "")

            if action_type == "query":
                # 执行工具查询
                tool_name = action.get("tool", "")
                tool_input = action.get("input", content)
                for tool in picked:
                    if tool.name == tool_name:
                        try:
                            result = tool.invoke(tool_input)
                            observations.append(f"查询[{tool_name}]: {result}")
                        except Exception as e:
                            observations.append(f"查询[{tool_name}]失败: {e}")
                        break
                else:
                    observations.append(f"查询: {content}")

            elif action_type == "ask":
                # 向用户提问
                user_answer = interrupt({"message": content})
                observations.append(f"用户回答: {user_answer}")

        state["current_observations"] = observations
        return state

    def analyze_observations(state: dict) -> dict:
        """LLM 分析观测结果，更新全局发现。"""
        findings = state.get("findings", "")
        observations = state.get("current_observations", []) or []
        task = state.get("task", "")

        system_prompt = f"""你是{task}的分析助手。
当前全局发现：{findings}

本轮观测结果：
{json.dumps(observations, ensure_ascii=False, indent=2)}

请分析这些观测结果，更新全局发现。输出更新后的发现。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
        ])

        try:
            result = llm.invoke(prompt.format_messages())
            state["findings"] = result.content
        except Exception as e:
            state["findings"] = f"分析失败: {e}"

        state["pending_actions"] = []
        state["current_observations"] = []

        return state

    def generate_conclusion(state: dict) -> dict:
        """生成最终结论。"""
        findings = state.get("findings", "")
        task = state.get("task", "")

        system_prompt = f"""你是{task}的总结助手。
全局发现：{findings}

请根据以上发现，生成最终结论。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
        ])

        try:
            result = llm.invoke(prompt.format_messages())
            state["messages"] = [AIMessage(content=result.content)]
            state["history"] = (state.get("history") or []) + [result.content]
        except Exception as e:
            state["messages"] = [AIMessage(content=f"结论生成失败: {e}")]
            state["history"] = (state.get("history") or []) + [f"结论生成失败: {e}"]

        return state

    # 构建图
    builder = StateGraph(state_cls)

    builder.add_node(f"{name}_init", init_state)
    builder.add_node(f"{name}_check_limit", check_limit)
    builder.add_node(f"{name}_reason", llm_reason)
    builder.add_node(f"{name}_execute", execute_actions)
    builder.add_node(f"{name}_analyze", analyze_observations)
    builder.add_node(f"{name}_conclusion", generate_conclusion)

    builder.set_entry_point(f"{name}_init")
    builder.add_edge(f"{name}_init", f"{name}_check_limit")

    builder.add_conditional_edges(
        f"{name}_check_limit",
        route_after_check,
        {
            f"{name}_reason": f"{name}_reason",
            f"{name}_conclusion": f"{name}_conclusion",
        }
    )

    builder.add_edge(f"{name}_reason", f"{name}_execute")
    builder.add_edge(f"{name}_execute", f"{name}_analyze")
    builder.add_conditional_edges(
        f"{name}_analyze",
        lambda state: f"{name}_check_limit" if not state.get("is_complete") else f"{name}_conclusion",
        {
            f"{name}_check_limit": f"{name}_check_limit",
            f"{name}_conclusion": f"{name}_conclusion",
        }
    )
    builder.add_edge(f"{name}_conclusion", END)

    if checkpoint is not None:
        return builder.compile(checkpointer=checkpoint)
    return builder.compile()


def build_tool_loop(
    name: str,
    tool_names: list[str],
    llm: ChatOpenAI,
    tools: list[BaseTool],
    state_cls: type,
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """构建 chatbot ⇄ tools 循环，自动运行到 END。

    流程：chatbot → 有工具调用 → tools → chatbot → ... → 无工具调用 → END
    """
    node_chat = f"{name}_chatbot"
    node_tools = f"{name}_tools"

    picked = [t for t in tools if t.name in set(tool_names)]
    chat_node = make_chat_node(llm.bind_tools(picked))
    tool_node = ToolNode(tools=picked)

    builder = StateGraph(state_cls)
    builder.add_node(node_chat, chat_node)
    builder.add_node(node_tools, tool_node)

    builder.add_conditional_edges(node_chat, tools_condition, {"tools": node_tools, END: END})
    builder.add_edge(node_tools, node_chat)

    builder.set_entry_point(node_chat)

    if checkpoint is not None:
        return builder.compile(checkpointer=checkpoint)
    return builder.compile()
