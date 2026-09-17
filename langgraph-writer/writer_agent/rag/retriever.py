"""召回入口：retrieve()（结构化）/ retrieve_text()（拼成可注入 prompt 的文本）。

首次调用或索引过期时自动重建，调用方无感。
"""

from __future__ import annotations

import os

from .embedder import get_embedder
from .ingest import PROJECT_ROOT, build_index, collect_files
from .store import Index, is_stale, load

VALID_SCOPES = ("knowledge", "manuscript")

# 进程内缓存：避免每次查询都重新解析几十 MB 的索引 JSON
_CACHE: dict[str, Index] = {}


def _same_file_set(index: Index, scope: str) -> bool:
    try:
        current = {p.relative_to(PROJECT_ROOT).as_posix() for p in collect_files(scope)}
        return set(index.files.keys()) == current
    except Exception:  # noqa: BLE001
        return True


def get_index(scope: str, auto_build: bool = True) -> Index | None:
    if scope not in VALID_SCOPES:
        raise ValueError(f"未知 scope: {scope!r}（可选 {VALID_SCOPES}）")
    embedder = get_embedder()

    index = _CACHE.get(scope)
    if index is not None and index.embedder_name == embedder.name \
            and not is_stale(index, PROJECT_ROOT) and _same_file_set(index, scope):
        return index

    index = load(scope, embedder_name=embedder.name)
    needs_build = index is None or is_stale(index, PROJECT_ROOT) or not _same_file_set(index, scope)
    if needs_build and auto_build:
        index = build_index(scope, force=True)
    if index is not None:
        _CACHE[scope] = index
    return index


def retrieve(query: str, k: int = 0, scope: str = "knowledge",
             alpha: float = -1.0, source_filter: str = "",
             auto_build: bool = True) -> list[dict]:
    """返回 top-k 召回片段（含 score / source / heading / text）。"""
    k = k or int(os.environ.get("WRITER_RAG_K", "5"))
    alpha = float(os.environ.get("WRITER_RAG_ALPHA", "0.5")) if alpha < 0 else alpha
    index = get_index(scope, auto_build=auto_build)
    if index is None:
        return []
    return index.search(query, k=k, alpha=alpha, source_filter=source_filter)


def retrieve_text(query: str, k: int = 0, scope: str = "knowledge",
                  alpha: float = -1.0, source_filter: str = "") -> str:
    """把召回片段拼成可直接注入 prompt 的文本。"""
    hits = retrieve(query, k=k, scope=scope, alpha=alpha, source_filter=source_filter)
    if not hits:
        return ""
    blocks = []
    for h in hits:
        loc = f"{h['source']}:{h.get('start')}-{h.get('end')}"
        blocks.append(f"### 召回片段（score={h['score']}，{loc}）\n{h['text']}")
    return "\n\n".join(blocks)
