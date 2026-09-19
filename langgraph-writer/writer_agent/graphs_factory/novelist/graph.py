"""通用「LLM + 工具」聊天图（对齐 LangGraph-Chatchat base_agent.BaseAgentGraph）。

图结构：history_manager → intent_recognition → 遍历子图 → 收集结果 → chatbot ⇄ tools

拓扑全部由类上的配置声明：NODES / EDGES / CONDITIONAL_EDGES / SUBGRAPHS。
加节点、加边、加子图只改配置，不用动 get_graph。
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from ...state import WriterState
from .._shared.chat_node import build_tool_loop, make_chat_node
from .._shared.registry import Graph, register_graph
from .configs import (
    NODES as CFG_NODES,
    ENTRY as CFG_ENTRY,
    EDGES as CFG_EDGES,
    ROUTES as CFG_ROUTES,
    CONDITIONAL_EDGES as CFG_CONDITIONAL_EDGES,
    STATE as CFG_STATE,
    SUBGRAPHS as CFG_SUBGRAPHS,
    MAX_CLARIFICATION_ATTEMPTS,
    FALLBACK_INTENTS,
)
from .prompts import (
    INTENT_PROMPT_TEMPLATE,
    INTENT_PROMPT_EXAMPLES,
    NOVELIST_SYSTEM_PROMPT,
)


class BaseAgentGraph(Graph):
    # ════════════════════════════════════════════════════════════════
    # 图配置（从 configs.py 导入）
    # ════════════════════════════════════════════════════════════════
    NODES = CFG_NODES
    ENTRY = CFG_ENTRY
    EDGES = CFG_EDGES
    ROUTES = CFG_ROUTES
    CONDITIONAL_EDGES = CFG_CONDITIONAL_EDGES
    STATE = CFG_STATE

    # ════════════════════════════════════════════════════════════════
    # 子类覆写
    # ════════════════════════════════════════════════════════════════
    name = ""
    label = "agent"
    title = ""
    system_prompt = ""
    tool_names: list[str] = ["*"]

    # 子图：意图 -> {"node_name", "tools", "description", "build_func"(可选)}
    SUBGRAPHS: dict[str, dict] = {}

    # ════════════════════════════════════════════════════════════════
    # __init__
    # ════════════════════════════════════════════════════════════════
    def __init__(self,
                 llm: ChatOpenAI,
                 tools: list[BaseTool],
                 history_len: int,
                 checkpoint: BaseCheckpointSaver,
                 system_prompt: str | None = None):
        super().__init__(llm, tools, history_len, checkpoint)

        cfg = self.SUBGRAPHS or {}
        known = set(cfg.keys()) | FALLBACK_INTENTS
        options = [f"- {k}：{v.get('description', '')}" for k, v in cfg.items()]
        options += [f"- {i}：待补充描述" for i in sorted(FALLBACK_INTENTS) if i not in cfg]

        intent_prompt_text = INTENT_PROMPT_TEMPLATE.format(
            intent_options="\n".join(options),
            intent_examples=INTENT_PROMPT_EXAMPLES,
        )
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", intent_prompt_text),
            ("placeholder", "{" + self.STATE["history"] + "}"),
        ])
        self.llm_with_intent = self.intent_prompt | self.llm

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt or self.system_prompt),
            ("placeholder", "{" + self.STATE["history"] + "}"),
        ])
        self.llm_with_tools = prompt | self.llm.bind_tools(self.tools)

        self._valid_intents: set[str] = known
        self._subgraphs: dict[str, CompiledStateGraph] = {}
        for intent, sub in cfg.items():
            builder = sub.get("build_func")
            if builder is not None:
                self._subgraphs[intent] = builder(self.llm, self.tools, self.checkpoint)
            else:
                self._subgraphs[intent] = build_tool_loop(
                    name=sub["node_name"],
                    tool_names=sub["tools"],
                    llm=self.llm,
                    tools=self.tools,
                    checkpoint=self.checkpoint,
                )

    # ------------------------------------------------------------------
    # 节点函数表（逻辑名 -> 可调用）
    # ------------------------------------------------------------------
    def _node_funcs(self) -> dict:
        return {
            "history": self.history_manager,
            "intent": self.intent_recognition,
            "clarify": self.ask_clarification,
            "dispatch": self.dispatch_next,
            "generic": self.execute_subgraph,
            "collect": self.collect_results,
            "chatbot": make_chat_node(self.llm_with_tools),
            "tools": ToolNode(tools=self.tools),
        }

    # ------------------------------------------------------------------
    # 历史管理
    # ------------------------------------------------------------------
    def history_manager(self, state: WriterState) -> WriterState:
        from langchain_core.messages import filter_messages

        try:
            filtered = []
            for message in filter_messages(state[self.STATE["messages"]], exclude_types=[ToolMessage]):
                if isinstance(message, AIMessage) and message.tool_calls:
                    continue
                filtered.append(message)
            state[self.STATE["history"]] = filtered[-self.history_len:]
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
        content = re.sub(r"```(?:json)?|```", "", str(content or "").strip()).strip()

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
            state[self.STATE["intents"]] = intents
            state[self.STATE["current"]] = intents[0] if intents else ""
            state[self.STATE["index"]] = 0
            state[self.STATE["results"]] = {}
            if intents:
                state[self.STATE["clarify_count"]] = 0
            else:
                state[self.STATE["clarify_count"]] = state.get(self.STATE["clarify_count"], 0) + 1
            return state
        except Exception as e:
            raise Exception(f"Intent recognition error: {e}")

    # ------------------------------------------------------------------
    # 追问 / 结束
    # ------------------------------------------------------------------
    def ask_clarification(self, state: WriterState) -> WriterState:
        options = "\n".join(f"- {k}：{v['description']}" for k, v in (self.SUBGRAPHS or {}).items())
        msg = AIMessage(content=f"我不太确定你想做什么，请告诉我更具体的需求，比如：\n{options}\n- 其他")
        state[self.STATE["messages"]] = [msg]
        state[self.STATE["history"]].append(msg)
        return state

    def end_conversation(self, state: WriterState) -> WriterState:
        msg = AIMessage(content="抱歉，我无法识别你的意图。请尝试更具体的描述，或者输入 /exit 退出。")
        state[self.STATE["messages"]] = [msg]
        state[self.STATE["history"]].append(msg)
        return state

    # ------------------------------------------------------------------
    # 子图分派
    # ------------------------------------------------------------------
    def route_after_intent(self, state: WriterState) -> str:
        if not state.get(self.STATE["intents"]):
            return self.ROUTES["clarify"]
        return self.ROUTES["dispatch"]

    def dispatch_next(self, state: WriterState) -> WriterState:
        intents = state.get(self.STATE["intents"]) or []
        idx = state.get(self.STATE["index"], 0)
        if idx < len(intents):
            state[self.STATE["current"]] = intents[idx]
            state[self.STATE["index"]] = idx + 1
        else:
            state[self.STATE["current"]] = ""
        return state

    def route_dispatch(self, state: WriterState) -> str:
        intent = state.get(self.STATE["current"])
        if not intent:
            return self.ROUTES["collect"]
        sub = (self.SUBGRAPHS or {}).get(intent)
        return sub["node_name"] if sub else self.ROUTES["generic"]

    def execute_subgraph(self, state: WriterState) -> WriterState:
        intent = state.get(self.STATE["current"], "")
        results = dict(state.get(self.STATE["results"]) or {})
        results[intent] = f"「{intent}」子图尚未实装（占位）。本轮识别意图：{state.get(self.STATE['intents'])}"
        state[self.STATE["results"]] = results
        return state

    def collect_results(self, state: WriterState) -> WriterState:
        results = state.get(self.STATE["results"], {})
        result_text = "\n".join(f"【{k}】{v}" for k, v in results.items()) if results else "（本轮无子任务产出）"
        state[self.STATE["task"]] = result_text
        state[self.STATE["history"]] = (state.get(self.STATE["history"]) or []) + [
            HumanMessage(content=f"以下是子图/工具产出，请据此并结合用户问题作答：\n{result_text}")
        ]
        return state

    # ------------------------------------------------------------------
    # 工具辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _last_human_text(state: WriterState) -> str:
        for m in reversed(state.get(BaseAgentGraph.STATE["messages"]) or []):
            if isinstance(m, HumanMessage):
                return m.content if isinstance(m.content, str) else str(m.content)
        return ""

    def _get_tool(self, name: str) -> BaseTool:
        for t in self.tools:
            if t.name == name:
                return t
        from ...tools_factory import get_tool
        return get_tool(name)

    # ------------------------------------------------------------------
    # 主图装配（读配置）
    # ------------------------------------------------------------------
    def get_graph(self) -> CompiledStateGraph:
        if not isinstance(self.llm, ChatOpenAI):
            raise TypeError("llm must be an instance of ChatOpenAI")
        if not all(isinstance(t, BaseTool) for t in self.tools):
            raise TypeError("All items in tools must be instances of BaseTool")

        builder = StateGraph(WriterState)
        funcs = self._node_funcs()
        for key, node in self.NODES.items():
            builder.add_node(node, funcs[key])

        # 子图节点 + 动态分派表
        dispatch_map = {
            self.NODES["generic"]: self.NODES["generic"],
            self.NODES["collect"]: self.NODES["collect"],
        }
        for intent, sub in (self.SUBGRAPHS or {}).items():
            node = sub["node_name"]
            builder.add_node(node, self._subgraphs[intent])
            builder.add_edge(node, self.NODES["dispatch"])
            dispatch_map[node] = node

        builder.set_entry_point(self.NODES[self.ENTRY])
        for src, dst in self.EDGES:
            builder.add_edge(self.NODES[src], END if dst is END else self.NODES[dst])

        for src, spec in self.CONDITIONAL_EDGES.items():
            router = spec["router"]
            fn = tools_condition if router is None else getattr(self, router)
            mapping = spec["map"]
            if mapping is None:
                builder.add_conditional_edges(self.NODES[src], fn)
            else:
                builder.add_conditional_edges(
                    self.NODES[src], fn, {k: self.NODES[v] for k, v in mapping.items()}
                )

        builder.add_conditional_edges(self.NODES["dispatch"], self.route_dispatch, dispatch_map)

        if self.checkpoint is not None:
            return builder.compile(checkpointer=self.checkpoint)
        return builder.compile()

    @staticmethod
    def handle_event(node: str, event: WriterState) -> BaseMessage:
        return event[BaseAgentGraph.STATE["messages"]][-1]


ToolCallingAgentGraph = BaseAgentGraph


@register_graph
class NovelistGraph(BaseAgentGraph):
    SUBGRAPHS = CFG_SUBGRAPHS

    name = "novelist"
    label = "agent"
    title = "小说家"
    tool_names = ["*"]
    system_prompt = NOVELIST_SYSTEM_PROMPT
