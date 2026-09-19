"""基础 RAG 图（对齐 LangGraph-Chatchat graphs_factory/base_rag.BaseRagGraph）。

Agentic RAG 流程（取自 LangGraph agentic-rag 教程）：
    history_manager → chatbot(决定是否检索) → (tools_condition) → retrieve
      → init_docs → grade_documents → generate / rewrite → chatbot …

与 Chatchat 的差异：把 `search_local_knowledgebase` 换成 writer 项目的
`search_knowledge`（写作知识库）与 `search_manuscript`（各书设定/正文）两个 RAG 工具。
"""

from typing import Dict, List, Literal

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
    filter_messages,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

from ...state import WriterState
from ...tools_factory import get_tool
from .._shared.registry import Graph, register_graph
from .configs import TOOL_NAMES as CFG_TOOL_NAMES
from .prompts import (
    RAG_CHATBOT_PROMPT,
    RAG_GRADE_PROMPT,
    RAG_GENERATE_PROMPT,
    RAG_REWRITE_PROMPT,
)


class RagState(WriterState, total=False):
    """RAG 图状态：在 WriterState 基础上补充检索相关字段。"""

    knowledge_base: str
    top_k: int
    score_threshold: float
    question: str
    docs: List[Dict]
    retrieve_retry: int


@register_graph
class BaseRagGraph(Graph):
    name = "base_rag"
    label = "rag"
    title = "基础RAG"
    tool_names = CFG_TOOL_NAMES

    def __init__(self,
                 llm: ChatOpenAI,
                 tools: list[BaseTool],
                 history_len: int,
                 checkpoint: BaseCheckpointSaver,
                 knowledge_base: str = "",
                 top_k: int = 5,
                 score_threshold: float = 0.0,
                 max_retrieve_retry: int = 1):
        super().__init__(llm, tools, history_len, checkpoint)
        self.tools = self._with_rag_tools(tools)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.knowledge_base = knowledge_base
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.max_retrieve_retry = max_retrieve_retry

    @staticmethod
    def _with_rag_tools(tools: list[BaseTool]) -> list[BaseTool]:
        """确保 RAG 检索工具一定在工具清单里（否则图无从检索）。"""
        merged = list(tools)
        existing = {t.name for t in merged}
        for name in ("search_knowledge", "search_manuscript"):
            if name not in existing:
                merged.append(get_tool(name))
        return merged

    def history_manager(self, state: RagState) -> RagState:
        """裁剪历史上下文，并初始化 RAG 检索参数。"""
        try:
            filtered_messages = []
            for message in filter_messages(state["messages"], exclude_types=[ToolMessage]):
                if isinstance(message, AIMessage) and message.tool_calls:
                    continue
                filtered_messages.append(message)
            state["history"] = filtered_messages[-self.history_len:]
            state["question"] = state["history"][-1].content
            state["knowledge_base"] = self.knowledge_base
            state["top_k"] = self.top_k
            state["score_threshold"] = self.score_threshold
            state["docs"] = []
            state["retrieve_retry"] = 0
            return state
        except Exception as e:  # noqa: BLE001
            raise Exception(f"Filtering messages error: {e}")

    def chatbot(self, state: RagState) -> RagState:
        """让 LLM 决定是否调用 RAG 检索工具回答问题。"""
        # ToolNode 只把结果追加到 messages, 需手动同步进 history, 否则会报
        # "messages with role 'tool' must be a response to a preceeding message with 'tool_calls'"
        if isinstance(state["messages"][-1], ToolMessage):
            state["history"].append(state["messages"][-1])

        prompt = PromptTemplate(
            template=RAG_CHATBOT_PROMPT,
            input_variables=["history", "knowledge_base", "top_k", "score_threshold"],
        )

        llm_with_tools = prompt | self.llm_with_tools
        message = llm_with_tools.invoke(state)
        state["messages"] = [message]
        state["history"].append(message)
        return state

    def grade_documents(self, state: RagState) -> Literal["generate", "rewrite"]:
        """判断召回文档是否与问题相关，决定生成还是改写问题重查。"""

        class Grade(BaseModel):
            """Binary score for relevance check."""
            binary_score: str = Field(description="Relevance score 'yes' or 'no'")

        prompt = PromptTemplate(
            template=RAG_GRADE_PROMPT,
            input_variables=["docs", "history"],
        )

        referee = prompt | self.llm.with_structured_output(Grade)
        scored_result = referee.invoke(state)
        if scored_result is None:
            score = "yes"
        else:
            score = getattr(scored_result, "binary_score", None)

        return "generate" if score == "yes" else "rewrite"

    def generate(self, state: RagState) -> RagState:
        """基于召回文档生成答案。"""
        prompt = PromptTemplate(
            template=RAG_GENERATE_PROMPT,
            input_variables=["context", "question"],
        )

        rag_chain = prompt | self.llm | StrOutputParser()
        response = rag_chain.invoke(state)
        state["messages"].append(AIMessage(content=response))
        return state

    def rewrite(self, state: RagState) -> RagState:
        """改写问题以获得更好的检索结果。"""
        prompt = PromptTemplate(
            template=RAG_REWRITE_PROMPT,
            input_variables=["question", "history"],
        )

        llm = prompt | self.llm
        response = llm.invoke(state)
        message = HumanMessage(content=response.content)

        state["messages"] = [message]
        state["history"].append(message)
        state["question"] = response.content
        return state

    def get_graph(self) -> CompiledStateGraph:
        if not isinstance(self.llm, ChatOpenAI):
            raise TypeError("llm must be an instance of ChatOpenAI")
        if not all(isinstance(tool, BaseTool) for tool in self.tools):
            raise TypeError("All items in tools must be instances of BaseTool")

        graph_builder = StateGraph(RagState)
        retrieve = ToolNode(tools=self.tools)

        graph_builder.add_node("history_manager", self.history_manager)
        graph_builder.add_node("chatbot", self.chatbot)
        graph_builder.add_node("retrieve", retrieve)
        graph_builder.add_node("init_docs", self.init_docs)
        graph_builder.add_node("rewrite", self.rewrite)
        graph_builder.add_node("generate", self.generate)

        graph_builder.add_edge(START, "history_manager")
        graph_builder.add_edge("history_manager", "chatbot")
        graph_builder.add_conditional_edges(
            "chatbot",
            tools_condition,
            {"tools": "retrieve", END: END},
        )
        graph_builder.add_edge("retrieve", "init_docs")
        graph_builder.add_conditional_edges("init_docs", self.grade_documents)
        graph_builder.add_edge("rewrite", "chatbot")
        graph_builder.add_edge("generate", END)

        return graph_builder.compile(checkpointer=self.checkpoint)

    @staticmethod
    def handle_event(node: str, event: RagState) -> BaseMessage:
        return event["messages"][-1]
