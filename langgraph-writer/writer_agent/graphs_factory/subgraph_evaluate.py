"""评估子图：六维评分、故事核心诊断、ACGN风格参考。

子图结构（对齐 docs/subgraph_评估.mmd）:
    START → chatbot(LLM+bind_tools) → tools_condition
        ├── 有工具调用 → ToolNode(story_core_master, dragon_ride_007, urobuchi_gen, anime_lightnovel_styles) → interrupt → chatbot
        └── 无工具调用 → END
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .chat_node import build_tool_loop

NODE_NAME = "evaluate"
TOOL_NAMES = ["story_core_master", "dragon_ride_007", "urobuchi_gen", "anime_lightnovel_styles"]
AFTER_TOOLS_MSG = "评估工具执行完毕，请查看评估结果并继续"


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
        after_tools_message=AFTER_TOOLS_MSG,
        checkpoint=checkpoint,
    )