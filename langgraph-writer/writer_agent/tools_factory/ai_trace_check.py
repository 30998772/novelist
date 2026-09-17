"""Skill 工具：ai-trace-check（源自 .opencode/skills/ai-trace-check/SKILL.md）。"""

from ._runner import run_skill_ref
from .registry import regist_tool


@regist_tool(
    title="AI写作痕迹检测与消除",
    description="AI写作痕迹检测与消除。当用户要扫描正文、识别AI腔、降重、润色、觉得这章AI味重时使用。",
)
def ai_trace_check(text: str = "", also_rewrite: bool = False) -> str:
    """按 AI 痕迹检测规范执行：逐项全量扫描(高频词统计/每万字密度对照目标、AI腔句式标记、破折号≤12处/万字、省略号≤8处/万字、感叹号≤10处/万字、超80字长句、比喻密度每万字≤5个明喻、段落整齐度)；输出扫描报告(表格)；如 als"""
    parts = []
    if text:
        parts.append("待扫描的正文/章节:\n" + text)
    if also_rewrite != False:
        parts.append("是否顺带输出改写后的降AI版本:\n" + str(also_rewrite))
    material = "\n".join(parts)
    return run_skill_ref(
        "ai-trace-check",
        "按 AI 痕迹检测规范执行：逐项全量扫描(高频词统计/每万字密度对照目标、AI腔句式标记、破折号≤12处/万字、省略号≤8处/万字、感叹号≤10处/万字、超80字长句、比喻密度每万字≤5个明喻、段落整齐度)；输出扫描报告(表格)；如 also_rewrite 为 true 则输出消除后的正文版本。纪律：只动文风不动情节，数据要准。",
        material,
        refs=["高频词清单.md", "AI腔句式.md", "标点规范.md", "重复类型.md", "替换方案.md", "各书特殊规则.md"],
    )
