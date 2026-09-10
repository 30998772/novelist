"""状态定义与阶段调度配置。

工作流固定为线性阶段序列，支持从任意阶段开始、任意阶段结束（区间执行）。
阶段名统一使用英文标识，对应关系:
    research -> 调研
    outline  -> 大纲
    draft    -> 写稿
    review   -> 审稿
    revise   -> 修改
    finalize -> 定稿
"""

from typing import Annotated, List, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


# 全流程阶段顺序（索引即顺序）
STAGE_ORDER: List[str] = [
    "research",
    "outline",
    "draft",
    "review",
    "revise",
    "finalize",
]

STAGE_LABELS: dict[str, str] = {
    "research": "调研",
    "outline": "大纲",
    "draft": "写稿",
    "review": "审稿",
    "revise": "修改",
    "finalize": "定稿",
}


class WriterState(TypedDict, total=False):
    """Agent 在节点间传递的状态。

    区间执行时, 若从中间阶段开始, 调用方必须在初始 state 中提供该阶段
    所需的输入字段（例如从 review 开始需要提供 draft）。
    """

    # 消息队列（LangGraph add_messages 自动合并）
    messages: Annotated[List[BaseMessage], add_messages]

    # ---- 任务描述 ----
    task: str                       # 用户下达的任务描述
    input_data: dict                # 原始素材/用户附带信息

    # ---- 调研阶段产物 ----
    research_notes: str             # 调研纪要

    # ---- 大纲阶段产物 ----
    outline: str                    # 章节/篇章大纲

    # ---- 写稿阶段产物 ----
    draft: str                      # 章节草稿

    # ---- 审稿阶段产物 ----
    review_notes: List[str]         # 审稿意见列表

    # ---- 定稿阶段产物 ----
    final_content: str              # 最终输出

    # ---- 迭代控制 ----
    iteration: int                  # 当前迭代次数
    max_iterations: int             # 最大迭代次数


def normalize_stage(stage: str) -> str:
    """将中英文阶段标识统一为英文键。"""
    s = (stage or "").strip().lower()
    if s in STAGE_ORDER:
        return s
    # 允许中文名
    for key, label in STAGE_LABELS.items():
        if s == label:
            return key
    raise ValueError(
        f"未知阶段: {stage!r}。可用阶段: {', '.join(STAGE_ORDER)}"
    )


def validate_interval(start: str, end: str) -> tuple[int, int]:
    """校验阶段区间, 返回 (start_idx, end_idx)。

    要求 start 在顺序上不晚于 end (允许 start == end 单阶段执行)。
    自动接受中英文阶段名。
    """
    s = normalize_stage(start)
    e = normalize_stage(end)

    si = STAGE_ORDER.index(s)
    ei = STAGE_ORDER.index(e)

    if si > ei:
        raise ValueError(
            f"区间非法: start={STAGE_LABELS[s]}({si}) 晚于 end={STAGE_LABELS[e]}({ei})。"
            f"阶段顺序必须为: {' → '.join(STAGE_LABELS[x] for x in STAGE_ORDER)}"
        )
    return si, ei


def interval_stages(start: str, end: str) -> List[str]:
    """返回 [start, end] 区间内的阶段名列表（含两端）。"""
    si, ei = validate_interval(start, end)
    return STAGE_ORDER[si : ei + 1]