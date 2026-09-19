"""审稿子图：排查矛盾、AI痕迹、节奏、对话、场景、叙事等全方位检查。

子图结构（对齐 docs/subgraph_审稿.mmd）:
    START → chatbot(LLM+bind_tools) → tools_condition
        ├── 有工具调用 → ToolNode(continuity_check, ai_trace_check, ...) → interrupt → chatbot
        └── 无工具调用 → END
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .._shared.chat_node import build_tool_loop
from .configs import NODE_NAME, TOOL_NAMES, AFTER_TOOLS_MSG, ReviewState


def build_subgraph_review(
    llm: ChatOpenAI,
    tools: list[BaseTool],
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    return build_tool_loop(
        name=NODE_NAME,
        tool_names=TOOL_NAMES,
        llm=llm,
        tools=tools,
        state_cls=ReviewState,
        checkpoint=checkpoint,
    )
