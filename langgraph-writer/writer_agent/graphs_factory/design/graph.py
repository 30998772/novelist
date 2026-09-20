"""设计子图：大纲设计、角色创建、世界观搭建。

子图结构（对齐 docs/subgraph_设计.mmd）:
    chatbot ⇄ tools → END
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .._shared.chat_node import build_tool_loop
from .configs import NODE_NAME, TOOL_NAMES, PROJECT_DIR, DesignState

DESIGN_PROMPT = """你是小说设计助手，负责大纲设计、角色创建、世界观搭建。

完成设计后，必须用 write_file 工具把结果写入文件：
- 大纲 → 写入 "设定/大纲.md"
- 角色 → 写入 "设定/角色设定/角色名.md"
- 世界观 → 写入 "设定/世界观设定/核心设定.md"

路径相对于项目目录（书名/）。"""


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
        state_cls=DesignState,
        system_prompt=DESIGN_PROMPT,
        checkpoint=checkpoint,
    )
