"""轻量 RAG（检索增强生成）子系统：把「知识库 + 正文」切块、向量化、建索引，
生成/审稿时按 query 召回最相关片段，只把 top-k 片段注入 prompt。

设计目标（面试可讲）：
- 零外部依赖可跑通：默认用确定性哈希向量 + BM25 做混合召回（离线、可复现）；
- 可升级为真向量：设置 LLM_EMBEDDING_MODEL 后自动改用 OpenAI 兼容 embedding；
- 两个索引空间（scope）：
    knowledge  = .opencode/skills 下的技能/参考知识库（写作规范、平台规则等）
    manuscript = 各小说的 设定 / 章节大纲 / 正文 / 系列规划（支持跨章节找伏笔、设定冲突）
"""

from .retriever import retrieve, retrieve_text
from .ingest import build_index, build_all

__all__ = ["retrieve", "retrieve_text", "build_index", "build_all"]
