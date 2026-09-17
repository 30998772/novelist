"""Skill 工具：revision（源自 .opencode/skills/revision/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="改稿润色与审稿",
    description="改稿润色与审稿。当用户要修改章节、润色文字、精简压缩、调整节奏，或要求对稿子提意见时使用。",
)
def revision(text: str = "", mode: str = "") -> str:
    """按改稿润色流程执行：先诊断后动刀；三层检查(结构层：是否推进一件事/场景顺序/开头钩子；场景层：节奏/视角越界/信息泄露；文字层：删冗余、对话标签、AI腔套话、长句拆短)；输出格式：结构/场景/文字三栏，每条给位置+问题+建议。红线：不擅自"""
    parts = []
    if text:
        parts.append("待审/待改的稿子:\n" + text)
    if mode:
        parts.append("direct=直接改 / advice=只提意见:\n" + mode)
    material = "\n".join(parts)
    return run_skill(
        "revision",
        "按改稿润色流程执行：先诊断后动刀；三层检查(结构层：是否推进一件事/场景顺序/开头钩子；场景层：节奏/视角越界/信息泄露；文字层：删冗余、对话标签、AI腔套话、长句拆短)；输出格式：结构/场景/文字三栏，每条给位置+问题+建议。红线：不擅自改变情节走向与人物性格。",
        material,
    )
