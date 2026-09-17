"""skill 工具的公共执行器：规则加载 + LLM 调用。

工具内部调用 LLM 产出结果（按用户选定的设计）：
1. 运行时加载对应技能规则（load_skill / load_skill_with_references）;
2. 把「技能规则 + 任务要求 + 用户素材」拼成 prompt, 调用 LLM;
3. 直接返回 LLM 生成的最终结果文本。
"""

from typing import Optional

from langchain_core.messages import HumanMessage

from ..llm import get_llm
from ._files import load_skill, load_skill_retrieved, load_skill_with_references


def run_skill(
    name: str,
    task: str,
    material: str = "",
    rules: Optional[str] = None,
    temperature: Optional[float] = None,
    output_hint: str = "",
) -> str:
    """按指定技能（skill）执行一次 LLM 生成。

    Args:
        name: 技能目录名（.opencode/skills/<name>）。
        task: 本次要产出的内容要求。
        material: 用户提供的素材/待处理文本。
        rules: 覆盖规则文本（默认 load_skill(name)）。
        temperature: 覆盖 LLM 温度。
        output_hint: 追加到 prompt 末尾的输出格式约束。
    """
    if rules is None:
        rules = load_skill(name)

    prompt_parts = [
        "你是一位资深中文小说创作专家。以下是你必须严格遵循的「创作技能」规范：",
        "========== 技能规范（务必逐条对照执行） ==========",
        rules,
        "========== 结束 ==========",
        "",
    ]
    if task:
        prompt_parts.append(f"任务：{task}")
    if material and material.strip():
        prompt_parts.append(f"用户提供的素材/文本：\n{material}")
    if output_hint:
        prompt_parts.append(output_hint)
    prompt_parts.append("请直接输出最终结果本身，不要输出任何过程说明或多余解释。")

    resp = get_llm(temperature=temperature).invoke([HumanMessage(content="\n".join(prompt_parts))])
    return str(resp.content).strip() if resp.content is not None else ""


def run_skill_ref(
    name: str,
    task: str,
    material: str = "",
    refs: Optional[list[str]] = None,
    temperature: Optional[float] = None,
    output_hint: str = "",
) -> str:
    """同 run_skill, 但注入 reference/ 知识库。

    默认走 RAG：以「任务+素材」为 query 召回最相关片段（见 load_skill_retrieved）；
    无索引/检索失败时自动回退为全量注入（load_skill_with_references）。
    """
    query = "\n".join(x for x in (task, material) if x and x.strip())
    rules = load_skill_retrieved(name, query, refs=refs)
    return run_skill(name, task, material, rules=rules, temperature=temperature, output_hint=output_hint)