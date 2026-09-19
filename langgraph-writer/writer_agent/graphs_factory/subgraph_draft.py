"""创作子图：章节正文写作与设定补充。

子图结构（对齐 docs/subgraph_创作.mmd）:
    START → chatbot(LLM+bind_tools) → tools_condition
        ├── 有工具调用 → ToolNode(chapter_drafting, add_setting) → interrupt → chatbot
        └── 无工具调用 → END
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .chat_node import build_tool_loop

NODE_NAME = "draft"
TOOL_NAMES = ["chapter_drafting", "add_setting"]
AFTER_TOOLS_MSG = "创作工具执行完毕，请查看正文结果并继续"


def build_subgraph_draft(
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