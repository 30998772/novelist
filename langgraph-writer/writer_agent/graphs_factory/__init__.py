"""graphs_factory：LangGraph 图集合与注册中心。

框架层（对齐 LangGraph-Chatchat graphs_factory）：
- _shared（registry + chat_node）
- novelist（BaseAgentGraph 基类 + NovelistGraph 主图：意图识别 → 子图分派 → chatbot ⇄ tools）
- base_rag（BaseRagGraph：Agentic RAG，label="rag"）

导入本模块即注册全部图到 graphs_registry。
"""

from . import _shared  # noqa: F401
from . import novelist  # noqa: F401
from . import base_rag  # noqa: F401


from ._shared.registry import (  # noqa: E402
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
from .novelist.graph import BaseAgentGraph, NovelistGraph, ToolCallingAgentGraph  # noqa: E402
from .base_rag.graph import BaseRagGraph, RagState  # noqa: E402

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
    "NovelistGraph",
    "ToolCallingAgentGraph",
    "BaseRagGraph",
    "RagState",
]
