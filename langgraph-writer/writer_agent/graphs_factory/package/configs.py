"""包装子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class PackageState(TypedDict, total=False):
    """包装子图状态：起书名、写简介、推荐投稿平台。"""

    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]
    task: str
    draft: str               # 待包装稿件


NODE_NAME = "package"
TOOL_NAMES = ["title_blurb", "recommend_platform", "revision_log"]
AFTER_TOOLS_MSG = "包装工具执行完毕，请查看包装结果并继续"
