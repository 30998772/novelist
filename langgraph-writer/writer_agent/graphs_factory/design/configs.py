"""设计子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class DesignState(TypedDict, total=False):
    """设计子图状态：大纲设计、角色创建、世界观搭建。"""

    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]
    task: str
    project_dir: str
    outline: str
    brainstorm_draft: str

    # 推理循环字段
    findings: str                    # 全局发现
    call_count: int                  # 当前调用次数
    max_calls: int                   # 最大调用次数
    is_complete: bool                # 任务是否完成
    pending_actions: List[dict]      # 待执行的动作列表
    current_observations: List[str]  # 本轮观测结果


NODE_NAME = "design"
TOOL_NAMES = ["story_outline", "character_design", "worldbuilding", "write_file", "read_file", "list_files"]
PROJECT_DIR = "novels/新书"  # 默认项目目录，可按需修改
