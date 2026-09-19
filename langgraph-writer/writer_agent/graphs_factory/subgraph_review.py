"""审稿子图：排查矛盾、AI痕迹、节奏、对话、场景、叙事等全方位检查。

子图结构（对齐 docs/subgraph_审稿.mmd）:
    START → chatbot(LLM+bind_tools) → tools_condition
        ├── 有工具调用 → ToolNode(continuity_check, ai_trace_check, pacing_control, hook_opening, dialogue_craft, scene_description, emotion_scene, action_scene, suspense_twist, narrative_viewpoint) → interrupt → chatbot
        └── 无工具调用 → END
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from .chat_node import build_tool_loop

NODE_NAME = "review"
TOOL_NAMES = [
    "continuity_check",
    "ai_trace_check",
    "pacing_control",
    "hook_opening",
    "dialogue_craft",
    "scene_description",
    "emotion_scene",
    "action_scene",
    "suspense_twist",
    "narrative_viewpoint",
]
AFTER_TOOLS_MSG = "审稿工具执行完毕，请查看审稿结果并继续"


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
        after_tools_message=AFTER_TOOLS_MSG,
        checkpoint=checkpoint,
    )