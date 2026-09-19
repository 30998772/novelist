"""包装子图：起书名、写简介、推荐投稿平台。

子图结构（对齐 docs/subgraph_包装.mmd）:
    START → chatbot(LLM+bind_tools) → tools_condition
        ├── 有工具调用 → ToolNode(title_blurb, recommend_platform, revision_log) → interrupt → chatbot
        └── 无工具调用 → END
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .._shared.chat_node import build_tool_loop
from .configs import NODE_NAME, TOOL_NAMES, AFTER_TOOLS_MSG, PackageState


def build_subgraph_package(
    llm: ChatOpenAI,
    tools: list[BaseTool],
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    return build_tool_loop(
        name=NODE_NAME,
        tool_names=TOOL_NAMES,
        llm=llm,
        tools=tools,
        state_cls=PackageState,
        checkpoint=checkpoint,
    )
