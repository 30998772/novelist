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

from ..state import WriterState
from .graphs_registry import Graph, register_graph

# 意图识别最大尝试次数
MAX_CLARIFICATION_ATTEMPTS = 3


class BaseAgentGraph(Graph):
    name = ""
    label = "agent"
    title = ""
    system_prompt = ""
    tool_names: list[str] = ["*"]  # "*" 表示全部工具

    def __init__(self,
                 llm: ChatOpenAI,
                 tools: list[BaseTool],
                 history_len: int,
                 checkpoint: BaseCheckpointSaver,
                 system_prompt: str | None = None):
        super().__init__(llm, tools, history_len, checkpoint)
        
        # 意图识别 prompt
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个意图识别助手。根据用户输入，识别用户的意图并输出意图列表。

可选意图：
- 构思：找灵感、定题材、讨论核心冲突
- 设计：大纲设计、角色创建、世界观搭建
- 创作：写新章、续写正文、补充素材
- 审稿：排查矛盾、检查AI痕迹、审节奏/钩子/对话/画面等
- 修改：修改润色、定制文风、丰满度补强
- 评估：六维评分、特殊风格参考
- 包装：起书名/写简介、推荐投稿平台

输出格式：JSON数组，如 ["构思", "创作"]
如果用户输入不明确，输出空数组 []"""),
            ("placeholder", "{history}"),
        ])
        self.llm_with_intent = self.intent_prompt | self.llm
        
        # 主对话 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt or self.system_prompt),
            ("placeholder", "{history}"),
        ])
        self.llm_with_tools = prompt | self.llm.bind_tools(self.tools)

        # 子图（构思阶段），供主图 intent_route 分派
        self.brainstorm_subgraph = self.build_brainstorm_subgraph()

    def history_manager(self, state: WriterState) -> WriterState:
        """裁剪历史，过滤Tool消息，只保留最近history_len条。"""
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

    def intent_recognition(self, state: WriterState) -> WriterState:
        """LLM识别用户意图，输出意图列表。"""
        try:
            response = self.llm_with_intent.invoke(state)
            # 解析意图列表
            content = response.content
            # 尝试解析JSON
            import json
            try:
                intents = json.loads(content)
            except json.JSONDecodeError:
                # 如果解析失败，尝试从文本中提取
                intents = []
                for intent in ["构思", "设计", "创作", "审稿", "修改", "评估", "包装"]:
                    if intent in content:
                        intents.append(intent)
            
            state["intent_list"] = intents
            state["current_intent"] = intents[0] if intents else ""
            state["intent_results"] = {}
            state["clarification_attempts"] = state.get("clarification_attempts", 0) + 1
            return state
        except Exception as e:
            raise Exception(f"Intent recognition error: {e}")

    def check_intent(self, state: WriterState) -> Literal["ask_clarification", "loop"]:
        """检查意图列表是否为空。"""
        if not state.get("intent_list"):
            return "ask_clarification"
        return "loop"

    def check_clarification_limit(self, state: WriterState) -> Literal["ask_clarification", "end"]:
        """检查是否超过最大尝试次数。"""
        if state.get("clarification_attempts", 0) >= MAX_CLARIFICATION_ATTEMPTS:
            return "end"
        return "ask_clarification"

    def ask_clarification(self, state: WriterState) -> WriterState:
        """询问用户补充信息。"""
        msg = AIMessage(content="我不太确定你想做什么，请告诉我更具体的需求，比如：\n- 开新书/找灵感\n- 设计大纲/角色\n- 写新章/续写\n- 检查矛盾/AI痕迹\n- 修改润色\n- 其他")
        state["messages"] = [msg]
        state["history"].append(msg)
        return state

    def end_conversation(self, state: WriterState) -> WriterState:
        """告知用户无法识别意图。"""
        msg = AIMessage(content="抱歉，我无法识别你的意图。请尝试更具体的描述，或者输入 /exit 退出。")
        state["messages"] = [msg]
        state["history"].append(msg)
        return state

    # ------------------------------------------------------------------
    # 子图分派
    # ------------------------------------------------------------------
    def route_after_intent(self, state: WriterState) -> str:
        """意图为空 -> 追问；否则按当前意图分派到对应子图节点。"""
        if not state.get("intent_list"):
            return "ask_clarification"
        return "subgraph_brainstorm" if state.get("current_intent") == "构思" else "subgraph_generic"

    def execute_subgraph(self, state: WriterState) -> WriterState:
        """通用子图占位（设计/创作/审稿/修改/评估/包装 尚未实装为独立子图）。"""
        intent = state.get("current_intent", "")
        results = dict(state.get("intent_results") or {})
        results[intent] = f"「{intent}」子图尚未实装（占位）。本轮识别意图：{state.get('intent_list')}"
        state["intent_results"] = results
        return state

    def collect_results(self, state: WriterState) -> WriterState:
        """汇总子图产出为 task，并把成果注入 history，供 chatbot 使用。"""
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
    # 构思阶段子图
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

    def build_brainstorm_subgraph(self) -> CompiledStateGraph:
        """构思子图：story_brainstorm 工具发散 -> LLM 收敛为推荐方案。"""

        def bg_generate(state: WriterState) -> WriterState:
            idea = self._last_human_text(state)
            tool = self._get_tool("story_brainstorm")
            try:
                draft = str(tool.invoke({"idea": idea, "genre": ""}))
            except Exception as e:  # noqa: BLE001
                draft = f"（头脑风暴执行失败：{e}）"
            state["brainstorm_draft"] = draft
            return state

        def bg_polish(state: WriterState) -> WriterState:
            idea = self._last_human_text(state)
            draft = state.get("brainstorm_draft", "")
            resp = self.llm.invoke([
                ("system", "你是资深小说策划。请把下面的头脑风暴草案收敛为一个明确的推荐方向，"
                           "并给出「一句话高概念 logline + 类型定位 + 核心冲突」。中文，简洁。"),
                ("user", f"用户原始需求：{idea}\n\n头脑风暴草案：\n{draft}"),
            ])
            core = str(resp.content).strip()
            results = dict(state.get("intent_results") or {})
            results["构思"] = f"【发散方案】\n{draft}\n\n【收敛推荐】\n{core}"
            state["core_concept"] = core
            state["intent_results"] = results
            return state

        bg = StateGraph(WriterState)
        bg.add_node("bg_generate", bg_generate)
        bg.add_node("bg_polish", bg_polish)
        bg.add_edge(START, "bg_generate")
        bg.add_edge("bg_generate", "bg_polish")
        bg.add_edge("bg_polish", END)
        return bg.compile()

    # ------------------------------------------------------------------
    # chatbot
    # ------------------------------------------------------------------
    def chatbot(self, state: WriterState) -> WriterState:
        """LLM整合结果，回答用户。"""
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
        builder.add_node("subgraph_brainstorm", self.brainstorm_subgraph)
        builder.add_node("subgraph_generic", self.execute_subgraph)
        builder.add_node("collect_results", self.collect_results)
        builder.add_node("chatbot", self.chatbot)
        builder.add_node("tools", ToolNode(tools=self.tools))

        builder.set_entry_point("history_manager")
        builder.add_edge("history_manager", "intent_recognition")
        builder.add_conditional_edges(
            "intent_recognition",
            self.route_after_intent,
            {
                "ask_clarification": "ask_clarification",
                "subgraph_brainstorm": "subgraph_brainstorm",
                "subgraph_generic": "subgraph_generic",
            },
        )
        builder.add_edge("ask_clarification", END)
        builder.add_edge("subgraph_brainstorm", "collect_results")
        builder.add_edge("subgraph_generic", "collect_results")
        builder.add_edge("collect_results", "chatbot")
        builder.add_conditional_edges("chatbot", tools_condition)
        builder.add_edge("tools", "chatbot")

        if self.checkpoint is not None:
            return builder.compile(checkpointer=self.checkpoint)
        return builder.compile()

    @staticmethod
    def handle_event(node: str, event: WriterState) -> BaseMessage:
        return event["messages"][-1]


ToolCallingAgentGraph = BaseAgentGraph


@register_graph
class NovelistGraph(BaseAgentGraph):
    """小说家主图：全能调度 + 写作工具集，构思阶段走子图。"""

    name = "novelist"
    label = "agent"
    title = "小说家"
    tool_names = ["*"]
    system_prompt = (
        "你是「小说家」主 agent，负责统筹构思/设计/创作/审稿/修改/评估/包装等写作环节。"
        "你可以直接调用写作工具产出正文、大纲、设定、检查等内容。"
        "始终用中文回复，紧扣用户的写作需求，输出可直接使用的成品，不要空谈方法论。"
    )
