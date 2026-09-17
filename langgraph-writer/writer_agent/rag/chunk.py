"""Markdown 感知切块：保留标题层级、按段落聚合、超长段落开窗并留 overlap。

切块质量直接决定召回质量：块太大 → 噪声多、浪费 token；太小 → 语义不完整。
默认 max_chars=800 / overlap=120，对中文小说设定与写作规范都较合适。
"""

from __future__ import annotations

import re
from typing import Iterator

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def _iter_blocks(text: str) -> Iterator[dict]:
    """把正文切成「段落块」，每块带标题路径与起始行号。"""
    heading_stack: list[tuple[int, str]] = []
    buf: list[str] = []
    start = 1

    def heading_path() -> str:
        return " / ".join(title for _, title in heading_stack)

    def flush(end_line: int):
        nonlocal buf
        body = "\n".join(buf).strip()
        if body:
            yield {"text": body, "heading": heading_path(), "start": start, "end": end_line}
        buf = []

    for i, line in enumerate(text.splitlines(), 1):
        m = _HEADING.match(line)
        if m:
            yield from flush(i - 1)
            level = len(m.group(1))
            heading_stack = [(lv, t) for lv, t in heading_stack if lv < level]
            heading_stack.append((level, m.group(2).strip()))
            continue
        if line.strip() == "":
            yield from flush(i - 1)
            continue
        if not buf:
            start = i
        buf.append(line)
    yield from flush(len(text.splitlines()))


def _window(text: str, max_chars: int, overlap: int) -> list[str]:
    """超长文本按 max_chars 开窗，窗口间保留 overlap 字符。"""
    if len(text) <= max_chars:
        return [text]
    out: list[str] = []
    step = max(1, max_chars - overlap)
    for i in range(0, len(text), step):
        piece = text[i:i + max_chars]
        if piece.strip():
            out.append(piece)
        if i + max_chars >= len(text):
            break
    return out


def chunk_markdown(text: str, max_chars: int = 800, overlap: int = 120) -> list[dict]:
    """返回 chunk 列表，每项含 text / heading / start / end。"""
    chunks: list[dict] = []
    pending: list[dict] = []
    pending_len = 0

    def flush_pending():
        nonlocal pending, pending_len
        if not pending:
            return
        body = "\n\n".join(b["text"] for b in pending)
        heading = pending[0]["heading"]
        chunks.append({
            "text": body,
            "heading": heading,
            "start": pending[0]["start"],
            "end": pending[-1]["end"],
        })
        pending = []
        pending_len = 0

    for block in _iter_blocks(text):
        pieces = _window(block["text"], max_chars, overlap)
        for piece in pieces:
            if pending and (pending_len + len(piece) > max_chars or block["heading"] != pending[0]["heading"]):
                flush_pending()
            pending.append({
                "text": piece,
                "heading": block["heading"],
                "start": block["start"],
                "end": block["end"],
            })
            pending_len += len(piece) + 2
    flush_pending()
    return chunks
