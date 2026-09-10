"""writer_agent: 区间式小说创作 LangGraph Agent 包。"""

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
from . import nodes  # noqa: F401  注册全部阶段节点

__all__ = [
    "STAGE_LABELS",
    "STAGE_ORDER",
    "WriterState",
    "interval_stages",
    "normalize_stage",
    "validate_interval",
    "all_stages",
    "get_stage",
    "register_stage",
    "registered_names",
    "WriterGraph",
    "build_agent",
    "run_interval",
    "nodes",
]

__version__ = "0.1.0"