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

from .chat_node import build_tool_loop

NODE_NAME = "package"
TOOL_NAMES = ["title_blurb", "recommend_platform", "revision_log"]
AFTER_TOOLS_MSG = "包装工具执行完毕，请查看包装结果并继续"


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
        after_tools_message=AFTER_TOOLS_MSG,
        checkpoint=checkpoint,
    )