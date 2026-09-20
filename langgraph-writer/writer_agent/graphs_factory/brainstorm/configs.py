"""构思子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class BrainstormState(TypedDict, total=False):
    """构思子图状态：故事头脑风暴与灵感发散。"""

    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]
    task: str
    project_dir: str

    brainstorm_draft: str
    core_concept: str

    findings: str
    call_count: int
    max_calls: int
    is_complete: bool
    pending_actions: List[dict]
    current_observations: List[str]


NODE_NAME = "brainstorm"
TOOL_NAMES = ["story_brainstorm", "write_file", "read_file", "list_files"]
PROJECT_DIR = "D:\devProject\writer\novelist"
