"""writer_agent: 小说创作 LangGraph Agent 包。

架构对齐 LangGraph-Chatchat:
- `graphs_factory/`: 6 个 opencode agent 转换来的图和注册中心;
- `tools_factory/`: 27 个 skill 转换来的工具和注册中心, 外加文件工具;
- `app.py`: 装配入口 (build_tools / create_graph / run_agent);
- `service/`: session 管理;
- `state.py`: 状态定义与意图识别字段。
"""

from .state import WriterState
from .llm import get_llm
from . import tools_factory  # noqa: F401  注册全部 skill 工具
from . import graphs_factory  # noqa: F401  注册全部 agent 图
from . import app  # noqa: F401
from .service import Session, SessionManager, get_session_manager

# 便捷导出
from .graphs_factory import (
    BaseAgentGraph,
    BaseRagGraph,
    Graph,
    NovelistGraph,
    State,
    all_graph_names,
    get_graph_class,
    get_graph_class_by_label_and_title,
    list_graph_titles_by_label,
    register_graph,
)
from .tools_factory import (
    BaseToolOutput,
    all_tool_names,
    get_tool,
    list_tools,
    regist_tool,
)
from .app import build_tools, create_graph, run_agent

__all__ = [
    # 状态
    "WriterState",
    # LLM
    "get_llm",
    # 图注册与选择
    "Graph",
    "State",
    "register_graph",
    "get_graph_class",
    "get_graph_class_by_label_and_title",
    "all_graph_names",
    "list_graph_titles_by_label",
    "BaseAgentGraph",
    "BaseRagGraph",
    "NovelistGraph",
    # 工具注册
    "regist_tool",
    "BaseToolOutput",
    "get_tool",
    "list_tools",
    "all_tool_names",
    # 装配
    "build_tools",
    "create_graph",
    "run_agent",
    "app",
    "tools_factory",
    "graphs_factory",
    # Session 管理
    "Session",
    "SessionManager",
    "get_session_manager",
]

__version__ = "0.3.0"
