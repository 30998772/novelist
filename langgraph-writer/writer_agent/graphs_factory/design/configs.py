"""设计子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class DesignState(TypedDict, total=False):
    """设计子图状态：大纲设计、角色创建、世界观搭建。"""

    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]
    task: str
    outline: str              # 大纲
    brainstorm_draft: str     # 头脑风暴草案（参考用）


NODE_NAME = "design"
TOOL_NAMES = ["story_outline", "character_design", "worldbuilding"]
AFTER_TOOLS_MSG = "设计工具执行完毕，请查看设计结果并继续"
