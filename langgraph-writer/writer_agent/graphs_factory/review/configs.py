"""审稿子图配置。"""

NODE_NAME = "review"
TOOL_NAMES = [
    "continuity_check",
    "ai_trace_check",
    "pacing_control",
    "hook_opening",
    "dialogue_craft",
    "scene_description",
    "emotion_scene",
    "action_scene",
    "suspense_twist",
    "narrative_viewpoint",
]
AFTER_TOOLS_MSG = "审稿工具执行完毕，请查看审稿结果并继续"
