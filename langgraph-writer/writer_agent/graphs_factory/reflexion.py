"""自我反思图（对齐 LangGraph-Chatchat graphs_factory/reflexion.ReflexionGraph）。

流程（取自 LangGraph reflexion 教程）：
    history_manager → function_call(检索子图) → draft → function_call_loop
      → revise → (未达轮数回 function_call_loop / 达到则 END)

与 Chatchat 的差异：强行追加的是 writer 的 `search_knowledge`（而非 search_internet），
且反思轮数记录在 state["iteration"] 上，不使用模块级全局变量（避免并发/多次调用串扰）。
"""

import datetime
from typing import Any, List, Literal, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ToolMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from ..state import WriterState
from ..tools_factory import get_tool
from .graphs_registry import Graph, register_graph


class Reflection(BaseModel):
    missing: Optional[str] = Field(None, description="Critique of what is missing.")
    superfluous: Optional[str] = Field(None, description="Critique of what is superfluous")


class AnswerQuestion(BaseModel):
    """Answer the question with reflection and follow-up search queries."""

    answer: Optional[str] = Field(None, description="Your answer to the question.")
    reflection: Optional[Reflection] = Field(
        None, description="Your reflection on the initial answer."
    )
    search_queries: Optional[List[str]] = Field(
        None,
        description="1-3 search queries for researching improvements to address the critique.",
    )


class ReviseAnswer(AnswerQuestion):
    """Revise the answer, citing references and adding search queries."""

    references: Optional[List[str]] = Field(
        None, description="Citations motivating your updated answer."
    )


class ReflexionState(WriterState, total=False):
    """question / answer / reflection / search_queries / references。"""

    question: Optional[BaseMessage]
    answer: Optional[str]
    reflection: Optional[Reflection]
    search_queries: Optional[List[str]]
    references: Optional[List[str]]


def extract_messages(messages):
    result = []
    for message in reversed(messages):
        if isinstance(message, ToolMessage):
            result.append(message)
        elif isinstance(message, AIMessage):
            result.append(message)
            break
    return result[::-1]


@register_graph
class ReflexionGraph(Graph):
    name = "reflexion"
    label = "agent"
    title = "自我反思机器人[Beta]"

    def __init__(self,
                 llm: ChatOpenAI,
                 tools: list[BaseTool],
                 history_len: int,
                 checkpoint: BaseCheckpointSaver,
                 max_iterations: int = 2,
                 **kwargs):
        super().__init__(llm, tools, history_len, checkpoint)
        self.max_iterations = max_iterations
        # 保证 agent 有可检索的工具, 否则反思循环无信息可用
        merged = list(tools)
        if not any(t.name == "search_knowledge" for t in merged):
            merged.append(get_tool("search_knowledge"))
        self.tools = merged
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def function_call(self, state: ReflexionState) -> ReflexionState:
        state["question"] = state["history"][-1]
        if not state.get("search_queries"):
            state["search_queries"] = list(state["history"])

        tool_node_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    你是一个能够识别并调用合适函数来解决各种问题的高级 AI。
                    你可以按需同时调用多个函数，或多次调用同一个函数。

                    当前时间：{time}

                    下面是一组问题。对每个问题，识别合适的函数并调用，按问题顺序返回结果。
                    若找不到合适的函数，返回「未找到合适的函数」。

                    问题：
                    {search_queries}
                    """,
                ),
            ]
        ).partial(time=lambda: datetime.datetime.now().isoformat())

        llm_with_tools = tool_node_template | self.llm_with_tools
        func_call = llm_with_tools.invoke(state)
        state["messages"] = [func_call]
        state["history"].append(func_call)
        return state

    @staticmethod
    def process_func_call_history(state: ReflexionState) -> ReflexionState:
        """把尾部连续的 ToolMessage 手动同步进 history。"""
        index = len(state["messages"]) - 1
        while index >= 0 and isinstance(state["messages"][index], ToolMessage):
            index -= 1
        tool_messages_to_add = state["messages"][index + 1:]
        if tool_messages_to_add:
            state["history"].extend(tool_messages_to_add)
        return state

    @staticmethod
    def process_reflexion_result(state: ReflexionState, result) -> ReflexionState:
        if getattr(result, "reflection", None) is not None and not isinstance(
            result.reflection, dict
        ):
            result.reflection = result.reflection.dict()

        if getattr(result, "search_queries", None) is not None and not isinstance(
            result.search_queries, list
        ):
            result.search_queries = list(result.search_queries)

        state["messages"].append(AIMessage(content=str(result)))
        state["history"].append(AIMessage(content=str(result)))
        state["answer"] = result.answer
        state["reflection"] = result.reflection
        state["search_queries"] = result.search_queries
        if hasattr(result, "references"):
            state["references"] = result.references
        return state

    def initial(self, state: ReflexionState) -> ReflexionState:
        initial_prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """你是一位资深小说创作专家。
                    当前时间：{time}
                    用户问题：{question}

                    目前已完成的操作与结果：
                    {history}

                    步骤：
                    1. 给出正确、简洁的回答。
                    2. 基于用户问题、已完成的操作与结果，对初稿进行反思与批判，尽量充分。
                       - missing 字段：指出初稿缺失的重要信息或视角。
                       - superfluous 字段：指出初稿中多余或无关的信息。
                    3. 列出还需要收集的额外信息（只列需求，不执行）。
                    4. 用 {function_name} 结构给出更新后的回答，包含：
                       - 更新后的答案
                       - 更新后的反思（填写 missing / superfluous）
                       - 检索词（search_queries）
                       - 参考文献（references）
                    """,
                ),
            ]
        ).partial(time=lambda: datetime.datetime.now().isoformat())

        initial_answer_chain = initial_prompt_template.partial(
            function_name=AnswerQuestion.__name__
        ) | self.llm.with_structured_output(AnswerQuestion)

        initial_result = initial_answer_chain.invoke(state)

        if getattr(initial_result, "reflection", None) is not None and not isinstance(
            initial_result.reflection, dict
        ):
            initial_result.reflection = initial_result.reflection.dict()

        return self.process_reflexion_result(state, initial_result)

    def revision(self, state: ReflexionState) -> ReflexionState:
        if not state.get("iteration"):
            state["references"] = []

        revision_prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """你是一位资深小说创作专家。
                    当前时间：{time}
                    用户问题：{question}

                    目前已完成的操作与结果：
                    {history}

                    初稿：
                    {answer}

                    对初稿的反思：
                    {reflection}

                    步骤：
                    1. 结合新信息修订此前的回答：
                       - 依据批判补全重要信息。
                       - 在修订稿中加入数字标注的引用以便核验。
                       - 若使用了外部来源或函数，在答案末尾加「References」小节，每行一个来源链接；
                         若未使用，则附一个空的 References 列表。
                       - 依据批判删除多余信息。
                       - 保证修订稿清晰、简洁、结构良好。
                    2. 基于用户问题、已完成的操作与结果、反思，再次反思与批判，尽量充分。
                       - missing 字段：确保补全所有关键信息与视角。
                       - superfluous 字段：确保删除所有多余或无关信息。
                    3. 列出还需要收集的额外信息（只列需求，不执行）。
                    4. 用 {function_name} 结构给出更新后的回答。

                    当前参考文献：
                    {references}
                    """,
                ),
            ]
        ).partial(time=lambda: datetime.datetime.now().isoformat())

        revision_chain = revision_prompt_template.partial(
            function_name=ReviseAnswer.__name__
        ) | self.llm.with_structured_output(ReviseAnswer)

        revised_result = revision_chain.invoke(state)
        state["iteration"] = (state.get("iteration") or 0) + 1

        if getattr(revised_result, "reflection", None) is not None and not isinstance(
            revised_result.reflection, dict
        ):
            revised_result.reflection = revised_result.reflection.dict()

        return self.process_reflexion_result(state, revised_result)

    def event_loop(self, state: ReflexionState) -> Literal["function_call_loop", "__end__"]:
        if (state.get("iteration") or 0) >= self.max_iterations:
            return END
        return "function_call_loop"

    def get_graph(self) -> CompiledGraph:
        if not isinstance(self.llm, ChatOpenAI):
            raise TypeError("llm must be an instance of ChatOpenAI")
        if not all(isinstance(tool, BaseTool) for tool in self.tools):
            raise TypeError("All items in tools must be instances of BaseTool")

        tool_node = ToolNode(tools=self.tools)

        function_call_sub_graph_builder = StateGraph(ReflexionState)
        function_call_sub_graph_builder.add_node("function_call", self.function_call)
        function_call_sub_graph_builder.add_node("tools", tool_node)
        function_call_sub_graph_builder.add_node(
            "process_func_call_history", self.process_func_call_history
        )
        function_call_sub_graph_builder.set_entry_point("function_call")
        function_call_sub_graph_builder.add_edge("function_call", "tools")
        function_call_sub_graph_builder.add_edge("tools", "process_func_call_history")
        function_call_sub_graph_builder.add_edge("process_func_call_history", END)
        function_call_sub_graph = function_call_sub_graph_builder.compile(
            checkpointer=self.checkpoint
        )

        builder = StateGraph(ReflexionState)
        builder.add_node("history_manager", self.history_manager)
        builder.add_node("draft_answer", self.initial)
        builder.add_node("revise", self.revision)
        builder.add_node("function_call", function_call_sub_graph)
        builder.add_node("function_call_loop", function_call_sub_graph)

        builder.set_entry_point("history_manager")
        builder.add_edge("history_manager", "function_call")
        builder.add_edge("function_call", "draft_answer")
        builder.add_edge("draft_answer", "function_call_loop")
        builder.add_edge("function_call_loop", "revise")
        builder.add_conditional_edges("revise", self.event_loop)

        return builder.compile(checkpointer=self.checkpoint)

    @staticmethod
    def handle_event(node: str, event: ReflexionState) -> Any:
        if node == "revise":
            return ReviseAnswer(
                answer=event.get("answer"),
                reflection=event.get("reflection"),
                search_queries=event.get("search_queries"),
                references=event.get("references"),
            )
        elif node == "draft_answer":
            return AnswerQuestion(
                answer=event.get("answer"),
                reflection=event.get("reflection"),
                search_queries=event.get("search_queries"),
            )
        elif node in ("function_call", "function_call_loop"):
            return extract_messages(event["messages"])
        return None
