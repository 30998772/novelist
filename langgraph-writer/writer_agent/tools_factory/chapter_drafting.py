"""Skill 工具：chapter-drafting（源自 .opencode/skills/chapter-drafting/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="章节正文写作",
    description="章节正文写作主流程。当用户要写新章、续写下一章、扩写场景、按大纲产出正文时使用。",
)
def chapter_drafting(material: str = "", target_word_count: int = 3500) -> str:
    """按「一章一个故事」铁律撰写章节正文：遵循动笔前检查要求(衔接上章、核对伏笔准备、对照人物语言特征)；场景遵循 目标-冲突-结果；遵守文风纪律(展示而非说教、对话推进剧情或刻画人物、避免AI腔套话、单段≤5行、章末必有钩子)；按素材中给出的目"""
    parts = []
    if material:
        parts.append("本章大纲卡片/前后章衔接/出场人物语音特征等背景:\n" + material)
    if target_word_count != 3500:
        parts.append("目标中文字符数:\n" + str(target_word_count))
    material = "\n".join(parts)
    return run_skill(
        "chapter-drafting",
        "按「一章一个故事」铁律撰写章节正文：遵循动笔前检查要求(衔接上章、核对伏笔准备、对照人物语言特征)；场景遵循 目标-冲突-结果；遵守文风纪律(展示而非说教、对话推进剧情或刻画人物、避免AI腔套话、单段≤5行、章末必有钩子)；按素材中给出的目标字数产出完整正文。输出正文本身。",
        material,
    )
