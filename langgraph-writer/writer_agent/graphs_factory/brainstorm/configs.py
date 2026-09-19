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

    # 推理循环字段
    findings: str                    # 全局发现
    call_count: int                  # 当前调用次数
    max_calls: int                   # 最大调用次数
    is_complete: bool                # 任务是否完成
    pending_actions: List[dict]      # 待执行的动作列表
    current_observations: List[str]  # 本轮观测结果


NODE_NAME = "brainstorm"
TOOL_NAMES = ["story_brainstorm"]
