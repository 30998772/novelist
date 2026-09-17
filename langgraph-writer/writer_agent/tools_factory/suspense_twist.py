"""Skill 工具：suspense-twist（源自 .opencode/skills/suspense-twist/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="悬念与反转设计",
    description="悬念与反转设计。当用户要埋悬念、设计反转、误导读者、揭示真相、追求意料之外情理之中的效果时使用。",
)
def suspense_twist(text: str = "", mode: str = "") -> str:
    """按悬念与反转规范执行：悬念三级火箭(大悬念分期兑付/中悬念卷级/小钩子章级)；反转三定律(意料之外/情理之中/代价真实)；公平性操作(列线索清单至少3条且已埋进正文、设计误导层、揭晓时回扣)；揭示时机与方式(压力最大处、大反转后留一章消化)"""
    parts = []
    if text:
        parts.append("目标段落/悬念或反转需求:\n" + text)
    if mode:
        parts.append("设计新反转 / 检查既有反转公平性:\n" + mode)
    material = "\n".join(parts)
    return run_skill(
        "suspense-twist",
        "按悬念与反转规范执行：悬念三级火箭(大悬念分期兑付/中悬念卷级/小钩子章级)；反转三定律(意料之外/情理之中/代价真实)；公平性操作(列线索清单至少3条且已埋进正文、设计误导层、揭晓时回扣)；揭示时机与方式(压力最大处、大反转后留一章消化)。按自查清单输出方案或对给定文本诊断建议。",
        material,
    )
