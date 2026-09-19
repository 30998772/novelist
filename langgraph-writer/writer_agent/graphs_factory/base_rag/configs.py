"""BaseRagGraph 图配置。

集中管理 RAG 图的工具列表和状态定义，graph.py 按需导入。
"""

from typing import Annotated, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# ════════════════════════════════════════════════════════════════
# BaseRagGraph 专用 State
# ════════════════════════════════════════════════════════════════

class RagState(TypedDict, total=False):
    """RAG 图状态：在基础消息字段上补充检索相关字段。"""

    # 消息队列（LangGraph add_messages 自动合并）
    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]

    # 任务
    task: str

    # RAG 检索参数
    knowledge_base: str
    top_k: int
    score_threshold: float
    question: str
    docs: List[Dict]
    retrieve_retry: int


# ════════════════════════════════════════════════════════════════
# 工具配置
# ════════════════════════════════════════════════════════════════

TOOL_NAMES = [
    "search_knowledge",
    "search_manuscript",
    "read_file",
    "search_files",
    "list_files",
]

MAX_RETRIEVE_RETRY = 1
DEFAULT_TOP_K = 5
DEFAULT_SCORE_THRESHOLD = 0.0
