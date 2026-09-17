"""Skill 工具：hook-opening（源自 .opencode/skills/hook-opening/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="开篇与钩子设计",
    description="开篇与钩子设计。当用户要写开头、改第一章、设计黄金三章、提升留存、开篇不够抓人、设计章末悬念时使用。",
)
def hook_opening(text: str = "", position: str = "") -> str:
    """按开篇与钩子规范执行：开篇三要素检查(前500字内完成：具体人物做具体的事/反常信号/问题钩子)；黄金三章标准核对(第一章主角+核心冲突+卖点亮相+钩子，第二章卖点兑现，第三章小高潮)；列出常见死法命中项；章末钩子类型轮换与兑现时效检查；输"""
    parts = []
    if text:
        parts.append("待检查/待设计的开篇或章节:\n" + text)
    if position:
        parts.append("开篇(前500字) / 黄金三章 / 章末钩子:\n" + position)
    material = "\n".join(parts)
    return run_skill(
        "hook-opening",
        "按开篇与钩子规范执行：开篇三要素检查(前500字内完成：具体人物做具体的事/反常信号/问题钩子)；黄金三章标准核对(第一章主角+核心冲突+卖点亮相+钩子，第二章卖点兑现，第三章小高潮)；列出常见死法命中项；章末钩子类型轮换与兑现时效检查；输出具体修改建议或直接改写。",
        material,
    )
