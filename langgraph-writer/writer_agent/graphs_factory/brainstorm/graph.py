"""构思子图：纯聊天 + 工具。

流程：chatbot ⇄ tools → END
- 聊天讨论构思
- 需要时调用工具（write_file, create_project 等）
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .._shared.chat_node import build_tool_loop
from .configs import NODE_NAME, TOOL_NAMES, BrainstormState


def build_subgraph_brainstorm(
    llm: ChatOpenAI,
    tools: list[BaseTool],
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    return build_tool_loop(
        name=NODE_NAME,
        tool_names=TOOL_NAMES,
        llm=llm,
        tools=tools,
        state_cls=BrainstormState,
        checkpoint=checkpoint,
    )
