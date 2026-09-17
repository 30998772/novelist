"""Skill 工具：urobuchi-gen（源自 .opencode/skills/urobuchi-gen/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="老虚：温柔致郁型哲学解构",
    description="温柔致郁型哲学解构写作。当用户要写没有反派只有遗憾、宿命性悲剧、存在主义困境、创作者伦理、美丽而痛苦的叙事、修复一切除了自己的救赎者时使用。",
)
def urobuchi_gen(idea: str = "") -> str:
    """按老虚风格执行：用结构性困境替代正邪对立(所有角色做对的事但代价碰撞)；宿命感与自由意志张力(性格即宿命、给可以放弃的选择点)；温柔中埋刺的节奏(致郁场景≤2段回温暖)；为角色设计宿命语录与三位一体美学符号(色彩+视觉标记+语录)；设计世界"""
    parts = []
    if idea:
        parts.append("故事构思/正文片段/角色/铁律设想:\n" + idea)
    material = "\n".join(parts)
    return run_skill(
        "urobuchi-gen",
        "按老虚风格执行：用结构性困境替代正邪对立(所有角色做对的事但代价碰撞)；宿命感与自由意志张力(性格即宿命、给可以放弃的选择点)；温柔中埋刺的节奏(致郁场景≤2段回温暖)；为角色设计宿命语录与三位一体美学符号(色彩+视觉标记+语录)；设计世界观铁律；如涉创作伦理则直面创造即暴力/工具宿命/双向书写。",
        material,
    )
