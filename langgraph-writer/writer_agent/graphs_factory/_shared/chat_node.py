"""通用聊天节点：把「调用 LLM(绑定工具)、维护 messages/history」的逻辑抽出来供各图复用。

同时提供 chatbot ⇄ tools 的交互式子图构建器（最终输出时 interrupt，用户确认后结束或继续）。
"""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt


def make_chat_node(llm_with_tools):
    def chat_node(state: dict) -> dict:
        messages = state.get("messages") or []
        if messages and isinstance(messages[-1], ToolMessage):
            state["history"] = (state.get("history") or []) + [messages[-1]]
        out = llm_with_tools.invoke(messages)
        state["messages"] = [out]
        state["history"] = (state.get("history") or []) + [out]
        return state
    return chat_node


def build_tool_loop(
    name: str,
    tool_names: list[str],
    llm: ChatOpenAI,
    tools: list[BaseTool],
    state_cls: type,
    after_tools_message: str = "工具执行完毕，请确认结果",
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    node_chat = f"{name}_chatbot"
    node_tools = f"{name}_tools"
    node_finish = f"{name}_finish"

    picked = [t for t in tools if t.name in set(tool_names)]
    chat_node = make_chat_node(llm.bind_tools(picked))
    tool_node = ToolNode(tools=picked)

    def finish_node(state: dict) -> dict:
        messages = state.get("messages") or []
        final_result = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                final_result = msg.content if isinstance(msg.content, str) else str(msg.content)
                break

        user_feedback = interrupt({
            "message": after_tools_message,
            "result": final_result,
        })

        if user_feedback and str(user_feedback).strip().lower() in ("pass", "通过", "ok", "yes", "y", "确认"):
            state["_subgraph_done"] = True
        else:
            feedback_msg = HumanMessage(content=f"用户反馈：{user_feedback}\n请根据反馈继续修改。")
            state["messages"] = [feedback_msg]
            state["history"] = (state.get("history") or []) + [feedback_msg]
            state["_subgraph_done"] = False
        return state

    def route_after_finish(state: dict) -> str:
        if state.get("_subgraph_done"):
            return END
        return node_chat

    builder = StateGraph(state_cls)
    builder.add_node(node_chat, chat_node)
    builder.add_node(node_tools, tool_node)
    builder.add_node(node_finish, finish_node)

    builder.add_conditional_edges(node_chat, tools_condition, {"tools": node_tools, END: node_finish})
    builder.add_edge(node_tools, node_chat)
    builder.add_conditional_edges(node_finish, route_after_finish, {node_chat: node_chat, END: END})

    builder.set_entry_point(node_chat)

    if checkpoint is not None:
        return builder.compile(checkpointer=checkpoint)
    return builder.compile()
