"""Skill 工具：character-design（源自 .opencode/skills/character-design/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="人物设计与档案",
    description="人物设计与档案管理。当用户要创建角色、完善人设、设计人物关系网、分析人物弧线，或写作中发现人设问题时使用。",
)
def character_design(concept: str = "", role: str = "") -> str:
    """按人物档案模板输出角色档案：基本信息/外貌辨识点/性格核心特质+一个缺陷/欲望vs恐惧/背景故事(3条内)/语言特征(保证对话可辨识)/成长弧线/人物关系/专属符号/宿命语录。配角精简，单元人物按单元模板。守则：动机自洽、弧线绑定主线、一致"""
    parts = []
    if concept:
        parts.append("角色设想：名字/身份/性格倾向/剧情功能:\n" + concept)
    if role:
        parts.append("主要角色 / 配角 / 单元人物:\n" + role)
    material = "\n".join(parts)
    return run_skill(
        "character-design",
        "按人物档案模板输出角色档案：基本信息/外貌辨识点/性格核心特质+一个缺陷/欲望vs恐惧/背景故事(3条内)/语言特征(保证对话可辨识)/成长弧线/人物关系/专属符号/宿命语录。配角精简，单元人物按单元模板。守则：动机自洽、弧线绑定主线、一致性铁律。",
        material,
    )
