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

    # 计划 / 意图识别
    plan: List[dict]
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
    "generic": "subgraph_generic",
    "confirm": "confirm_step",
    "collect": "collect_results",
    "summarize": "summarize_results",
}

ENTRY = "history"

EDGES = [
    ["history", "intent"],
    ["clarify", END],
    ["generic", "confirm"],
    ["collect", "summarize"],
    ["summarize", END],
]

ROUTES = {
    "clarify": "ask_clarification",
    "collect": "collect_results",
    "generic": "subgraph_generic",
    "confirm": "confirm_step",
}

CONDITIONAL_EDGES = {
    "intent": {
        "router": "route_after_intent",
        "map": {ROUTES["clarify"]: "clarify", ROUTES["generic"]: "generic"},
    },
}

# ════════════════════════════════════════════════════════════════
# State 字段映射
# ════════════════════════════════════════════════════════════════

STATE = {
    "messages": "messages",
    "history": "history",
    "plan": "plan",
    "intents": "intent_list",
    "current": "current_intent",
    "index": "intent_index",
    "results": "intent_results",
    "clarify_count": "clarification_attempts",
    "task": "task",
    "pending_confirm": "pending_confirm",
    "feedback": "step_feedback",
    "attempts": "step_attempts",
    "retry_current": "retry_current",
}

# ════════════════════════════════════════════════════════════════
# 子图注册表（引用扁平的 subgraph_*.py）
# ════════════════════════════════════════════════════════════════

SUBGRAPHS = {
    "构思": {
        "node_name": "subgraph_brainstorm",
        "tools": ["story_brainstorm", "write_file", "read_file", "list_files"],
        "description": "找灵感、定题材、开新书、讨论核心冲突，可写入文件",
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

# ════════════════════════════════════════════════════════════════
# 子图逐步确认（human-in-the-loop）
# ════════════════════════════════════════════════════════════════

# 同一步最多允许用户要求重做几次，超过则强制跳过，避免无限重跑
MAX_STEP_RETRY = 2

# 用户回复归一化：命中即为采纳本步结果
APPROVE_WORDS = {
    "", "approve", "ok", "okay", "y", "yes", "good", "fine",
    "通过", "确认", "采纳", "同意", "可以", "继续", "下一步", "没问题", "对", "是",
}

# 命中即为丢弃本步结果并重跑（不带具体意见）
RETRY_WORDS = {"retry", "redo", "again", "重做", "重跑", "再来", "再来一次", "不行", "不满意"}

# 命中即为丢弃本步结果并进入下一步
SKIP_WORDS = {"skip", "next", "跳过", "略过", "下一个", "不管了"}
