"""Skill 工具：recommend-platform（源自 .opencode/skills/recommend-platform/SKILL.md）。"""

from ._runner import run_skill_ref
from .registry import regist_tool


@regist_tool(
    title="推荐投递平台",
    description="推荐投递平台。当用户写完一本书、想投稿、或询问这本书该投哪里时使用。",
)
def recommend_platform(book_type: str = "", genre: str = "", length: str = "", target_reader: str = "") -> str:
    """按书目信息推荐投递平台：依据平台数据库与类型匹配规则，输出「高度匹配(优先投稿)/可尝试/不推荐」三档表格(含分成模式、匹配理由、投稿方式)，并给出投稿注意事项与投稿记录表模板。"""
    parts = []
    if book_type:
        parts.append("书籍类型:\n" + book_type)
    if genre:
        parts.append("题材风格:\n" + genre)
    if length:
        parts.append("篇幅:\n" + length)
    if target_reader:
        parts.append("目标读者/平台偏好，可空:\n" + target_reader)
    material = "\n".join(parts)
    return run_skill_ref(
        "recommend-platform",
        "按书目信息推荐投递平台：依据平台数据库与类型匹配规则，输出「高度匹配(优先投稿)/可尝试/不推荐」三档表格(含分成模式、匹配理由、投稿方式)，并给出投稿注意事项与投稿记录表模板。",
        material,
        refs=["平台数据库.md", "类型匹配规则.md", "投稿注意事项.md"],
    )
