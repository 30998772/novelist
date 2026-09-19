"""NovelistGraph 图配置。

集中管理 NODES / EDGES / ROUTES / CONDITIONAL_EDGES / STATE / SUBGRAPHS，
graph.py 按需导入。
"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END
from langgraph.graph.message import add_messages

from ..brainstorm import build_subgraph_brainstorm
from ..design import build_subgraph_design
from ..draft import build_subgraph_draft
from ..review import build_subgraph_review
from ..revise import build_subgraph_revise
from ..evaluate import build_subgraph_evaluate
from ..package import build_subgraph_package


# ════════════════════════════════════════════════════════════════
# NovelistGraph 专用 State
# ════════════════════════════════════════════════════════════════

class NovelistState(TypedDict, total=False):
    """小说家主图状态，包含消息、意图识别和任务字段。"""

    # 消息队列（LangGraph add_messages 自动合并）
    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]

    # 意图识别
    intent_list: List[str]
    current_intent: str
    intent_index: int
    intent_results: dict
    clarification_attempts: int

    # 任务
    task: str

# ════════════════════════════════════════════════════════════════
# 图拓扑
# ════════════════════════════════════════════════════════════════

NODES = {
    "history": "history_manager",
    "intent": "intent_recognition",
    "clarify": "ask_clarification",
    "dispatch": "dispatch_next",
    "generic": "subgraph_generic",
    "collect": "collect_results",
    "chatbot": "chatbot",
    "tools": "tools",
}

ENTRY = "history"

EDGES = [
    ["history", "intent"],
    ["clarify", END],
    ["generic", "dispatch"],
    ["collect", "chatbot"],
    ["tools", "chatbot"],
]

ROUTES = {
    "clarify": "ask_clarification",
    "dispatch": "dispatch_next",
    "collect": "collect_results",
    "generic": "subgraph_generic",
}

CONDITIONAL_EDGES = {
    "intent": {
        "router": "route_after_intent",
        "map": {ROUTES["clarify"]: "clarify", ROUTES["dispatch"]: "dispatch"},
    },
    "chatbot": {"router": None, "map": None},
}

# ════════════════════════════════════════════════════════════════
# State 字段映射
# ════════════════════════════════════════════════════════════════

STATE = {
    "messages": "messages",
    "history": "history",
    "intents": "intent_list",
    "current": "current_intent",
    "index": "intent_index",
    "results": "intent_results",
    "clarify_count": "clarification_attempts",
    "task": "task",
}

# ════════════════════════════════════════════════════════════════
# 子图注册表（引用扁平的 subgraph_*.py）
# ════════════════════════════════════════════════════════════════

SUBGRAPHS = {
    "构思": {
        "node_name": "subgraph_brainstorm",
        "tools": ["story_brainstorm"],
        "description": "找灵感、定题材、开新书、讨论核心冲突",
        "build_func": build_subgraph_brainstorm,
    },
    "设计": {
        "node_name": "subgraph_design",
        "tools": ["story_outline", "character_design", "worldbuilding"],
        "description": "大纲设计、角色创建、世界观搭建",
        "build_func": build_subgraph_design,
    },
    "创作": {
        "node_name": "subgraph_draft",
        "tools": ["chapter_drafting", "add_setting"],
        "description": "写新章、续写正文、补充素材",
        "build_func": build_subgraph_draft,
    },
    "审稿": {
        "node_name": "subgraph_review",
        "tools": [
            "continuity_check", "ai_trace_check", "pacing_control",
            "hook_opening", "dialogue_craft", "scene_description",
            "emotion_scene", "action_scene", "suspense_twist", "narrative_viewpoint",
        ],
        "description": "排查矛盾、AI痕迹、节奏、对话、场景、叙事等全方位检查",
        "build_func": build_subgraph_review,
    },
    "修改": {
        "node_name": "subgraph_revise",
        "tools": ["revision", "writing_style", "story_core_master"],
        "description": "修改润色、文风定制、丰满度补强",
        "build_func": build_subgraph_revise,
    },
    "评估": {
        "node_name": "subgraph_evaluate",
        "tools": ["story_core_master", "dragon_ride_007", "urobuchi_gen", "anime_lightnovel_styles"],
        "description": "六维评分、故事核心诊断、ACGN风格参考",
        "build_func": build_subgraph_evaluate,
    },
    "包装": {
        "node_name": "subgraph_package",
        "tools": ["title_blurb", "recommend_platform", "revision_log"],
        "description": "起书名、写简介、推荐投稿平台",
        "build_func": build_subgraph_package,
    },
}

MAX_CLARIFICATION_ATTEMPTS = 3
FALLBACK_INTENTS: set[str] = set()
