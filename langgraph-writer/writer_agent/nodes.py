"""六个工作流阶段节点的实现。

每个节点只负责一个阶段, 通过 get_llm() 调用 LLM, 返回值仅包含本阶段
需要更新到 state 的字段（LangGraph 只会把这些字段合并进共享状态）。
因此任意节点都既可以作为入口（调用方预置前置字段）, 也可以作为出口。
"""

import json
import os
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from .registry import register_stage
from .state import WriterState

SUPPORTED_DIMENSIONS = [
    "字数与篇幅",
    "人物设定一致性",
    "剧情连贯性/伏笔呼应",
    "AI 写作痕迹（套话、空洞修辞、金句总结）",
    "节奏与爽点密度",
    "章节末尾钩子",
    "番茄内容合规风险提示",
]


def get_llm() -> ChatOpenAI:
    """从环境变量读取配置, 创建 LLM 实例。"""
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("请设置环境变量 LLM_API_KEY")
    return ChatOpenAI(
        model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        temperature=float(os.environ.get("LLM_TEMPERATURE", "0.85")),
    )


def _first_text(state: WriterState, key: str, fallback: str = "") -> str:
    """安全读取 state 字段, 兼容字段缺失（区间跳步场景）。"""
    value = state.get(key)
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    return str(value)


def _chapter_desc(state: WriterState) -> str:
    """从 state 中拼出章节描述片段（用于提示词中的背景信息）。"""
    input_data = state.get("input_data") or {}
    task = _first_text(state, "task")
    parts = []
    if task:
        parts.append(f"任务描述: {task}")
    if input_data:
        parts.append(f"用户素材: {json.dumps(input_data, ensure_ascii=False)}")
    study = _first_text(state, "research_notes")
    if study:
        parts.append(f"调研纪要: {study}")
    outline = _first_text(state, "outline")
    if outline:
        parts.append(f"大纲: {outline}")
    return "\n".join(parts)


def _log(state: WriterState, message: str) -> dict:
    """构造消息回执。"""
    return {"messages": [AIMessage(content=message)]}


@register_stage("research")
def research_node(state: WriterState) -> dict:
    """调研：收集素材、回顾设定, 输出调研纪要。"""
    llm = get_llm()
    input_data = state.get("input_data") or {}
    prompt = f"""你是一位资深小说创作助手, 正在为章节创作做前期调研。

任务描述: {_first_text(state, 'task')}
用户素材: {json.dumps(input_data, ensure_ascii=False)}

请输出调研纪要, 覆盖：
1. 本章核心冲突 / 目标事件
2. 需要呼应的前文伏笔与已埋设定
3. 主要人物在本章应有的状态与动机
4. 场景、环境、道具等需要一致的细节
5. 节奏与情绪走向建议

直接输出纪要正文, 不要输出多余解释。"""

    resp = llm.invoke([HumanMessage(content=prompt)])
    notes = resp.content.strip()
    return {
        **{"research_notes": notes},
        **{"messages": [AIMessage(content=f"调研完成: {notes[:80]}...")]},
    }


@register_stage("outline")
def outline_node(state: WriterState) -> dict:
    """大纲：基于调研纪要产出章节级大纲。"""
    llm = get_llm()
    prompt = f"""你是一位小说剧情架构师, 基于调研纪要产出章节大纲。

{_chapter_desc(state)}

请输出大纲, 覆盖：
1. 章节起承转合结构（开头钩子 → 推进 → 高潮/转折 → 结尾钩子）
2. 具体场景清单（每个场景目的与时长占比）
3. 关键对话与情报传递点
4. 本章结束时的悬念/读者期待

直接输出大纲正文。"""

    resp = llm.invoke([HumanMessage(content=prompt)])
    outline = resp.content.strip()
    return {
        **{"outline": outline},
        **{"messages": [AIMessage(content=f"大纲完成: {outline[:80]}...")]},
    }


@register_stage("draft")
def draft_node(state: WriterState) -> dict:
    """写稿：基于大纲撰写章节正文。

    若因校验失败回跳（state.check_error 非空），在提示词中带上失败原因。
    """
    llm = get_llm()
    iteration = int(state.get("iteration", 0))
    review_notes = state.get("review_notes", [])
    input_data = state.get("input_data") or {}
    check_error = state.get("check_error") or ""

    target_len = input_data.get("target_word_count", 3200)

    if iteration > 0 and review_notes:
        # 修改模式复用 draft 逻辑, 但一般由 revise 节点负责
        prompt = f"""你是小说作家。请根据审稿意见重写以下章节。

原稿:
{_first_text(state, 'draft')}

审稿意见:
{chr(10).join('- ' + n for n in review_notes)}
{f'需修正的硬性检查不通过项:\n{check_error}' if check_error else ''}

产出完整新稿, 目标约 {target_len} 字。"""
    elif check_error:
        # 校验失败回跳写稿
        prompt = f"""你是小说作家。上一版草稿未通过硬性检查，请按提示重写完整章节正文。

硬性检查不通过的原因:
{check_error}

大纲:
{_first_text(state, 'outline')}

要求:
- 只修正检查指出的问题，保留原稿好的部分与剧情骨架
- 目标篇幅约 {target_len} 中文字符
- 直接输出完整重写稿正文, 不要标题与解释"""
    else:
        prompt = f"""你是小说作家。请按以下大纲撰写章节正文。

{_chapter_desc(state)}

要求:
- 目标篇幅约 {target_len} 中文字符
- 流畅现代白话文, 避免翻译腔与 AI 腔
- 对话符合人物身份, 用对白推进剧情
- show, don't tell; 少用"微微/轻轻/缓缓/某种/像一把"等AI高频词
- 段落短、节奏快, 结尾留下钩子
- 直接输出正文, 不要标题与解释"""

    resp = llm.invoke([HumanMessage(content=prompt)])
    draft = resp.content.strip()
    return {
        **{"draft": draft, "iteration": iteration + 1, "check_error": ""},
        **{"messages": [AIMessage(content=f"草稿完成(第{iteration + 1}版), 约 {len(draft)} 字")]},
    }


@register_stage("review")
def review_node(state: WriterState) -> dict:
    """审稿：按多维标准检查草稿, 输出 JSON 意见列表。"""
    llm = get_llm()
    draft = _first_text(state, "draft")
    input_data = state.get("input_data") or {}
    dimensions = input_data.get("review_dimensions") or SUPPORTED_DIMENSIONS
    target_len = input_data.get("target_word_count", 3200)

    prompt = f"""你是严格的审稿编辑, 专门为网络文学平台把关。请检查章节并输出 JSON 数组意见。

章节背景:
{_chapter_desc(state)}

正文(前 300 字): {draft[:300]}...
正文字数: {len(draft)} 字, 目标约 {target_len} 字

检查维度:
{chr(10).join('1. ' + d for d in dimensions)}

输出要求:
- 严格输出 JSON 数组, 每项一条具体可操作的意见(指出问题位置或具体修改方向)
- 无问题则输出 []
- 不要输出任何 JSON 之外的文字"""

    resp = llm.invoke([HumanMessage(content=prompt)])
    notes: list[str] = []
    try:
        parsed = json.loads(resp.content.strip())
        if isinstance(parsed, list):
            notes = [str(n) for n in parsed]
    except (json.JSONDecodeError, ValueError):
        notes = []
    return {
        **{"review_notes": notes},
        **{"messages": [AIMessage(content=f"审稿完成, 发现 {len(notes)} 个问题")]},
    }


@register_stage("revise")
def revise_node(state: WriterState) -> dict:
    """修改：根据审稿意见修订草稿, 输出新稿。"""
    llm = get_llm()
    draft = _first_text(state, "draft")
    review_notes = state.get("review_notes", [])
    input_data = state.get("input_data") or {}
    target_len = input_data.get("target_word_count", 3200)

    prompt = f"""你是小说作家, 现根据审稿意见修改章节。

原稿:
{draft}

审稿意见:
{chr(10).join('- ' + n for n in review_notes) if review_notes else '(无意见, 保持原稿并微调顺滑)'}

要求:
- 保留原有剧情骨架与人物言行基调
- 针对每条意见落实修改, 不能用套话糊弄
- 输出完整改写稿, 目标约 {target_len} 字
- 直接输出正文, 不要评论"""

    resp = llm.invoke([HumanMessage(content=prompt)])
    new_draft = resp.content.strip()
    return {
        **{"draft": new_draft, "iteration": int(state.get("iteration", 0)) + 1},
        **{"messages": [AIMessage(content=f"修改完成, 约 {len(new_draft)} 字")]},
    }


@register_stage("finalize")
def finalize_node(state: WriterState) -> dict:
    """定稿：汇总输出。"""
    draft = _first_text(state, "draft")
    notes = state.get("review_notes", [])
    input_data = state.get("input_data") or {}

    if input_data.get("attach_review_notes"):
        body = (
            draft
            + "\n\n---\n待确认意见:\n"
            + "\n".join(f"- {n}" for n in notes)
            if notes
            else draft
        )
    else:
        body = draft

    return {
        **{"final_content": body},
        **{"messages": [AIMessage(content="定稿完成")]},
    }


# --- 确定性 code 节点（不经 LLM，纯 Python 校验） ---

import re as _re

_CJK_RE = _re.compile(r"[\u4e00-\u9fff]")

# 默认禁用词（AI 高频词/写作铁律）
DEFAULT_BLACKLIST = ["微微", "轻轻", "缓缓", "某种", "仿佛", "似乎", "像是", "像一把"]


def _check_range(target: int, check_input: dict) -> tuple[int, int]:
    """由 target 或显式 min/max 推出字数允许区间。"""
    lo = check_input.get("min_word_count")
    hi = check_input.get("max_word_count")
    if lo is None:
        lo = int(target * 0.9)
    if hi is None:
        hi = int(target * 1.1)
    return lo, hi


@register_stage("check_word_count")
def check_word_count_node(state: WriterState) -> dict:
    """【code 节点】统计草稿中文字符数，校验是否落进目标区间。

    失败时写 check_error 并返回 loop_back_to=draft，由路由函数决定回跳。
    """
    draft = _first_text(state, "draft")
    input_data = state.get("input_data") or {}
    target = int(input_data.get("target_word_count", 3200))
    lo, hi = _check_range(target, input_data)

    count = len(_CJK_RE.findall(draft))
    passed = lo <= count <= hi
    state.update({"cjk_count": count})

    if not passed:
        state["check_error"] = f"字数校验失败: 中文字符 {count} 个，目标区间 [{lo}, {hi}]（target {target}）。请扩写/精简到区间内。"
        msg = AIMessage(content=f"✗ 字数校验: {count}/{target} 字 (区间 {lo}-{hi})，回跳 draft 重写")
    else:
        state["check_error"] = ""
        msg = AIMessage(content=f"✓ 字数校验: {count}/{target} 字 (区间 {lo}-{hi})")
    return {"messages": [msg], "cjk_count": count, "check_error": state["check_error"]}


@register_stage("check_blacklist")
def check_blacklist_node(state: WriterState) -> dict:
    """【code 节点】扫描草稿中的禁用词，全部命中则回跳 draft。

    禁用词来源: input_data.blacklist_words，缺省用 DEFAULT_BLACKLIST。
    """
    draft = _first_text(state, "draft")
    input_data = state.get("input_data") or {}
    words = input_data.get("blacklist_words") or DEFAULT_BLACKLIST
    hits = [w for w in words if w and w in draft]
    state["blacklist_hits"] = hits

    if hits:
        state["check_error"] = f"禁用词扫描失败: 命中 {hits}。请替换为自然表达后重新输出完整正文。"
        msg = AIMessage(content=f"✗ 禁用词扫描: 命中 {hits}，回跳 draft 重写")
    else:
        state["check_error"] = ""
        msg = AIMessage(content="✓ 禁用词扫描: 未命中")
    return {"messages": [msg], "blacklist_hits": hits, "check_error": state["check_error"]}