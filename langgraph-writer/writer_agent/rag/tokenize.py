"""中英混排分词：中文按「字 + 二元组」，英文/数字按词。

中文没有空格，直接用空格切词会失效；这里用「单字 + 相邻二元组（bigram）」近似，
既能把「高频词清单」这类词召回，又不用引入 jieba 等分词依赖。
"""

from __future__ import annotations

import re

_ASCII_WORD = re.compile(r"[A-Za-z0-9_]+")
_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    tokens: list[str] = []
    for m in _ASCII_WORD.finditer(text):
        tokens.append(m.group(0).lower())
    for m in _CJK_RUN.finditer(text):
        run = m.group(0)
        tokens.extend(run)  # 单字
        if len(run) > 1:
            tokens.extend(run[i:i + 2] for i in range(len(run) - 1))  # 二元组
    return tokens
