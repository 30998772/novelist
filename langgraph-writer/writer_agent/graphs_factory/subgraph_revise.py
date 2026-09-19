"""修改子图：修改润色、文风定制、丰满度补强。

子图结构（对齐 docs/subgraph_修改.mmd）:
    START → chatbot(LLM+bind_tools) → tools_condition
        ├── 有工具调用 → ToolNode(revision, writing_style, story_core_master) → interrupt → chatbot
        └── 无工具调用 → END
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from ._shared.chat_node import build_tool_loop

NODE_NAME = "revise"
TOOL_NAMES = ["revision", "writing_style", "story_core_master"]
AFTER_TOOLS_MSG = "修改工具执行完毕，请查看修改结果并继续"


def build_subgraph_revise(
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