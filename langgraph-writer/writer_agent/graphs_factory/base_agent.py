"""通用「LLM + 工具」聊天图（对齐 LangGraph-Chatchat base_agent.BaseAgentGraph）。

图结构：history_manager → chatbot(LLM+bind_tools) → (条件) tools → chatbot …

原始 6 个 opencode agent 全部继承本类，只差三样东西：
- `system_prompt`：该 agent 的职责/调度/纪律 prompt（源自 `.opencode/agent/*.md`）;
- `tool_names`：该 agent 可用的工具清单（"*" 表示全部, 即「一站式 / 全能调度」）;
- `name` / `title`：注册键。
"""

from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from ..state import WriterState
from .graphs_registry import Graph


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
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt or self.system_prompt),
                ("placeholder", "{history}"),
            ]
        )
        self.llm_with_tools = prompt | self.llm.bind_tools(self.tools)

    def chatbot(self, state: WriterState) -> WriterState:
        # ToolMessage 需手动追加入 history, 否则报 "messages with role 'tool' must be
        # a response to a proceeding message with 'tool_calls'" 错误
        if isinstance(state["messages"][-1], ToolMessage):
            state["history"].append(state["messages"][-1])

        messages = self.llm_with_tools.invoke(state)
        state["messages"] = [messages]
        # 同一图内未结束前, 每次输出都缓存进 history, 供下一轮调用
        state["history"].append(messages)
        return state

    def get_graph(self) -> CompiledStateGraph:
        if not isinstance(self.llm, ChatOpenAI):
            raise TypeError("llm must be an instance of ChatOpenAI")
        if not all(isinstance(t, BaseTool) for t in self.tools):
            raise TypeError("All items in tools must be instances of BaseTool")

        builder = StateGraph(WriterState)
        tool_node = ToolNode(tools=self.tools)

        builder.add_node("history_manager", self.history_manager)
        builder.add_node("chatbot", self.chatbot)
        builder.add_node("tools", tool_node)

        builder.set_entry_point("history_manager")
        builder.add_edge("history_manager", "chatbot")
        builder.add_conditional_edges("chatbot", tools_condition)
        builder.add_edge("tools", "chatbot")

        return builder.compile(checkpointer=self.checkpoint)

    @staticmethod
    def handle_event(node: str, event: WriterState) -> BaseMessage:
        return event["messages"][-1]


ToolCallingAgentGraph = BaseAgentGraph