"""Skill 工具：title-blurb（源自 .opencode/skills/title-blurb/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="书名简介文案",
    description="书名简介文案。当用户要起书名、写简介、写宣传语tagline、起章节标题，或觉得书名/简介不行要改时使用。",
)
def title_blurb(positioning: str = "", content: str = "") -> str:
    """按书名简介规范执行：书名给≥5个候选并按四路数(悬念钩子/高概念/意象情绪/主角宣言)分型呈现(3~8字、好读好搜)；简介按公式(钩子首句/主角与赌注/卖点展示/收尾悬念)给出≥2版不同侧重(一版重悬念一版重情绪，120~250字)；附15"""
    parts = []
    if positioning:
        parts.append("作品定位：题材/卖点/平台/目标读者:\n" + positioning)
    if content:
        parts.append("正文选段或关键梗概，供提炼用，可空:\n" + content)
    material = "\n".join(parts)
    return run_skill(
        "title-blurb",
        "按书名简介规范执行：书名给≥5个候选并按四路数(悬念钩子/高概念/意象情绪/主角宣言)分型呈现(3~8字、好读好搜)；简介按公式(钩子首句/主角与赌注/卖点展示/收尾悬念)给出≥2版不同侧重(一版重悬念一版重情绪，120~250字)；附15字内 tagline；如需要可给章节标题候选。",
        material,
    )
