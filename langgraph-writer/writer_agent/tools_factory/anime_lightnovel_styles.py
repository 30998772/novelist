"""Skill 工具：anime-lightnovel-styles（源自 .opencode/skills/anime-lightnovel-styles/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="日式ACGN风格参考库",
    description="日式ACGN经典风格参考库。当用户要参考模仿钢之炼金术师(等价交换)、DRRR(多线群像)、夏目友人帐(温柔单元)、物语系列(话痨藏真相)的风格、叙事结构、世界观或美学系统时使用。",
)
def anime_lightnovel_styles(style: str = "", material: str = "") -> str:
    """从所选日式风格中提取「为什么好看」的底层逻辑并转化为叙事工具应用到素材上：钢炼=等价交换规则与代价透明；DRRR=多线POV与信息差悬念、城市人格化；夏目=单元剧+情感留白、温柔中一丝寂寞的节奏；物语=对话驱动藏关键信息、怪异对应心理、残缺"""
    parts = []
    if style:
        parts.append("目标风格：钢炼 / DRRR / 夏目 / 物语 / 组合:\n" + style)
    if material:
        parts.append("要套用该风格的文本/设定/章节需求:\n" + material)
    material = "\n".join(parts)
    return run_skill(
        "anime-lightnovel-styles",
        "从所选日式风格中提取「为什么好看」的底层逻辑并转化为叙事工具应用到素材上：钢炼=等价交换规则与代价透明；DRRR=多线POV与信息差悬念、城市人格化；夏目=单元剧+情感留白、温柔中一丝寂寞的节奏；物语=对话驱动藏关键信息、怪异对应心理、残缺即个性。给出一段完整改写/创作示例。",
        material,
    )
