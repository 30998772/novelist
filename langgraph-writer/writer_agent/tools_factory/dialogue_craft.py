"""Skill 工具：dialogue-craft（源自 .opencode/skills/dialogue-craft/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="对话写作与打磨",
    description="对话写作与打磨。当用户要写对话戏、优化对白、区分角色口吻、加潜台词，或觉得对话生硬/像念台词/所有人说话一个腔调时使用。",
)
def dialogue_craft(text: str = "", characters: str = "") -> str:
    """按对话三重功能(推进情节/塑造人物/制造张力)检查给定对话：删除纯寒暄；用潜台词技法让说的与想要的错位；如有角色信息则做角色声纹区分检查(遮住名字能猜出是谁)；按技术规范(动作beat代替“说”、连续对话插动作、不塞info dump)输出"""
    parts = []
    if text:
        parts.append("待检查/待打磨的对话段落:\n" + text)
    if characters:
        parts.append("出场人物及其声纹四件套(句长习惯/口头禅/称呼方式/回避什么)，可空:\n" + characters)
    material = "\n".join(parts)
    return run_skill(
        "dialogue-craft",
        "按对话三重功能(推进情节/塑造人物/制造张力)检查给定对话：删除纯寒暄；用潜台词技法让说的与想要的错位；如有角色信息则做角色声纹区分检查(遮住名字能猜出是谁)；按技术规范(动作beat代替“说”、连续对话插动作、不塞info dump)输出逐句修改建议或直接改写。",
        material,
    )
