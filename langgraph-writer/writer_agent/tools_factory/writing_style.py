"""Skill 工具：writing-style（源自 .opencode/skills/writing-style/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="文风分析与定制",
    description="文风分析与定制。当用户要定义文风、分析模仿某作者风格、统一语言风格、生成文风指南，或要求按某种文风写/这段文风不对时使用。",
)
def writing_style(sample: str = "", text: str = "", target: str = "") -> str:
    """按文风六要素(句式节奏/词汇色彩/叙述温度/意象偏好/幽默感/信息方式)分析样本文本输出「文风画像」表格(逐项评级+原文例句佐证)；如需应用，则提炼文风配方(正面示例段/禁用清单/句式配方)并对给定文字按该文风改写。模仿守则：只学特征不抄句"""
    parts = []
    if sample:
        parts.append("风格样本文本:\n" + sample)
    if text:
        parts.append("需要按该风格改写或书写的文字:\n" + text)
    if target:
        parts.append("目标文风（冷峻硬朗/轻快吐槽/绵密抒情/古典雅致/悬疑冷峻等，可空）:\n" + target)
    material = "\n".join(parts)
    return run_skill(
        "writing-style",
        "按文风六要素(句式节奏/词汇色彩/叙述温度/意象偏好/幽默感/信息方式)分析样本文本输出「文风画像」表格(逐项评级+原文例句佐证)；如需应用，则提炼文风配方(正面示例段/禁用清单/句式配方)并对给定文字按该文风改写。模仿守则：只学特征不抄句子、禁止复用原文连续7字以上。",
        material,
    )
