"""建索引：扫描「知识库 + 正文」，切块、向量化、落盘。

scope:
  knowledge  = .opencode/skills/**/*.md（技能规则 + reference 参考知识库）
  manuscript = 各小说的 设定 / 章节大纲 / 正文 / 系列规划/**/*.md
"""

from __future__ import annotations

from pathlib import Path

from .chunk import chunk_markdown
from .store import Index, build, index_path, is_stale, load, save

# writer 项目根目录：langgraph-writer/writer_agent/rag/ingest.py -> parents[3]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = PROJECT_ROOT / ".opencode" / "skills"

_MANUSCRIPT_SUBDIRS = ("设定", "章节大纲", "正文", "系列规划")
_EXCLUDE_DIRS = {".git", "__pycache__", ".venv", ".rag", "_archive", "node_modules"}


def _iter_md(root: Path):
    if not root.exists():
        return
    for p in root.rglob("*.md"):
        if any(part in _EXCLUDE_DIRS for part in p.parts):
            continue
        yield p


def _novel_dirs() -> list[Path]:
    dirs = []
    for child in PROJECT_ROOT.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        if any((child / sub).is_dir() for sub in _MANUSCRIPT_SUBDIRS):
            dirs.append(child)
    return sorted(dirs)


def collect_files(scope: str) -> list[Path]:
    if scope == "knowledge":
        return sorted(_iter_md(SKILLS_ROOT))
    if scope == "manuscript":
        files: list[Path] = []
        for novel in _novel_dirs():
            for sub in _MANUSCRIPT_SUBDIRS:
                files.extend(_iter_md(novel / sub))
        return sorted(set(files))
    raise ValueError(f"未知 scope: {scope!r}（可选 knowledge / manuscript）")


def _docs_from(files: list[Path]) -> list[dict]:
    docs: list[dict] = []
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            continue
        rel = fp.relative_to(PROJECT_ROOT).as_posix()
        for ch in chunk_markdown(text):
            heading = ch.get("heading", "")
            body = ch["text"]
            docs.append({
                "source": rel,
                "heading": heading,
                "start": ch.get("start"),
                "end": ch.get("end"),
                "text": f"【{heading}】\n{body}" if heading else body,
            })
    return docs


def _rel(p: Path) -> str:
    return p.relative_to(PROJECT_ROOT).as_posix()


def _same_file_set(index: Index, files: list[Path]) -> bool:
    return set(index.files.keys()) == {_rel(p) for p in files}


def build_index(scope: str, force: bool = False) -> Index:
    files = collect_files(scope)
    if not force:
        existing = load(scope)
        if existing and not is_stale(existing, PROJECT_ROOT) and _same_file_set(existing, files):
            return existing

    docs = _docs_from(files)
    file_mtimes = {_rel(p): p.stat().st_mtime for p in files}
    index = build(docs, scope, file_mtimes)
    save(index)
    print(f"[rag] scope={scope} 文件={len(files)} 块={len(docs)} -> {index_path(scope)}")
    return index


def build_all(force: bool = False) -> dict[str, Index]:
    return {scope: build_index(scope, force=force) for scope in ("knowledge", "manuscript")}
