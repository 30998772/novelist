"""Skill 工具：continuity-check（源自 .opencode/skills/continuity-check/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="一致性检查与伏笔追踪",
    description="一致性检查与伏笔追踪。当用户要排查前后矛盾、核对设定、检查伏笔回收、审查时间线，或连载前查漏时使用。",
)
def continuity_check(materials: str = "", focus: str = "") -> str:
    """按一致性检查执行：人物一致性(言行 vs 档案)、设定一致性(正文 vs 硬约束)、时间线(排事件轴找冲突)、伏笔账本(逾期预警/新铺垫补登/回收吻合)。按报告格式输出：🔴矛盾(引用位置)、🟡逾期伏笔、🟢通过项。只报告不擅改，修复方案列出选"""
    parts = []
    if materials:
        parts.append("待核对的正文/档案/设定文本，或填入主要矛盾线索:\n" + materials)
    if focus:
        parts.append("侧重：人物/设定/时间线/伏笔:\n" + focus)
    material = "\n".join(parts)
    return run_skill(
        "continuity-check",
        "按一致性检查执行：人物一致性(言行 vs 档案)、设定一致性(正文 vs 硬约束)、时间线(排事件轴找冲突)、伏笔账本(逾期预警/新铺垫补登/回收吻合)。按报告格式输出：🔴矛盾(引用位置)、🟡逾期伏笔、🟢通过项。只报告不擅改，修复方案列出选项。",
        material,
    )
