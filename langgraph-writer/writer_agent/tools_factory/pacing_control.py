"""Skill 工具：pacing-control（源自 .opencode/skills/pacing-control/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="节奏与张力控制",
    description="节奏与张力控制。当用户觉得太平了/太赶了/拖沓/注水，要调节章节快慢、安排张弛、设计高潮低谷曲线、扩写或压缩场景时使用。",
)
def pacing_control(text: str = "", symptom: str = "") -> str:
    """按节奏控制执行：张力曲线诊断(注水自查：删掉主线受损吗/重复已知信息吗/对话同义反复吗；太赶自查：转折有铺垫吗/高潮篇幅够吗/情绪转变有过渡吗)；按快慢工具箱给出具体修改位置清单(引用原文位置+加速或减速的具体手法)，给出场景-反应单元调整"""
    parts = []
    if text:
        parts.append("待诊断的章节/片段:\n" + text)
    if symptom:
        parts.append("症状：太拖/太赶/太平/注水:\n" + symptom)
    material = "\n".join(parts)
    return run_skill(
        "pacing-control",
        "按节奏控制执行：张力曲线诊断(注水自查：删掉主线受损吗/重复已知信息吗/对话同义反复吗；太赶自查：转折有铺垫吗/高潮篇幅够吗/情绪转变有过渡吗)；按快慢工具箱给出具体修改位置清单(引用原文位置+加速或减速的具体手法)，给出场景-反应单元调整建议。",
        material,
    )
