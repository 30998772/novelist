"""构思子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class BrainstormState(TypedDict, total=False):
    """构思子图状态：纯聊天 + 工具。"""

    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]
    task: str


NODE_NAME = "brainstorm"
TOOL_NAMES = ["story_brainstorm", "write_file", "read_file", "list_files", "create_project"]
