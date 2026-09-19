"""BaseRagGraph 图配置。

集中管理 RAG 图的工具列表等配置，graph.py 按需导入。
"""

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
