"""Skill 工具：story-outline + outline-scoring（源自 .opencode/skills/{story-outline,outline-scoring}/SKILL.md）。

mode=「设计」走 story-outline 大纲搭建; mode=「评分」走 outline-scoring 大纲评分诊断。
"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="大纲与情节结构设计",
    description="大纲与情节结构设计/评分。当用户要设计大纲、规划章节卷册、安排情节节奏伏笔高潮、拆分细纲时使用；当用户要评估大纲质量、给大纲打分、诊断大纲问题或优化大纲时也用（mode 传「评分」）。",
)
def story_outline(material: str = "", mode: str = "设计", pref: str = "") -> str:
    """搭建小说整体结构与章节细纲，或对已有大纲评分诊断。mode=「设计」(默认): 按篇幅选择骨架，产出总纲(一句话概括/多部总览/核心主线/暗线总表/商业定位)、分部总纲模板、逐章卡片模板（含 POV/场景/目标/冲突/转折钩子/伏笔F-编号/状态），并把伏笔登记为 F-编号总表，标注预计回收位置；mode=「评分」: 把 material 当大纲全文，pref 传补充材料，按 8维100分制(题材创意15/世界观构建15/人物塑造15/情节节奏15/文笔质量15/结构完整度10/风格纪律10/IP潜力5)逐项打分"""
    if mode and ("评" in mode or "分" in mode or "打分" in mode):
        parts = []
        if material:
            parts.append("待评分大纲全文:\n" + material)
        if pref:
            parts.append("补充材料：角色档案/伏笔登记表/风格指南等，可空:\n" + pref)
        return run_skill(
            "outline-scoring",
            "按大纲质量评分系统执行：8维100分制(题材创意15/世界观构建15/人物塑造15/情节节奏15/文笔质量15/结构完整度10/风格纪律10/IP潜力5)逐项打分并给具体依据；叠加 story-core-master 的 6 维 60 分核心成色评分(人物不可替代性/关系张力/情绪落点/设定根基/核心痛感/作者冲动)；输出评级(S/A/B/C/D/F)、按严重程度排序的核心问题、针对性优化方案(预计加分)与优化后目标分。红线：核心成色<19 时结论须为「不要改文字，先找核心的人」。",
            "\n".join(parts),
        )
    parts = []
    if material:
        parts.append("已有构思/题材/设定/用户要求:\n" + material)
    if pref:
        parts.append("篇幅与结构偏好：短篇(起承转合)/中长篇(三幕式)/超长连载(先主线再卷再章):\n" + pref)
    return run_skill(
        "story-outline",
        "搭建小说整体结构与章节细纲：按篇幅选择骨架，产出总纲(一句话概括/多部总览/核心主线/暗线总表/商业定位)、分部总纲模板、逐章卡片模板（含 POV/场景/目标/冲突/转折钩子/伏笔F-编号/状态），并把伏笔登记为 F-编号总表，标注预计回收位置。",
        "\n".join(parts),
    )