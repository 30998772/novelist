"""向量化后端：默认离线哈希向量，配置后可切换 OpenAI 兼容 embedding。

- HashEmbedder：feature hashing（把 token 稳定哈希到固定维度）+ L2 归一化，
  完全离线、确定性、无需 API key；配合 BM25 已能支撑中文召回。
- OpenAIEmbedder：设置 LLM_EMBEDDING_MODEL 后启用，返回真正的语义向量。

两者都实现 embed(texts) -> list[list[float]] 与 embed_query(text) -> list[float]，
可无缝替换（面向接口编程，也是面试可讲的「可插拔 embedding」）。
"""

from __future__ import annotations

import hashlib
import math
import os

from .tokenize import tokenize


class HashEmbedder:
    """确定性哈希向量：token -> 固定维度桶，权重用 1+log(tf)。"""

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.name = f"hash-{dim}"

    @staticmethod
    def _bucket(token: str, dim: int) -> int:
        digest = hashlib.md5(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "little") % dim

    def _one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        counts: dict[str, int] = {}
        for tok in tokenize(text):
            counts[tok] = counts.get(tok, 0) + 1
        for tok, cnt in counts.items():
            vec[self._bucket(tok, self.dim)] += 1.0 + math.log(cnt)
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._one(text)


class OpenAIEmbedder:
    """OpenAI 兼容 embedding（如 text-embedding-3-small / text-embedding-v3 / bge）。"""

    def __init__(self):
        from langchain_openai import OpenAIEmbeddings  # 延迟导入，离线路径不依赖

        model = os.environ["LLM_EMBEDDING_MODEL"]
        base_url = os.environ.get("LLM_EMBEDDING_BASE_URL") or os.environ.get("LLM_BASE_URL")
        api_key = os.environ.get("LLM_EMBEDDING_API_KEY") or os.environ.get("LLM_API_KEY")
        if not api_key:
            raise RuntimeError("设置了 LLM_EMBEDDING_MODEL 但缺少 API key")
        self._client = OpenAIEmbeddings(model=model, base_url=base_url, api_key=api_key)
        self.name = f"openai:{model}"
        self.dim = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._client.embed_query(text)


def get_embedder() -> HashEmbedder | OpenAIEmbedder:
    """按环境变量选择后端；OpenAI embedding 初始化失败则回退哈希向量。"""
    if os.environ.get("LLM_EMBEDDING_MODEL"):
        try:
            return OpenAIEmbedder()
        except Exception as exc:  # noqa: BLE001
            print(f"[rag] embedding 初始化失败，回退 HashEmbedder: {exc}")
    return HashEmbedder()
