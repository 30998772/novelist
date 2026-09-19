"""审稿子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ReviewState(TypedDict, total=False):
    """审稿子图状态：排查矛盾、AI痕迹、节奏等全方位检查。"""

    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]
    task: str
    draft: str               # 待审稿件
    review_notes: List[str]  # 审稿意见


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
