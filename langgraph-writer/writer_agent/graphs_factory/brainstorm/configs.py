"""构思子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# ════════════════════════════════════════════════════════════════
# 构思子图专用 State
# ════════════════════════════════════════════════════════════════

class BrainstormState(TypedDict, total=False):
    """构思子图状态：故事头脑风暴与灵感发散。"""

    # 消息队列
    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]

    # 任务
    task: str

    # 构思产物
    brainstorm_draft: str    # 头脑风暴草案
    core_concept: str        # 一句话高概念


NODE_NAME = "brainstorm"
TOOL_NAMES = ["story_brainstorm"]
AFTER_TOOLS_MSG = "构思工具执行完毕，请查看灵感方案并继续"
