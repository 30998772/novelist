"""Skill 工具：dragon-ride-007（源自 .opencode/skills/dragon-ride-007/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="龙骑007：规则破坏型智斗",
    description="规则破坏型智斗写作。当用户要写主角利用系统漏洞、规则博弈、以智破力、meta叙事、创作者悖论、理解规则→利用规则→超越规则的叙事结构时使用。",
)
def dragon_ride_007(idea: str = "", mode: str = "") -> str:
    """按龙骑007风格执行：金手指必须先写三条限制再写一个代价；规则透明化(在冲突中展示不在说明中展示)；智斗公式 理解→利用→超越(含规则反制升级)；智能反派设计；如 meta 叙事则延迟揭示/线索即编辑痕迹/文本自愈力/创作者悖论；非人视角用"""
    parts = []
    if idea:
        parts.append("故事构思/正文片段/金手指设定:\n" + idea)
    if mode:
        parts.append("设计金手指与规则 / 写一个智斗场景 / 检查正文:\n" + mode)
    material = "\n".join(parts)
    return run_skill(
        "dragon-ride-007",
        "按龙骑007风格执行：金手指必须先写三条限制再写一个代价；规则透明化(在冲突中展示不在说明中展示)；智斗公式 理解→利用→超越(含规则反制升级)；智能反派设计；如 meta 叙事则延迟揭示/线索即编辑痕迹/文本自愈力/创作者悖论；非人视角用数据语言替代情感词汇。按自查清单输出方案/改写。",
        material,
    )
