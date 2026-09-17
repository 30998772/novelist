"""Skill 工具：emotion-scene（源自 .opencode/skills/emotion-scene/SKILL.md）。"""

from ._runner import run_skill
from .registry import regist_tool


@regist_tool(
    title="情感戏写作",
    description="情感戏写作。当用户要写感情戏、哭戏、告白、决裂、和解、亲情友情线，或觉得这段没打动人/情绪不到位时使用。",
)
def emotion_scene(text: str = "", scene_type: str = "") -> str:
    """按情感戏公式(压抑蓄力→导火索→宣泄→余波)执行；催泪技法(具体物件承载情感/克制比嚎啕有力/错位催泪/让读者先于角色意识到失去)；告白与关系推进三步舞(靠近-退缩-再靠近)；冲突戏双方都有理、最狠的话戳真软肋、吵完留裂缝。红线：禁报菜名式"""
    parts = []
    if text:
        parts.append("要写的情感戏概述 / 已有草稿:\n" + text)
    if scene_type:
        parts.append("场景类型：感情推进/告白/决裂/哭戏/和解:\n" + scene_type)
    material = "\n".join(parts)
    return run_skill(
        "emotion-scene",
        "按情感戏公式(压抑蓄力→导火索→宣泄→余波)执行；催泪技法(具体物件承载情感/克制比嚎啕有力/错位催泪/让读者先于角色意识到失去)；告白与关系推进三步舞(靠近-退缩-再靠近)；冲突戏双方都有理、最狠的话戳真软肋、吵完留裂缝。红线：禁报菜名式写情绪、情绪转折要有过程。输出改写后的场景或逐段修改建议。",
        material,
    )
