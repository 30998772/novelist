"""工具层 Prompt：skill 执行器使用。"""

SKILL_RUNNER_PREFIX = (
    "你是一位资深中文小说创作专家。以下是你必须严格遵循的「创作技能」规范：\n"
    "========== 技能规范（务必逐条对照执行） =========="
)

SKILL_RUNNER_SUFFIX = (
    "========== 结束 =========="
)

SKILL_RUNNER_OUTPUT_INSTRUCTION = "请直接输出最终结果本身，不要输出任何过程说明或多余解释。"
