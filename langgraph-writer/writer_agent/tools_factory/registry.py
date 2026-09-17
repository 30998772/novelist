"""兼容别名：`writer_agent.tools_factory.registry` → `tools_registry`。

skill 工具模块统一 `from .registry import regist_tool`, 真实实现见 tools_registry.py。
"""

from .tools_registry import (  # noqa: F401
    BaseToolOutput,
    _TOOLS_REGISTRY,
    all_tool_names,
    get_tool,
    list_tools,
    regist_tool,
)

__all__ = [
    "BaseToolOutput",
    "regist_tool",
    "get_tool",
    "list_tools",
    "all_tool_names",
    "_TOOLS_REGISTRY",
]