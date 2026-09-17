"""RAG 检索工具：把「知识库 / 正文」按语义+关键词混合召回，返回最相关片段。

与 ai_trace_check 等「全量注入 reference」的工具不同，这里只按 query 召回 top-k，
用于写稿/审稿前查规则、查设定、找伏笔、检测设定冲突。
"""

from .registry import regist_tool


@regist_tool(
    title="知识库检索(RAG)",
    description="从写作知识库（写作规范、AI痕迹清单、标点规范、平台规则等）中按语义+关键词召回最相关片段。查规则、查参考时使用。",
)
def search_knowledge(query: str, k: int = 5) -> str:
    """RAG search over the writing knowledge base."""
    from ..rag import retrieve_text

    return retrieve_text(query, k=k, scope="knowledge") or "（无召回结果）"


@regist_tool(
    title="正文设定检索(RAG)",
    description="在全部小说的 设定/章节大纲/正文/系列规划 中做 RAG 检索，用于查伏笔、查设定、找跨章节线索、检测设定冲突。",
)
def search_manuscript(query: str, k: int = 5) -> str:
    """RAG search over all novels' settings/outlines/manuscripts."""
    from ..rag import retrieve_text

    return retrieve_text(query, k=k, scope="manuscript") or "（无召回结果）"
