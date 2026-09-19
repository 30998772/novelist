"""设计子图：大纲设计、角色创建、世界观搭建。

子图结构（对齐 docs/subgraph_设计.mmd）:
    check_limit → llm_reason → execute_actions → analyze → check_complete
        → 完成 → conclusion → END
        → 未完成 → check_limit（循环）
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .._shared.chat_node import build_reason_loop
from .configs import NODE_NAME, TOOL_NAMES, DesignState


def build_subgraph_design(
    llm: ChatOpenAI,
    tools: list[BaseTool],
    checkpoint: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    return build_reason_loop(
        name=NODE_NAME,
        tool_names=TOOL_NAMES,
        llm=llm,
        tools=tools,
        state_cls=DesignState,
        max_calls=10,
        checkpoint=checkpoint,
    )
