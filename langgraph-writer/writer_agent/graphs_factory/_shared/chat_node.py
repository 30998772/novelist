"""通用聊天节点：把「调用 LLM(绑定工具)、维护 messages/history」的逻辑抽出来供各图复用。

同时提供 chatbot ⇄ tools 的交互式子图构建器。
"""

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition


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
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """构建 chatbot ⇄ tools 循环，自动运行到 END。

    流程：chatbot → 有工具调用 → tools → chatbot → ... → 无工具调用 → END
    """
    node_chat = f"{name}_chatbot"
    node_tools = f"{name}_tools"

    picked = [t for t in tools if t.name in set(tool_names)]
    chat_node = make_chat_node(llm.bind_tools(picked))
    tool_node = ToolNode(tools=picked)

    builder = StateGraph(state_cls)
    builder.add_node(node_chat, chat_node)
    builder.add_node(node_tools, tool_node)

    builder.add_conditional_edges(node_chat, tools_condition, {"tools": node_tools, END: END})
    builder.add_edge(node_tools, node_chat)

    builder.set_entry_point(node_chat)

    if checkpoint is not None:
        return builder.compile(checkpointer=checkpoint)
    return builder.compile()
