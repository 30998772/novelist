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

from ..state import WriterState
from .chat_node import build_tool_loop, make_chat_node
from .graphs_registry import Graph, register_graph
from .subgraph_brainstorm import build_subgraph_brainstorm
from .subgraph_draft import build_subgraph_draft
from .subgraph_design import build_subgraph_design
from .subgraph_review import build_subgraph_review
from .subgraph_revise import build_subgraph_revise
from .subgraph_evaluate import build_subgraph_evaluate
from .subgraph_package import build_subgraph_package

MAX_CLARIFICATION_ATTEMPTS = 3
FALLBACK_INTENTS: set[str] = set()


class BaseAgentGraph(Graph):
    # ════════════════════════════════════════════════════════════════
    # 图配置（改这里即可增删节点/边/子图）
    # ════════════════════════════════════════════════════════════════

    # 节点：逻辑名 -> 实际节点名
    NODES = {
        "history": "history_manager",
        "intent": "intent_recognition",
        "clarify": "ask_clarification",
        "dispatch": "dispatch_next",
        "generic": "subgraph_generic",
        "collect": "collect_results",
        "chatbot": "chatbot",
        "tools": "tools",
    }
    ENTRY = "history"

    # 普通边：[起点逻辑名, 终点逻辑名]；终点可为 END
    EDGES = [
        ["history", "intent"],
        ["clarify", END],
        ["generic", "dispatch"],
        ["collect", "chatbot"],
        ["tools", "chatbot"],
    ]

    # 路由返回值（要和 CONDITIONAL_EDGES 的 map key、route_* 的返回一致）
    ROUTES = {
        "clarify": "ask_clarification",
        "dispatch": "dispatch_next",
        "collect": "collect_results",
        "generic": "subgraph_generic",
    }

    # 条件边：起点逻辑名 -> {"router": 方法名或 None, "map": {路由值: 终点逻辑名} 或 None}
    CONDITIONAL_EDGES = {
        "intent": {
            "router": "route_after_intent",
            "map": {ROUTES["clarify"]: "clarify", ROUTES["dispatch"]: "dispatch"},
        },
        "chatbot": {"router": None, "map": None},  # None 走 tools_condition
    }

    # State 字段键
    STATE = {
        "messages": "messages",
        "history": "history",
        "intents": "intent_list",
        "current": "current_intent",
        "index": "intent_index",
        "results": "intent_results",
        "clarify_count": "clarification_attempts",
        "task": "task",
    }

    # 意图识别 prompt
    INTENT_PROMPT_TEMPLATE = (
        "你是一个意图识别助手。根据用户输入，识别用户的意图并输出意图列表。\n"
        "\n"
        "可选意图：\n"
        "{intent_options}\n"
        "\n"
        "输出要求：只输出一个JSON数组，不要输出任何其他文字、解释或Markdown代码块。\n"
        "示例：\n"
        "{intent_examples}\n"
        "如果用户输入不明确（如闲聊、问候），输出 []"
    )
    INTENT_PROMPT_EXAMPLES = (
        '用户：我想开新书，帮我找点灵感 -> ["构思"]\n'
        '用户：先写大纲再写第一章 -> ["设计", "创作"]\n'
        '用户：检查一下有没有AI痕迹 -> ["审稿"]'
    )

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

        intent_prompt_text = self.INTENT_PROMPT_TEMPLATE.format(
            intent_options="\n".join(options),
            intent_examples=self.INTENT_PROMPT_EXAMPLES,
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
        from ..tools_factory import get_tool
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
    SUBGRAPHS = {
        "构思": {
            "node_name": "subgraph_brainstorm",
            "tools": ["story_brainstorm"],
            "description": "找灵感、定题材、开新书、讨论核心冲突",
            "build_func": build_subgraph_brainstorm,
        },
        "设计": {
            "node_name": "subgraph_design",
            "tools": ["story_outline", "character_design", "worldbuilding"],
            "description": "大纲设计、角色创建、世界观搭建",
            "build_func": build_subgraph_design,
        },
        "创作": {
            "node_name": "subgraph_draft",
            "tools": ["chapter_drafting", "add_setting"],
            "description": "写新章、续写正文、补充素材",
            "build_func": build_subgraph_draft,
        },
        "审稿": {
            "node_name": "subgraph_review",
            "tools": [
                "continuity_check", "ai_trace_check", "pacing_control",
                "hook_opening", "dialogue_craft", "scene_description",
                "emotion_scene", "action_scene", "suspense_twist", "narrative_viewpoint"
            ],
            "description": "排查矛盾、AI痕迹、节奏、对话、场景、叙事等全方位检查",
            "build_func": build_subgraph_review,
        },
        "修改": {
            "node_name": "subgraph_revise",
            "tools": ["revision", "writing_style", "story_core_master"],
            "description": "修改润色、文风定制、丰满度补强",
            "build_func": build_subgraph_revise,
        },
        "评估": {
            "node_name": "subgraph_evaluate",
            "tools": ["story_core_master", "dragon_ride_007", "urobuchi_gen", "anime_lightnovel_styles"],
            "description": "六维评分、故事核心诊断、ACGN风格参考",
            "build_func": build_subgraph_evaluate,
        },
        "包装": {
            "node_name": "subgraph_package",
            "tools": ["title_blurb", "recommend_platform", "revision_log"],
            "description": "起书名、写简介、推荐投稿平台",
            "build_func": build_subgraph_package,
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