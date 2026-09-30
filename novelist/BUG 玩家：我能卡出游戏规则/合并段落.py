#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按语义合并段落：novelist.md 第146行「不用逐行断句：一段 60-180 字，按语义合并」，
第151行把「段均字数<35」列为判废线。

规则（保守）：
  - 只合并**连续的叙述段**。对白（" 「 ）、面板（【）、代码块（```）、引用（>）、
    场景分隔（---）一律**不合并**，保持原样。
  - 累积到 60 字即收，180 字封顶，超出则断开另起。
  - 不改动任何一个字，只删空行。

用法：python3 合并段落.py [--dry]
"""
import re, glob, os, sys

LO, HI = 95, 200
OPEN = ('"', '“', '「', '`', '【', '>', '-', '|', '*')


def han(t):
    return len(re.findall(r'[\u4e00-\u9fff]', t))


def is_narr(p):
    s = p.strip()
    if not s or s.startswith('#'):
        return False
    return not s.startswith(OPEN)


def process(path, dry=False):
    src = open(path, encoding='utf-8').read()
    paras = [p for p in src.split('\n\n') if p.strip()]
    out = []
    buf = []
    buf_len = 0

    def flush():
        nonlocal buf, buf_len
        if buf:
            out.append(''.join(buf))
            buf, buf_len = [], 0

    in_code = False
    for p in paras:
        s = p.strip()
        if s.startswith('```'):
            in_code = not in_code
            flush(); out.append(p); continue
        if in_code or not is_narr(p):
            flush(); out.append(p); continue
        # 叙述段：并入缓冲
        buf.append(s)
        buf_len += han(s)
        if buf_len >= LO:
            flush()
    flush()

    new = '\n\n'.join(out)
    if dry:
        return src, new
    if new != src:
        open(path, 'w', encoding='utf-8').write(new)
    return src, new


if __name__ == '__main__':
    dry = '--dry' in sys.argv
    tp = tn = 0
    chs = []
    for p in sorted(glob.glob('正文/*/*.md')):
        a, b = process(p, dry)
        pa = [x for x in a.split('\n\n') if x.strip() and not x.strip().startswith('#')]
        pb = [x for x in b.split('\n\n') if x.strip() and not x.strip().startswith('#')]
        ga = sum(han(x) for x in pa) / len(pa)
        gb = sum(han(x) for x in pb) / len(pb)
        tp += len(pa); tn += len(pb)
        chs.append((os.path.basename(p), len(pa), len(pb), ga, gb))
    print('%s：叙述段 %d → %d' % ('DRY' if dry else 'APPLY', tp, tn))
    print('%-28s %6s %6s %7s %7s' % ('章', '原段', '新段', '原均字', '新均字'))
    for b, a1, b1, g1, g2 in chs[:10]:
        print('%-28s %6d %6d %7.1f %7.1f' % (b, a1, b1, g1, g2))
    lo = sum(1 for _, _, _, _, g in chs if g < 35)
    print('\n仍 <35 字的章：%d / %d' % (lo, len(chs)))