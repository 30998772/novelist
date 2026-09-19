"""通用「LLM + 工具」聊天图（对齐 LangGraph-Chatchat base_agent.BaseAgentGraph）。

图结构：history_manager → intent_recognition → 遍历子图 → 收集结果 → chatbot(格式化)

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

from ...logging import get_logger
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
    NovelistState,
)
from .prompts import (
    INTENT_PROMPT_TEMPLATE,
    INTENT_OUTPUT_SCHEMA,
    NOVELIST_SYSTEM_PROMPT,
)

logger = get_logger("novelist")


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

        # 意图识别：JSON Schema 强制输出
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_PROMPT_TEMPLATE),
            ("placeholder", "{" + self.STATE["history"] + "}"),
        ])
        self.llm_with_intent = self.intent_prompt | self.llm.with_structured_output(
            INTENT_OUTPUT_SCHEMA,
            method="json_mode",
        )

        # 主聊天：格式化回复，不绑定工具
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt or self.system_prompt),
            ("placeholder", "{" + self.STATE["history"] + "}"),
        ])
        self.llm_with_chatbot = prompt | self.llm

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

        logger.info(
            "BaseAgentGraph initialized: name=%s, valid_intents=%s, subgraphs=%s",
            self.name, self._valid_intents, list(cfg.keys()),
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
            "chatbot": make_chat_node(self.llm_with_chatbot),
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
            logger.debug("history_manager: filtered %d messages, kept %d",
                         len(state[self.STATE["messages"]]), len(state[self.STATE["history"]]))
            return state
        except Exception as e:
            logger.error("history_manager failed: %s", e)
            raise Exception(f"Filtering messages error: {e}")

    # ------------------------------------------------------------------
    # 意图识别（JSON Schema）
    # ------------------------------------------------------------------
    def intent_recognition(self, state: WriterState) -> WriterState:
        try:
            history = state.get(self.STATE["history"]) or []
            last_human = ""
            for msg in reversed(history):
                if isinstance(msg, HumanMessage):
                    last_human = msg.content if isinstance(msg.content, str) else str(msg.content)
                    break
            logger.info("intent_recognition: user input = %s", repr(last_human[:200]))

            result = self.llm_with_intent.invoke(state)
            raw_intents = result.get("intents", []) if isinstance(result, dict) else []
            intents = [i for i in raw_intents if i in self._valid_intents]

            logger.info("intent_recognition: raw = %s, valid = %s", raw_intents, intents)

            state[self.STATE["intents"]] = intents
            state[self.STATE["current"]] = intents[0] if intents else ""
            state[self.STATE["index"]] = 0
            state[self.STATE["results"]] = {}
            if intents:
                state[self.STATE["clarify_count"]] = 0
            else:
                state[self.STATE["clarify_count"]] = state.get(self.STATE["clarify_count"], 0) + 1
                logger.warning("intent_recognition: no valid intent, clarify_count = %d",
                               state[self.STATE["clarify_count"]])
            return state
        except Exception as e:
            logger.error("intent_recognition failed: %s", e)
            raise Exception(f"Intent recognition error: {e}")

    # ------------------------------------------------------------------
    # 追问 / 结束
    # ------------------------------------------------------------------
    def ask_clarification(self, state: WriterState) -> WriterState:
        options = "\n".join(f"- {k}：{v['description']}" for k, v in (self.SUBGRAPHS or {}).items())
        msg = AIMessage(content=f"我不太确定你想做什么，请告诉我更具体的需求，比如：\n{options}\n- 其他")
        state[self.STATE["messages"]] = [msg]
        state[self.STATE["history"]].append(msg)
        logger.info("ask_clarification: asking user for clarification")
        return state

    def end_conversation(self, state: WriterState) -> WriterState:
        msg = AIMessage(content="抱歉，我无法识别你的意图。请尝试更具体的描述，或者输入 /exit 退出。")
        state[self.STATE["messages"]] = [msg]
        state[self.STATE["history"]].append(msg)
        logger.info("end_conversation: unable to identify intent, ending")
        return state

    # ------------------------------------------------------------------
    # 子图分派
    # ------------------------------------------------------------------
    def route_after_intent(self, state: WriterState) -> str:
        if not state.get(self.STATE["intents"]):
            logger.info("route_after_intent: no intents -> clarify")
            return self.ROUTES["clarify"]
        logger.info("route_after_intent: intents found -> dispatch")
        return self.ROUTES["dispatch"]

    def dispatch_next(self, state: WriterState) -> WriterState:
        intents = state.get(self.STATE["intents"]) or []
        idx = state.get(self.STATE["index"], 0)
        if idx < len(intents):
            state[self.STATE["current"]] = intents[idx]
            state[self.STATE["index"]] = idx + 1
            logger.info("dispatch_next: current = %s, index = %d/%d",
                        intents[idx], idx + 1, len(intents))
        else:
            state[self.STATE["current"]] = ""
            logger.info("dispatch_next: all intents dispatched")
        return state

    def route_dispatch(self, state: WriterState) -> str:
        intent = state.get(self.STATE["current"])
        if not intent:
            logger.info("route_dispatch: no current intent -> collect")
            return self.ROUTES["collect"]
        sub = (self.SUBGRAPHS or {}).get(intent)
        target = sub["node_name"] if sub else self.ROUTES["generic"]
        logger.info("route_dispatch: intent=%s -> target=%s", intent, target)
        return target

    def execute_subgraph(self, state: WriterState) -> WriterState:
        """运行子图并把结果存入 intent_results。"""
        intent = state.get(self.STATE["current"], "")
        sub = (self.SUBGRAPHS or {}).get(intent)

        if not sub or intent not in self._subgraphs:
            results = dict(state.get(self.STATE["results"]) or {})
            results[intent] = f"「{intent}」子图尚未实装"
            state[self.STATE["results"]] = results
            logger.warning("execute_subgraph: no subgraph for intent=%s", intent)
            return state

        # 运行子图
        subgraph = self._subgraphs[intent]
        sub_state = subgraph.invoke(state)

        # 从子图输出中提取最后一条 AI 消息作为结果
        sub_messages = sub_state.get("messages") or []
        result_text = ""
        for msg in reversed(sub_messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                result_text = msg.content if isinstance(msg.content, str) else str(msg.content)
                break

        if not result_text:
            result_text = f"「{intent}」子图未产出有效结果"

        results = dict(state.get(self.STATE["results"]) or {})
        results[intent] = result_text
        state[self.STATE["results"]] = results

        # 把子图产生的消息合并回主图
        state[self.STATE["messages"]] = sub_messages
        state[self.STATE["history"]] = sub_state.get("history") or state.get(self.STATE["history"]) or []

        logger.info("execute_subgraph: intent=%s, result_len=%d", intent, len(result_text))
        return state

    def collect_results(self, state: WriterState) -> WriterState:
        results = state.get(self.STATE["results"], {})
        result_text = "\n".join(f"【{k}】{v}" for k, v in results.items()) if results else "（本轮无子任务产出）"
        state[self.STATE["task"]] = result_text
        state[self.STATE["history"]] = (state.get(self.STATE["history"]) or []) + [
            HumanMessage(content=f"以下是子图/工具产出，请据此并结合用户问题作答：\n{result_text}")
        ]
        logger.info("collect_results: collected %d results", len(results))
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
    s = NOVELIST_SYSTEM_PROMPT
