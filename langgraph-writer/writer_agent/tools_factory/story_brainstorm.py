"""Skill 工具：story-brainstorm（源自 .opencode/skills/story-brainstorm/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="故事头脑风暴",
    description="新书构思与头脑风暴。当用户想开新小说、找灵感、讨论点子/创意、确定题材类型、提炼高概念或一句话故事时使用。",
)
def story_brainstorm(idea: str = "", genre: str = "") -> str:
    """根据偏好进行新书头脑风暴：先了解类型/篇幅/目标读者偏好，发散给出 3 个方向明显不同的方案（每个含一句话高概念 logline、类型定位与对标作品、核心冲突(外部+内部)、2~3 个亮点/名场面设想、风险提示），用表格对比卖点/难度/市场"""
    parts = []
    if idea:
        parts.append("用户想写什么/已有灵感/一句话点子:\n" + idea)
    if genre:
        parts.append("意向类型：玄幻/都市/科幻/悬疑/言情/历史等，可空:\n" + genre)
    material = "\n".join(parts)
    return run_skill(
        "story-brainstorm",
        "根据偏好进行新书头脑风暴：先了解类型/篇幅/目标读者偏好，发散给出 3 个方向明显不同的方案（每个含一句话高概念 logline、类型定位与对标作品、核心冲突(外部+内部)、2~3 个亮点/名场面设想、风险提示），用表格对比卖点/难度/市场空间，最后收敛给出推荐，并按构思检查清单自检。",
        material,
    )
