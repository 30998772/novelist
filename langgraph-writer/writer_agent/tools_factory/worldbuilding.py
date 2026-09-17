"""Skill 工具：worldbuilding（源自 .opencode/skills/worldbuilding/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="世界观构建",
    description="世界观与背景设定。当用户要构建世界背景、设计力量体系、历史地理社会制度、种族势力时使用。",
)
def worldbuilding(concept: str = "", modules: str = "") -> str:
    """按设定范围清单搭建世界观：核心概念、三大铁律(不可违反)、地理、历史(只写有用)、社会、力量体系(遵循代价与限制先于能力/规则透明/等级差距可感知)、势力、日常质感。每条影响剧情的硬设定标注「硬约束」。"""
    parts = []
    if concept:
        parts.append("世界背景想法/题材:\n" + concept)
    if modules:
        parts.append("需要的模块：核心概念/三大铁律/地理/历史/社会/力量体系/势力/日常，逗号分隔:\n" + modules)
    material = "\n".join(parts)
    return run_skill(
        "worldbuilding",
        "按设定范围清单搭建世界观：核心概念、三大铁律(不可违反)、地理、历史(只写有用)、社会、力量体系(遵循代价与限制先于能力/规则透明/等级差距可感知)、势力、日常质感。每条影响剧情的硬设定标注「硬约束」。",
        material,
    )
