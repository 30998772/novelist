"""通用聊天节点：把「调用 LLM(绑定工具)、维护 messages/history」的逻辑抽出来供各图复用。

同时提供 chatbot ⇄ tools 的交互式子图构建器（工具执行后 interrupt）。
"""

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt

from ..state import WriterState


def make_chat_node(llm_with_tools):
    """生成 chatbot 节点函数：调用 llm_with_tools，并把 ToolMessage 回灌 history。"""

    def chat_node(state: WriterState) -> WriterState:
        messages = state.get("messages") or []
        if messages and isinstance(messages[-1], ToolMessage):
            state["history"] = (state.get("history") or []) + [messages[-1]]
        out = llm_with_tools.invoke(state)
        state["messages"] = [out]
        state["history"] = (state.get("history") or []) + [out]
        return state

    return chat_node


def build_tool_loop(
    name: str,
    tool_names: list[str],
    llm: ChatOpenAI,
    tools: list[BaseTool],
    after_tools_message: str = "工具执行完毕，请查看结果并继续",
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """构建 {name}_chatbot → {name}_tools → {name}_after_tools → 循环 的交互子图。"""
    node_chat = f"{name}_chatbot"
    node_tools = f"{name}_tools"
    node_after = f"{name}_after_tools"

    picked = [t for t in tools if t.name in set(tool_names)]
    chat_node = make_chat_node(llm.bind_tools(picked))
    tool_node = ToolNode(tools=picked)

    def after_tools(state: WriterState) -> WriterState:
        interrupt(after_tools_message)
        return state

    builder = StateGraph(WriterState)
    builder.add_node(node_chat, chat_node)
    builder.add_node(node_tools, tool_node)
    builder.add_node(node_after, after_tools)
    builder.add_conditional_edges(node_chat, tools_condition, {"tools": node_tools, END: END})
    builder.add_edge(node_tools, node_after)
    builder.add_edge(node_after, node_chat)
    builder.set_entry_point(node_chat)

    if checkpoint is not None:
        return builder.compile(checkpointer=checkpoint)
    return builder.compile()