"""设计子图：大纲设计、角色创建、世界观搭建。

子图结构（对齐 docs/subgraph_设计.mmd）:
    START → chatbot(LLM+bind_tools) → tools_condition
        ├── 有工具调用 → ToolNode(story_outline, character_design, worldbuilding) → interrupt → chatbot
        └── 无工具调用 → END
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .chat_node import build_tool_loop

NODE_NAME = "design"
TOOL_NAMES = ["story_outline", "character_design", "worldbuilding"]
AFTER_TOOLS_MSG = "设计工具执行完毕，请查看设计结果并继续"


def build_subgraph_design(
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