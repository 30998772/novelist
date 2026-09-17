"""纯 Python BM25（Okapi）：稀疏词频召回，对中文单字+二元组效果稳定。"""

from __future__ import annotations

import math
from collections import Counter


class BM25:
    def __init__(self, docs_tokens: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.N = len(docs_tokens)
        self.tf = [Counter(d) for d in docs_tokens]
        self.dl = [len(d) for d in docs_tokens]
        self.avgdl = (sum(self.dl) / self.N) if self.N else 0.0

        df: dict[str, int] = {}
        for d in docs_tokens:
            for tok in set(d):
                df[tok] = df.get(tok, 0) + 1
        self.idf = {
            tok: math.log(1 + (self.N - n + 0.5) / (n + 0.5))
            for tok, n in df.items()
        }

    def scores(self, query_tokens: list[str]) -> list[float]:
        out = [0.0] * self.N
        if not self.N or not query_tokens:
            return out
        for tok in query_tokens:
            idf = self.idf.get(tok)
            if idf is None:
                continue
            for i in range(self.N):
                f = self.tf[i].get(tok, 0)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * self.dl[i] / (self.avgdl or 1.0))
                out[i] += idf * f * (self.k1 + 1) / denom
        return out
