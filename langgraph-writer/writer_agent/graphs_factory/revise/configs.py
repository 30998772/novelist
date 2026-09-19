"""修改子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ReviseState(TypedDict, total=False):
    """修改子图状态：修改润色、文风定制、丰满度补强。"""

    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]
    task: str
    draft: str               # 待修改稿件
    review_notes: List[str]  # 审稿意见（参考用）


NODE_NAME = "revise"
TOOL_NAMES = ["revision", "writing_style", "story_core_master"]
AFTER_TOOLS_MSG = "修改工具执行完毕，请查看修改结果并继续"
