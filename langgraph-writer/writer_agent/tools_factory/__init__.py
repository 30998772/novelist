"""tools_factory：由 `.opencode/skills/*/SKILL.md` 转换来的 LangGraph 工具集合。

每个 skill → 一个 tool（工具内部调用 LLM 按技能规则产出结果），
外加 4 个基础文件工具。导入本模块会触发全部工具注册到 `_TOOLS_REGISTRY`。

对齐 LangGraph-Chatchat 的 tools_factory 结构：注册中心在 tools_registry.py。
"""

from . import _files  # noqa: F401
from . import file_tools  # noqa: F401  注册文件工具
from . import story_brainstorm  # noqa: F401
from . import story_outline  # noqa: F401
from . import character_design  # noqa: F401
from . import worldbuilding  # noqa: F401
from . import story_core_master  # noqa: F401  含故事丰满度与AI协作(story-depth-ai)
from . import writing_style  # noqa: F401
from . import narrative_viewpoint  # noqa: F401
from . import dialogue_craft  # noqa: F401
from . import scene_description  # noqa: F401
from . import pacing_control  # noqa: F401
from . import hook_opening  # noqa: F401
from . import dragon_ride_007  # noqa: F401
from . import urobuchi_gen  # noqa: F401
from . import anime_lightnovel_styles  # noqa: F401
from . import emotion_scene  # noqa: F401
from . import action_scene  # noqa: F401
from . import suspense_twist  # noqa: F401
from . import chapter_drafting  # noqa: F401
from . import revision  # noqa: F401
from . import continuity_check  # noqa: F401
from . import ai_trace_check  # noqa: F401
from . import revision_log  # noqa: F401
from . import recommend_platform  # noqa: F401
from . import add_setting  # noqa: F401
from . import title_blurb  # noqa: F401
from . import knowledge_search  # noqa: F401  RAG 检索工具

from .tools_registry import (  # noqa: E402
    BaseToolOutput,
    all_tool_names,
    get_tool,
    list_tools,
    regist_tool,
)

__all__ = [
    "regist_tool",
    "BaseToolOutput",
    "get_tool",
    "list_tools",
    "all_tool_names",
]