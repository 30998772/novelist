"""Skill 工具：action-scene（源自 .opencode/skills/action-scene/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="动作与战斗戏写作",
    description="动作与战斗戏写作。当用户要写打斗、追逐、战斗高潮、能力对决，或觉得打戏看不清谁在打谁/不够燃时使用。",
)
def action_scene(text: str = "", power_rules: str = "") -> str:
    """按打斗戏写作规范执行：清晰第一(谁在哪朝哪动想干什么、空间分层、攻防交换后重新定位)；节拍结构(试探→交手升级→危机→翻盘(只用前文铺垫的能力/道具/环境)→定格)；燃感来源(契诃夫之枪回收/代价可见/旁观者放大器/短句分行)；能力体系纪律"""
    parts = []
    if text:
        parts.append("要写的打斗概述 / 已有草稿:\n" + text)
    if power_rules:
        parts.append("力量体系规则/能力限制与代价，可空:\n" + power_rules)
    material = "\n".join(parts)
    return run_skill(
        "action-scene",
        "按打斗戏写作规范执行：清晰第一(谁在哪朝哪动想干什么、空间分层、攻防交换后重新定位)；节拍结构(试探→交手升级→危机→翻盘(只用前文铺垫的能力/道具/环境)→定格)；燃感来源(契诃夫之枪回收/代价可见/旁观者放大器/短句分行)；能力体系纪律(遵守已定规则、越强限制越狠)。红线：禁流水账招数罗列。输出清晰的战斗场面或逐段修改。",
        material,
    )
