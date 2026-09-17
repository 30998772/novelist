"""Skill 工具：add-setting（源自 .opencode/skills/add-setting/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="补充设定与新素材入库",
    description="补充设定与新素材入库。当用户口述或提供新的经历素材、人物信息、背景设定，要求记录、归档、更新设定，或修正既有设定时使用。",
)
def add_setting(material: str = "", existing: str = "") -> str:
    """按补充设定流程执行：先把素材整理成条目清单复述确认；做冲突预检(与 existing 中既有设定对比，矛盾则停下报告差异给出「改设定」或「改正文」选项)；按素材去向表给出每条应写入的位置；每条加状态标记【硬设定】/【软设定】/【补白】/【待"""
    parts = []
    if material:
        parts.append("用户口述/提供的新素材原文:\n" + material)
    if existing:
        parts.append("既有相关设定或正文摘录，用于冲突预检，可空:\n" + existing)
    material = "\n".join(parts)
    return run_skill(
        "add-setting",
        "按补充设定流程执行：先把素材整理成条目清单复述确认；做冲突预检(与 existing 中既有设定对比，矛盾则停下报告差异给出「改设定」或「改正文」选项)；按素材去向表给出每条应写入的位置；每条加状态标记【硬设定】/【软设定】/【补白】/【待确认】；末尾回执：改动文件、新增条目数、新伏笔编号、【待确认】清单。",
        material,
    )
