"""writer_agent: 小说创作 LangGraph Agent 包。

架构对齐 LangGraph-Chatchat:
- `graphs_factory/`: 6 个 opencode agent 转换来的图和注册中心, 外加区间式创作流水线;
- `tools_factory/`: 27 个 skill 转换来的工具和注册中心, 外加文件工具;
- `app.py`: 装配入口 (build_tools / create_graph / run_agent);
- 保留 state / registry / nodes / graph_builder 以兼容区间式工作流与旧 CLI。
"""

from .state import (
    STAGE_LABELS,
    STAGE_ORDER,
    WriterState,
    interval_stages,
    normalize_stage,
    validate_interval,
)
from .registry import all_stages, get_stage, register_stage, registered_names
from .graph_builder import WriterGraph, build_agent, run_interval
from .llm import get_llm
from . import nodes  # noqa: F401  注册全部阶段节点
from . import tools_factory  # noqa: F401  注册全部 skill 工具
from . import graphs_factory  # noqa: F401  注册全部 agent 图
from . import app  # noqa: F401

# 便捷导出
from .graphs_factory import (
    BaseAgentGraph,
    BaseRagGraph,
    Graph,
    PlanExecuteGraph,
    ReflexionGraph,
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
    # 状态/阶段
    "STAGE_LABELS",
    "STAGE_ORDER",
    "WriterState",
    "interval_stages",
    "normalize_stage",
    "validate_interval",
    # 阶段节点注册
    "all_stages",
    "get_stage",
    "register_stage",
    "registered_names",
    # 区间工作流
    "WriterGraph",
    "build_agent",
    "run_interval",
    "nodes",
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
    "PlanExecuteGraph",
    "ReflexionGraph",
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
]

__version__ = "0.2.0"