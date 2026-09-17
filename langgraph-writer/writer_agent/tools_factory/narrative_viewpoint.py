"""Skill 工具：narrative-viewpoint（源自 .opencode/skills/narrative-viewpoint/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="叙事视角检查",
    description="叙事视角与人称选择。当用户要确定人称、切换POV、调整叙事距离、处理多视角结构，或觉得视角混乱/上帝视角太多/代入感差时使用。",
)
def narrative_viewpoint(text: str = "", task: str = "") -> str:
    """按叙事视角规范执行：给出视角选项与叙事距离建议；检查单场景视点纪律(只写视点人物看到听到想到、禁止镜头偷跑、全知评论腔是否泛滥、有无偷偷换脑袋)；对给定文本按视角混乱自查清单逐项检查并给出具体改法(引用原文位置+改写示例)。"""
    parts = []
    if text:
        parts.append("待检查章节/片段:\n" + text)
    if task:
        parts.append("要做的动作：检查视角纪律 / 设计视角方案 / 调整叙事距离:\n" + task)
    material = "\n".join(parts)
    return run_skill(
        "narrative-viewpoint",
        "按叙事视角规范执行：给出视角选项与叙事距离建议；检查单场景视点纪律(只写视点人物看到听到想到、禁止镜头偷跑、全知评论腔是否泛滥、有无偷偷换脑袋)；对给定文本按视角混乱自查清单逐项检查并给出具体改法(引用原文位置+改写示例)。",
        material,
    )
