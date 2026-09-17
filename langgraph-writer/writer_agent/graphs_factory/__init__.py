"""graphs_factory：由 `.opencode/agent/*.md` 转换来的 LangGraph 图集合。

框架层（对齐 LangGraph-Chatchat graphs_factory）：
- graphs_registry（rag_registry / agent_registry / graph_registry）
- base_agent（BaseAgentGraph：history_manager → chatbot → tools）
- base_rag（BaseRagGraph：Agentic RAG，label="rag"）
- plan_and_execute / reflexion（多步 agent 范式）

业务图（label="agent"）：
- novelist（主 agent, 全能调度）
- content_reviser / ai_trace_checker / craft_reviewer / style_curator / chapter_finalizer
- writer_workflow（保留的区间式创作流水线）

导入本模块即注册全部图到 graphs_registry。
"""

from . import graphs_registry  # noqa: F401
from . import base_agent  # noqa: F401
from . import base_rag  # noqa: F401
from . import plan_and_execute  # noqa: F401
from . import reflexion  # noqa: F401
from . import novelist  # noqa: F401
from . import content_reviser  # noqa: F401
from . import ai_trace_checker  # noqa: F401
from . import craft_reviewer  # noqa: F401
from . import style_curator  # noqa: F401
from . import chapter_finalizer  # noqa: F401
from . import writer_workflow  # noqa: F401

from .graphs_registry import (  # noqa: E402
    Graph,
    State,
    agent_registry,
    all_graph_names,
    get_graph_class,
    get_graph_class_by_label_and_title,
    list_graph_titles_by_label,
    rag_registry,
    register_graph,
)
from .base_agent import BaseAgentGraph, ToolCallingAgentGraph  # noqa: E402
from .base_rag import BaseRagGraph, RagState  # noqa: E402
from .plan_and_execute import PlanExecuteGraph  # noqa: E402
from .reflexion import ReflexionGraph  # noqa: E402

__all__ = [
    "Graph",
    "State",
    "register_graph",
    "get_graph_class",
    "all_graph_names",
    "list_graph_titles_by_label",
    "get_graph_class_by_label_and_title",
    "rag_registry",
    "agent_registry",
    "BaseAgentGraph",
    "ToolCallingAgentGraph",
    "BaseRagGraph",
    "RagState",
    "PlanExecuteGraph",
    "ReflexionGraph",
]
