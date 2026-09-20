"""创作子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# ════════════════════════════════════════════════════════════════
# 创作子图专用 State
# ════════════════════════════════════════════════════════════════

class DraftState(TypedDict, total=False):
    """创作子图状态：章节正文写作与设定补充。"""

    # 消息队列
    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]

    # 任务
    task: str

    # 创作产物
    draft: str                    # 章节草稿
    outline: str                  # 大纲（参考用）


NODE_NAME = "draft"
TOOL_NAMES = ["chapter_drafting", "add_setting", "write_file", "read_file", "list_files"]
AFTER_TOOLS_MSG = "创作工具执行完毕，请查看正文结果并继续"
