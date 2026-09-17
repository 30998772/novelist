"""从 `.opencode/skills/<name>/SKILL.md` 运行时加载技能内容。

langgraph-writer 作为 writer 项目的一个子目录运行, 技能文档与 agent 文档
保持在 writer 项目的根目录（单份事实来源）。skill 工具内部调用 LLM 前
把对应 SKILL.md（及 reference 参考文件）注入 prompt。
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = PROJECT_ROOT / ".opencode" / "skills"


def load_skill(name: str) -> str:
    """读取技能 SKILL.md 正文（去掉 YAML frontmatter）。"""
    path = SKILLS_ROOT / name / "SKILL.md"
    if not path.exists():
        return f"（技能文档缺失: {path}）"
    text = path.read_text(encoding="utf-8")
    return _strip_frontmatter(text)


def load_reference(name: str, filename: str) -> str:
    """读取技能目录下 reference/ 子目录中的知识文件。"""
    path = SKILLS_ROOT / name / "reference" / filename
    if not path.exists():
        return f"（参考文件缺失: {path}）"
    return path.read_text(encoding="utf-8")


def load_skill_with_references(name: str, refs: list[str]) -> str:
    """技能正文 + 指定 reference 文件拼接为完整规则文本。"""
    parts = []
    for ref in refs:
        parts.append(f"### 知识库文件: reference/{ref}\n\n{load_reference(name, ref)}")
    rule = load_skill(name)
    if parts:
        rule = rule + "\n\n---\n\n以下为检测规则参考知识库（正文中对它们的引用以此为准）:\n\n" + "\n\n".join(parts)
    return rule


def load_skill_retrieved(name: str, query: str, refs: list[str] | None = None,
                         top_k: int | None = None) -> str:
    """技能正文 + RAG 召回的参考片段（替代全量注入）。

    以 query（通常是本次任务+素材）从知识库索引里召回该技能 reference 下最相关的
    top-k 片段。任何异常或无召回都回退到 load_skill_with_references 的全量注入，
    保证不影响既有行为。
    """
    base = load_skill(name)
    if os.environ.get("WRITER_RAG", "1") == "0":
        return load_skill_with_references(name, refs or [])
    try:
        from ..rag import retrieve

        k = top_k or int(os.environ.get("WRITER_RAG_TOP_K", "6"))
        hits = retrieve(query, k=k, scope="knowledge", source_filter=f"/skills/{name}/")
        hits = [h for h in hits if not h["source"].endswith("/SKILL.md")]
        if not hits:
            return load_skill_with_references(name, refs or [])
        context = "\n\n".join(
            f"### 召回片段（score={h['score']}，{h['source']}）\n{h['text']}"
            for h in hits
        )
        return (
            base
            + "\n\n---\n\n以下为按当前任务从知识库检索出的参考片段（RAG 召回，按相关度排序）:\n\n"
            + context
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[rag] 检索失败，回退全量注入: {exc}")
        return load_skill_with_references(name, refs or [])


def _strip_frontmatter(text: str) -> str:
    """移除 ``` 开头的三个反引号块与 YAML frontmatter (---\n...\n---)。"""
    stripped = text.strip()
    sub_lines = stripped.split("\n")
    if sub_lines and sub_lines[0].startswith("```"):
        sub_lines = sub_lines[1:]
        # 反引号语言标注行也可能出现, 直接找到再一个 ``` 为结束
        end = next((i for i, ln in enumerate(sub_lines) if ln.strip().startswith("```")), None)
        if end is not None:
            sub_lines = sub_lines[end + 1:]
    if sub_lines and sub_lines[0].strip() == "---":
        end = next((i for i, ln in enumerate(sub_lines[1:], start=1) if ln.strip() == "---"), None)
        if end is not None:
            sub_lines = sub_lines[end + 1:]
    return "\n".join(sub_lines).strip()