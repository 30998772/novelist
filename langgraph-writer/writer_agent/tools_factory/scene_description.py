"""Skill 工具：scene-description（源自 .opencode/skills/scene-description/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="描写技巧与画面感",
    description="描写技巧与画面感。当用户要加强画面感、写景写人写物、这段太干没画面、需要五感描写或氛围渲染时使用。",
)
def scene_description(text: str = "", focus: str = "") -> str:
    """按描写技巧执行：展示而非陈述(情绪外化为动作与生理反应)；五感调度(重要场景至少两种非视觉感官)；描写三问过滤(服务情绪/人物/伏笔？能更具体吗？视点人物此刻会注意到吗？)；按分场景配方(环境/外貌/氛围/心理)对给定文字加画面或改写。红线"""
    parts = []
    if text:
        parts.append("待改写/待加强描写的文字:\n" + text)
    if focus:
        parts.append("侧重：环境/外貌/氛围/心理:\n" + focus)
    material = "\n".join(parts)
    return run_skill(
        "scene-description",
        "按描写技巧执行：展示而非陈述(情绪外化为动作与生理反应)；五感调度(重要场景至少两种非视觉感官)；描写三问过滤(服务情绪/人物/伏笔？能更具体吗？视点人物此刻会注意到吗？)；按分场景配方(环境/外貌/氛围/心理)对给定文字加画面或改写。红线：比喻连用不超两个/段、描写段落≤5行。",
        material,
    )
