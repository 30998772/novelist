"""Skill 工具：revision-log（源自 .opencode/skills/revision-log/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="修改记录登记",
    description="修改记录维护。当用户降AI痕迹、修bug、润色、改稿后需要登记修改记录时使用。",
)
def revision_log(chapter: str = "", change_type: str = "", change_desc: str = "", metrics: str = "") -> str:
    """按修改记录规范生成一条登记条目：按输出格式产出 YYYY-MM-DD + 修改类型简述 + 具体修改表格(章节/问题/修复方式) + 统计对比表格(修改前/后/变化) + 备注(保留原则/未动内容)。只追加不删除历史。"""
    parts = []
    if chapter:
        parts.append("涉及章节，如 ch007:\n" + chapter)
    if change_type:
        parts.append("修改类型：降AI/修重复/修逻辑/润色/调结构/调字数/修正设定:\n" + change_type)
    if change_desc:
        parts.append("本次修改的具体内容描述:\n" + change_desc)
    if metrics:
        parts.append("统计对比(高频词/破折号/重复段落等)，可空:\n" + metrics)
    material = "\n".join(parts)
    return run_skill(
        "revision-log",
        "按修改记录规范生成一条登记条目：按输出格式产出 YYYY-MM-DD + 修改类型简述 + 具体修改表格(章节/问题/修复方式) + 统计对比表格(修改前/后/变化) + 备注(保留原则/未动内容)。只追加不删除历史。",
        material,
    )
