"""通用「LLM + 工具」聊天图（对齐 LangGraph-Chatchat base_agent.BaseAgentGraph）。

图结构：history_manager → intent_recognition → 遍历子图 → 收集结果 → chatbot

原始 6 个 opencode agent 全部继承本类，只差三样东西：
- `system_prompt`：该 agent 的职责/调度/纪律 prompt（源自 `.opencode/agent/*.md`）;
- `tool_names`：该 agent 可用的工具清单（"*" 表示全部, 即「一站式 / 全能调度」）;
- `name` / `title`：注册键。
"""

from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt

from ..state import WriterState
from .graphs_registry import Graph, register_graph

MAX_CLARIFICATION_ATTEMPTS = 3

FALLBACK_INTENTS = {"设计", "审稿", "修改", "评估", "包装"}


class BaseAgentGraph(Graph):
    name = ""
    label = "agent"
    title = ""
    system_prompt = ""
    tool_names: list[str] = ["*"]

    SUBGRAPH_CONFIG: dict[str, dict] = {}

    def __init__(self,
                 llm: ChatOpenAI,
                 tools: list[BaseTool],
                 history_len: int,
                 checkpoint: BaseCheckpointSaver,
                 system_prompt: str | None = None):
        super().__init__(llm, tools, history_len, checkpoint)

        cfg = (self.SUBGRAPH_CONFIG or {}).copy()
        known = set(cfg.keys()) | FALLBACK_INTENTS
        lines = []
        for k, v in cfg.items():
            lines.append(f"- {k}：{v.get('description', '')}")
        for i in sorted(FALLBACK_INTENTS):
            if i not in cfg:
                lines.append(f"- {i}：待补充描述")

        intent_prompt_text = f"""你是一个意图识别助手。根据用户输入，识别用户的意图并输出意图列表。

可选意图：
{chr(10).join(lines)}

输出要求：只输出一个JSON数组，不要输出任何其他文字、解释或Markdown代码块。
示例：
用户：我想开新书，帮我找点灵感 -> ["构思"]
用户：先写大纲再写第一章 -> ["设计", "创作"]
用户：检查一下有没有AI痕迹 -> ["审稿"]
如果用户输入不明确（如闲聊、问候），输出 []"""

        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", intent_prompt_text),
            ("placeholder", "{history}"),
        ])
        self.llm_with_intent = self.intent_prompt | self.llm

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt or self.system_prompt),
            ("placeholder", "{history}"),
        ])
        self.llm_with_tools = prompt | self.llm.bind_tools(self.tools)

        self._valid_intents: set[str] = known
        self._subgraphs: dict[str, CompiledStateGraph] = {}
        for intent, sub_cfg in cfg.items():
            self._subgraphs[intent] = self._build_interactive_subgraph(sub_cfg["tools"])

    # ------------------------------------------------------------------
    # 子图工厂
    # ------------------------------------------------------------------
    def _build_interactive_subgraph(self, tool_names: list[str]) -> CompiledStateGraph:
        tools = [self._get_tool(n) for n in tool_names]
        sub_llm = self.llm.bind_tools(tools)
        sub_tool_node = ToolNode(tools=tools)

        def sub_chatbot(state: WriterState) -> WriterState:
            out = sub_llm.invoke(state)
            state["messages"] = [out]
            return state

        def sub_after_tools(state: WriterState) -> WriterState:
            interrupt("工具执行完毕，请查看结果并继续")
            return state

        sub_builder = StateGraph(WriterState)
        sub_builder.add_node("sub_chatbot", sub_chatbot)
        sub_builder.add_node("sub_tools", sub_tool_node)
        sub_builder.add_node("sub_after_tools", sub_after_tools)

        sub_builder.add_conditional_edges(
            "sub_chatbot", tools_condition,
            {"tools": "sub_tools", END: END},
        )
        sub_builder.add_edge("sub_tools", "sub_after_tools")
        sub_builder.add_edge("sub_after_tools", "sub_chatbot")
        return sub_builder.compile()

    # ------------------------------------------------------------------
    # 历史管理
    # ------------------------------------------------------------------
    def history_manager(self, state: WriterState) -> WriterState:
        from langchain_core.messages import filter_messages

        try:
            filtered_messages = []
            for message in filter_messages(state["messages"], exclude_types=[ToolMessage]):
                if isinstance(message, AIMessage) and message.tool_calls:
                    continue
                filtered_messages.append(message)
            state["history"] = filtered_messages[-self.history_len:]
            return state
        except Exception as e:
            raise Exception(f"Filtering messages error: {e}")

    # ------------------------------------------------------------------
    # 意图识别
    # ------------------------------------------------------------------
    def _parse_intents(self, content) -> list[str]:
        import json
        import re

        if isinstance(content, list):
            content = "".join(
                b.get("text", "") if isinstance(b, dict) else str(b) for b in content
            )
        content = str(content or "").strip()
        content = re.sub(r"```(?:json)?|```", "", content).strip()

        match = re.search(r"\[[^\[\]]*\]", content, re.S)
        if not match:
            return []
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return [i for i in self._valid_intents if i in content]
        if not isinstance(parsed, list):
            return []
        return [i for i in parsed if isinstance(i, str) and i in self._valid_intents]

    def intent_recognition(self, state: WriterState) -> WriterState:
        try:
            response = self.llm_with_intent.invoke(state)
            intents = self._parse_intents(response.content)
            state["intent_list"] = intents
            state["current_intent"] = intents[0] if intents else ""
            state["intent_index"] = 0
            state["intent_results"] = {}
            if intents:
                state["clarification_attempts"] = 0
            else:
                state["clarification_attempts"] = state.get("clarification_attempts", 0) + 1
            return state
        except Exception as e:
            raise Exception(f"Intent recognition error: {e}")

    def check_intent(self, state: WriterState) -> Literal["ask_clarification", "loop"]:
        if not state.get("intent_list"):
            return "ask_clarification"
        return "loop"

    def check_clarification_limit(self, state: WriterState) -> Literal["ask_clarification", "end"]:
        if state.get("clarification_attempts", 0) >= MAX_CLARIFICATION_ATTEMPTS:
            return "end"
        return "ask_clarification"

    def ask_clarification(self, state: WriterState) -> WriterState:
        options = "\n".join(
            f"- {k}：{v['description']}" for k, v in (self.SUBGRAPH_CONFIG or {}).items()
        )
        msg = AIMessage(content=f"我不太确定你想做什么，请告诉我更具体的需求，比如：\n{options}\n- 其他")
        state["messages"] = [msg]
        state["history"].append(msg)
        return state

    def end_conversation(self, state: WriterState) -> WriterState:
        msg = AIMessage(content="抱歉，我无法识别你的意图。请尝试更具体的描述，或者输入 /exit 退出。")
        state["messages"] = [msg]
        state["history"].append(msg)
        return state

    # ------------------------------------------------------------------
    # 子图分派
    # ------------------------------------------------------------------
    def route_after_intent(self, state: WriterState) -> str:
        if not state.get("intent_list"):
            return "ask_clarification"
        return "dispatch_next"

    def dispatch_next(self, state: WriterState) -> WriterState:
        intents = state.get("intent_list") or []
        idx = state.get("intent_index", 0)
        if idx < len(intents):
            state["current_intent"] = intents[idx]
            state["intent_index"] = idx + 1
        else:
            state["current_intent"] = ""
        return state

    def route_dispatch(self, state: WriterState) -> str:
        intent = state.get("current_intent")
        if not intent:
            return "collect_results"
        sub_cfg = (self.SUBGRAPH_CONFIG or {}).get(intent)
        return sub_cfg["node_name"] if sub_cfg else "subgraph_generic"

    def execute_subgraph(self, state: WriterState) -> WriterState:
        intent = state.get("current_intent", "")
        results = dict(state.get("intent_results") or {})
        results[intent] = f"「{intent}」子图尚未实装（占位）。本轮识别意图：{state.get('intent_list')}"
        state["intent_results"] = results
        return state

    def collect_results(self, state: WriterState) -> WriterState:
        results = state.get("intent_results", {})
        if results:
            result_text = "\n".join([f"【{k}】{v}" for k, v in results.items()])
        else:
            result_text = "（本轮无子任务产出）"
        state["task"] = result_text
        state["history"] = (state.get("history") or []) + [
            HumanMessage(content=f"以下是子图/工具产出，请据此并结合用户问题作答：\n{result_text}")
        ]
        return state

    # ------------------------------------------------------------------
    # 工具辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _last_human_text(state: WriterState) -> str:
        for m in reversed(state.get("messages") or []):
            if isinstance(m, HumanMessage):
                return m.content if isinstance(m.content, str) else str(m.content)
        return ""

    def _get_tool(self, name: str) -> BaseTool:
        for t in self.tools:
            if t.name == name:
                return t
        from ..tools_factory import get_tool
        return get_tool(name)

    # ------------------------------------------------------------------
    # chatbot
    # ------------------------------------------------------------------
    def chatbot(self, state: WriterState) -> WriterState:
        if state.get("messages") and isinstance(state["messages"][-1], ToolMessage):
            state["history"] = (state.get("history") or []) + [state["messages"][-1]]

        messages = self.llm_with_tools.invoke(state)
        state["messages"] = [messages]
        state["history"] = (state.get("history") or []) + [messages]
        return state

    # ------------------------------------------------------------------
    # 主图装配
    # ------------------------------------------------------------------
    def get_graph(self) -> CompiledStateGraph:
        if not isinstance(self.llm, ChatOpenAI):
            raise TypeError("llm must be an instance of ChatOpenAI")
        if not all(isinstance(t, BaseTool) for t in self.tools):
            raise TypeError("All items in tools must be instances of BaseTool")

        builder = StateGraph(WriterState)

        builder.add_node("history_manager", self.history_manager)
        builder.add_node("intent_recognition", self.intent_recognition)
        builder.add_node("ask_clarification", self.ask_clarification)
        builder.add_node("dispatch_next", self.dispatch_next)
        builder.add_node("subgraph_generic", self.execute_subgraph)
        builder.add_node("collect_results", self.collect_results)
        builder.add_node("chatbot", self.chatbot)
        builder.add_node("tools", ToolNode(tools=self.tools))

        for intent, sub_cfg in (self.SUBGRAPH_CONFIG or {}).items():
            node_name = sub_cfg["node_name"]
            builder.add_node(node_name, self._subgraphs[intent])
            builder.add_edge(node_name, "dispatch_next")

        builder.set_entry_point("history_manager")
        builder.add_edge("history_manager", "intent_recognition")
        builder.add_conditional_edges(
            "intent_recognition",
            self.route_after_intent,
            {
                "ask_clarification": "ask_clarification",
                "dispatch_next": "dispatch_next",
            },
        )
        builder.add_edge("ask_clarification", END)
        builder.add_edge("subgraph_generic", "dispatch_next")
        builder.add_edge("collect_results", "chatbot")
        builder.add_conditional_edges("chatbot", tools_condition)
        builder.add_edge("tools", "chatbot")

        dispatch_map = {sub_cfg["node_name"]: sub_cfg["node_name"] for sub_cfg in (self.SUBGRAPH_CONFIG or {}).values()}
        dispatch_map["subgraph_generic"] = "subgraph_generic"
        dispatch_map["collect_results"] = "collect_results"
        builder.add_conditional_edges("dispatch_next", self.route_dispatch, dispatch_map)

        if self.checkpoint is not None:
            return builder.compile(checkpointer=self.checkpoint)
        return builder.compile()

    @staticmethod
    def handle_event(node: str, event: WriterState) -> BaseMessage:
        return event["messages"][-1]


ToolCallingAgentGraph = BaseAgentGraph


@register_graph
class NovelistGraph(BaseAgentGraph):
    SUBGRAPH_CONFIG = {
        "构思": {
            "node_name": "subgraph_brainstorm",
            "tools": ["story_brainstorm"],
            "description": "找灵感、定题材、开新书、讨论核心冲突",
        },
        "创作": {
            "node_name": "subgraph_draft",
            "tools": ["chapter_drafting", "add_setting"],
            "description": "写新章、续写正文、补充素材",
        },
    }

    name = "novelist"
    label = "agent"
    title = "小说家"
    tool_names = ["*"]
    system_prompt = (
        "你是「小说家」主 agent，负责统筹构思/设计/创作/审稿/修改/评估/包装等写作环节。"
        "你可以直接调用写作工具产出正文、大纲、设定、检查等内容。"
        "始终用中文回复，紧扣用户的写作需求，输出可直接使用的成品，不要空谈方法论。"
    )