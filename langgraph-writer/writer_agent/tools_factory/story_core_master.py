"""Skill 工具：story-core-master + story-depth-ai（源自 .opencode/skills/{story-core-master,story-depth-ai}/SKILL.md）。

mode 命中「丰满/AI/深度」走 story-depth-ai 丰满度补强与 AI 协作; 否则走 story-core-master 核心掌控。
"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="故事核心掌控",
    description="故事核心掌控/丰满度与AI协作。当用户看不透作品为什么好/为什么差、想动笔但不知核心抓什么、已有初稿觉得差一口气、写到一半自我怀疑时使用；当用户用AI写的东西对但不动人、能跑通但薄、想用AI但不想被带偏时也用（mode 传「丰满度」）。",
)
def story_core_master(material: str = "", mode: str = "", goal: str = "") -> str:
    """按需执行核心掌控或丰满度与AI协作。mode=「丰满度/AI协作」: 三问速判(丰满还是堆砌)+四层丰满度模型(人物/关系/情绪/主题层)0-20量化评分+指出最需补强层+把「感觉」翻译成具体画面与情绪指令(期望效果传 goal)+给出让 AI 出三版本试写、按标尺反修全篇的操作建议；其余 mode（识别类型/启动新故事找核心/初稿修正）或留空: 四问定类型→类型坐标与复合结构；六维评分(0-10)与总分判断；一句话说清核心；找最根本的敌人；初稿修正则降维、找最接近一处、把感觉翻成一句话、只重写关键场景、反向修订全篇"""
    if mode and ("丰满" in mode or "AI" in mode or "深度" in mode):
        parts = []
        if material:
            parts.append("正文/场景片段:\n" + material)
        if goal:
            parts.append("期望情绪或效果（如：湿冷克制、告别感）:\n" + goal)
        return run_skill(
            "story-depth-ai",
            "按故事丰满度与AI协作法执行：三问速判(丰满还是堆砌)；四层丰满度模型(人物/关系/情绪/主题层)量化评分 0-20 并给总分评估；指出最需要补强的层；把「感觉」翻译成具体画面与情绪指令，给出让 AI 出三版本试写、再按标尺反修全篇的操作建议。",
            "\n".join(parts),
        )
    parts = []
    if material:
        parts.append("故事介绍/大纲/正文片段/构思:\n" + material)
    if mode:
        parts.append("识别类型 / 启动新故事找核心 / 初稿修正:\n" + mode)
    return run_skill(
        "story-core-master",
        "按故事核心掌控法执行：四问定类型→给出类型坐标与复合结构；六维评分(每项0-10并给依据与总分判断)；用一句话说清核心；找最根本的敌人；如为初稿修正则先降维、找最接近的一处、把感觉翻译成一句话、只重写关键场景、反向修订全篇。",
        "\n".join(parts),
    )