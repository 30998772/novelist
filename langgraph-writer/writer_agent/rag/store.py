"""向量索引：构建、持久化、混合召回（dense 余弦 + sparse BM25）。

持久化到 langgraph-writer/.rag/index_<scope>.json，随文件 mtime 判断是否需要重建。
召回用 alpha 加权融合：score = alpha * dense + (1 - alpha) * sparse，各自归一化到 [0,1]。
"""

from __future__ import annotations

import base64
import json
import math
import struct
import time
from pathlib import Path

from .bm25 import BM25
from .embedder import HashEmbedder, get_embedder
from .tokenize import tokenize

_RAG_DIR = Path(__file__).resolve().parents[2] / ".rag"
_SCHEMA_VERSION = 1


def default_rag_dir() -> Path:
    return _RAG_DIR


def index_path(scope: str) -> Path:
    return _RAG_DIR / f"index_{scope}.json"


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _encode_vec(vec: list[float]) -> str:
    """归一化向量 [-1,1] -> int16 -> base64，落盘体积约为 JSON 浮点的 1/5。"""
    ints = [int(max(-1.0, min(1.0, v)) * 10000) for v in vec]
    return base64.b64encode(struct.pack(f"<{len(ints)}h", *ints)).decode("ascii")


def _decode_vec(s: str) -> list[float]:
    raw = base64.b64decode(s)
    count = len(raw) // 2
    return [v / 10000.0 for v in struct.unpack(f"<{count}h", raw)]


def _minmax(scores: list[float]) -> list[float]:
    if not scores:
        return scores
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-12:
        return [0.0] * len(scores)
    return [(s - lo) / (hi - lo) for s in scores]


class Index:
    """一个 scope（knowledge / manuscript）的索引。"""

    def __init__(self, scope: str, embedder_name: str, chunks: list[dict], files: dict[str, float]):
        self.scope = scope
        self.embedder_name = embedder_name
        self.chunks = chunks
        self.files = files
        self._bm25: BM25 | None = None

    def _ensure_bm25(self) -> BM25:
        if self._bm25 is None:
            self._bm25 = BM25([tokenize(c["text"]) for c in self.chunks])
        return self._bm25

    def search(self, query: str, k: int = 5, alpha: float = 0.5,
               source_filter: str = "") -> list[dict]:
        if not self.chunks:
            return []
        embedder = get_embedder()
        q_tokens = tokenize(query)

        dense = [_cosine(_normalize(embedder.embed_query(query)), c["vec"]) for c in self.chunks]
        sparse = self._ensure_bm25().scores(q_tokens) if q_tokens else [0.0] * len(self.chunks)
        dn, sn = _minmax(dense), _minmax(sparse)

        scored = []
        for i, c in enumerate(self.chunks):
            if source_filter and source_filter not in c["source"]:
                continue
            scored.append((alpha * dn[i] + (1 - alpha) * sn[i], c))
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, c in scored[:k]:
            results.append({
                "score": round(score, 4),
                "source": c["source"],
                "heading": c.get("heading", ""),
                "start": c.get("start"),
                "end": c.get("end"),
                "text": c["text"],
            })
        return results

    def to_dict(self) -> dict:
        chunks = [
            {**{k: v for k, v in c.items() if k != "vec"}, "vec": _encode_vec(c["vec"])}
            for c in self.chunks
        ]
        return {
            "version": _SCHEMA_VERSION,
            "scope": self.scope,
            "embedder": self.embedder_name,
            "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files": self.files,
            "chunks": chunks,
        }


def build(docs: list[dict], scope: str, files: dict[str, float],
          embedder: HashEmbedder | None = None) -> Index:
    emb = embedder or get_embedder()
    texts = [d["text"] for d in docs]
    vecs = emb.embed(texts) if texts else []
    chunks = []
    for d, v in zip(docs, vecs):
        chunks.append({
            "source": d["source"],
            "heading": d.get("heading", ""),
            "start": d.get("start"),
            "end": d.get("end"),
            "text": d["text"],
            "vec": _normalize(v),
        })
    return Index(scope=scope, embedder_name=emb.name, chunks=chunks, files=files)


def save(index: Index) -> Path:
    _RAG_DIR.mkdir(parents=True, exist_ok=True)
    path = index_path(index.scope)
    path.write_text(json.dumps(index.to_dict(), ensure_ascii=False), encoding="utf-8")
    return path


def load(scope: str, embedder_name: str | None = None) -> Index | None:
    path = index_path(scope)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    if data.get("version") != _SCHEMA_VERSION:
        return None
    if embedder_name and data.get("embedder") != embedder_name:
        return None
    chunks = [{**c, "vec": _decode_vec(c["vec"])} for c in data["chunks"]]
    return Index(
        scope=data["scope"],
        embedder_name=data["embedder"],
        chunks=chunks,
        files=data.get("files", {}),
    )


def is_stale(index: Index, base: Path) -> bool:
    """索引记录的 mtime 与磁盘不一致（文件修改/删除）则为过期。

    files 用相对 base 的路径存储，因此索引可跨平台（WSL / Windows）复用。
    """
    if not index.files:
        return True
    for rel, mtime in index.files.items():
        p = base / rel
        if not p.exists() or abs(p.stat().st_mtime - mtime) >= 1.0:
            return True
    return False
