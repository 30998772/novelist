"""评估子图：六维评分、故事核心诊断、ACGN风格参考。

子图结构（对齐 docs/subgraph_评估.mmd）:
    START → chatbot(LLM+bind_tools) → tools_condition
        ├── 有工具调用 → ToolNode(story_core_master, dragon_ride_007, ...) → interrupt → chatbot
        └── 无工具调用 → END
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .._shared.chat_node import build_tool_loop
from .configs import NODE_NAME, TOOL_NAMES, AFTER_TOOLS_MSG, EvaluateState


def build_subgraph_evaluate(
    llm: ChatOpenAI,
    tools: list[BaseTool],
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    return build_tool_loop(
        name=NODE_NAME,
        tool_names=TOOL_NAMES,
        llm=llm,
        tools=tools,
        state_cls=EvaluateState,
        checkpoint=checkpoint,
    )
