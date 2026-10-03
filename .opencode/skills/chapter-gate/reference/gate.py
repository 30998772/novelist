#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
章节质量门禁 —— 合规轴判定器。

只判合规，不打总分。质量轴（连续性/文风/没劲/声纹/意象）必须通读给依据，
见 chapter-gate/SKILL.md。

用法:
    python3 gate.py --book "novelist/他们说我是来替他挡灾的" --pass 92
    python3 gate.py --file 正文/第一部/第001章-门框.md
    python3 gate.py --book <路径> --strict-imagery --dialog-heavy

字数口径唯一：len(re.sub(r'\\s','',t))，含标点不含空白。
"""
import argparse
import glob
import os
import re
import sys

LO, HI, TARGET = 3200, 3800, 3500
CN = re.compile(r'[\u4e00-\u9fff]')
QUOTE = '"'
# 标点粘连（数词紧跟数词，中间漏标点，例：三月二十四一抽）
#
# ⚠️ 这一项**不做自动检测**，改为人工通读检查项。理由是可复现的：
#   真粘连  三月二十四一抽
#   正常日期 三月十二，四月十一，五月十六
#   AABB叠词 一下一下，一格一格，一日一日
# 三者在正则层面同构，无法零误报地区分。实测旧正则对本部 36 章报出 52 处，
# 全部是正常日期。**一个误报率 100% 的判据等于没有判据，只会被关掉。**
# 故：gate.py 不再检此项；SKILL.md 的质量轴第 5 步列为人工必查项。
GLUE_MANUAL = True
# 通用复现意象；本书特例由 --imagery 追加
IMAGERY_DEFAULT = ['灰', '霜', '墨', '屑', '霉', '纸', '印', '瓦', '绳', '门框']


def cn(s):
    return len(CN.findall(s))


def body_paragraphs(t):
    ps = [p.strip() for p in t.split('\n\n') if p.strip()]
    return ps[1:] if ps and ps[0].startswith('# ') else ps


def quote_char_ratio(t):
    """引号内字数 / 总字数 —— 用于文体分档"""
    q = ''.join(re.findall(r'"([^"]*)"', t))
    return cn(q) / max(1, cn(t))


def sentences(t):
    body = re.sub(r'"[^"]*"', '', t, flags=re.M)
    return [x.strip() for x in re.split(r'[。！？]', body) if x.strip()]


def seg_band(qr):
    if qr >= 0.30:
        return 35, 100, '对白章'
    if qr >= 0.18:
        return 40, 100, '偏对白'
    return 60, 180, '叙述章'


def uniq_ratio(t):
    ss = _sentences(t)
    if not ss:
        return 1.0
    from collections import Counter
    c = Counter(ss)
    return len(c) / len(ss)


def _sentences(t):
    """切句并归一化：只按句末标点切；切后把内部空白全压掉。
    不归一化的话，「"嗯。"」所在的多行对白段会留下 "\n" 残留在片段里，
    同一句话在不同段被切成不同字符串，计数全部失真。"""
    ss = [x.strip() for x in re.split(r'[。！？]', t) if x.strip()]
    out = []
    for x in ss:
        x = re.sub(r'\s+', '', x)
        if x and x not in ('"', '\u201c', '\u201d'):
            out.append(x)
    return out


def max_repeat(t):
    """同一「句」最大重复次数，分两档返回 (短节拍, 完整句)。

    分档理由：本书的签名手法是拿单字应答（"嗯。" / "姑娘。"）作节拍，
    一章 3-4 次是风格，10 次以上是机械。完整句一律 ≤2。
    不分档会把风格判成缺陷；分不档会把缺陷放过去。
    """
    from collections import Counter
    ss = _sentences(t)
    if not ss:
        return 0, 0
    c = Counter(ss)
    short = max([v for k, v in c.items() if cn(k.strip('"')) <= 4] or [0])
    full = max([v for k, v in c.items() if cn(k.strip('"')) > 4] or [0])
    return short, full

def weld_count(t):
    """同构块焊接：重复出现的完整段落。
    「——」是场景分隔符，出现多次合法，必须剔除。"""
    ps = [p for p in body_paragraphs(t) if p.strip() != '——']
    return len(ps) - len(set(ps))


def isomorphic_triple(t):
    """同构三连：连续三个同汉字长度且同结尾的短句（非对白）"""
    c = 0
    for p in body_paragraphs(t):
        if '"' in p:
            continue
        ss = [x for x in re.split(r'[。！？]', p) if x.strip()]
        for i in range(len(ss) - 2):
            a, b, d = ss[i], ss[i + 1], ss[i + 2]
            L = [cn(x) for x in (a, b, d)]
            if max(L) <= 16 and len(set(L)) == 1 and len({x[-2:] for x in (a, b, d)}) == 1:
                c += 1
    return c


def hook_is_material(t):
    """章末钩子必须落物证/动作，不得以最后一句对白收尾"""
    ps = body_paragraphs(t)
    if not ps:
        return False, ''
    last = ps[-1].strip()
    if not last.startswith(QUOTE):
        return True, last
    obj = len(re.findall(
        r'纸|印|瓦|绳|门框|灰|墨|痕|格|数|井|袖口|褥子|手|碗|屑|圈|点|册|布|绳', last))
    return obj >= 2, last


def check(path, imagery, require_hook=True, lo=LO, hi=HI):
    t = open(path, encoding='utf-8').read()
    name = os.path.basename(path)
    chars = len(re.sub(r'\s', '', t))
    ps = body_paragraphs(t)
    L = [len(re.sub(r'\s', '', p)) for p in ps]
    seg = sum(L) // max(1, len(L))
    qr = quote_char_ratio(t)
    s_lo, s_hi, style = seg_band(qr)
    ss = sentences(t)
    longn = sum(1 for s in ss if cn(s) >= 45)
    dash = t.count('——')
    uniq = round(uniq_ratio(t), 3)
    rep_short, rep_full = max_repeat(t)
    weld = weld_count(t)
    tri = isomorphic_triple(t)
    glue = 0  # 见 GLUE_MANUAL：改为人工通读检查
    hook_ok, hook_txt = (True, '') if not require_hook else hook_is_material(t)
    sim = len(re.findall(r'(像|好像|如同|仿佛)', t))
    cnt = {k: t.count(k) for k in imagery if t.count(k)}
    dens = sum(cnt.values()) / max(1, chars) * 1000

    rows = []
    rows.append(('字数', chars, f'{lo}-{hi}', lo <= chars <= hi))
    rows.append(('段均', seg, f'{s_lo}-{s_hi}({style})', s_lo <= seg <= s_hi))
    rows.append(('破折号', dash, '≤8', dash <= 8))
    rows.append(('长句≥45字', longn, '≥2', longn >= 2))
    rows.append(('唯一句占比', uniq, '≥0.85', uniq >= 0.85))
    rows.append(('短节拍重复', rep_short, '≤4', rep_short <= 4))
    rows.append(('完整句重复', rep_full, '≤2', rep_full <= 2))
    rows.append(('焊接', weld, '=0', weld == 0))
    rows.append(('同构三连', tri, '=0', tri == 0))
    rows.append(('标点粘连', glue, '=0', glue == 0))
    scene = sum(1 for p in ps if p.strip() == '——')
    rows.append(('场景分隔符', scene, '≤3', scene <= 3))
    rows.append(('明喻', sim, '≥3', sim >= 3))
    rows.append(('意象母题种类', len(cnt), '≥3', len(cnt) >= 3))
    rows.append(('意象链', f'{dens:.1f}/千字 母题{sum(cnt.values())}次',
                 '密度≥8.0 或 总量≥15', dens >= 8.0 or sum(cnt.values()) >= 15))
    rows.append(('章末钩子', '物证/动作' if hook_ok else f'落在对白: {hook_txt[:24]}',
                 '须落物证', hook_ok))

    fails = [r for r in rows if not r[3]]
    return name, rows, fails, style


def render(results, verbose=False):
    npass = 0
    for name, rows, fails, style in results:
        npass += not fails
        tag = 'PASS' if not fails else 'FAIL'
        print(f'{name:<30} {style:<5} {tag}')
        if fails or verbose:
            for k, v, th, ok in rows:
                if not ok or verbose:
                    print(f'    {"✓" if ok else "✗"} {k:<14}{str(v):<22}阈值 {th}')
    print(f'\n合规轴 {npass}/{len(results)} PASS')
    if npass != len(results):
        print('有 FAIL —— 合规轴一票否决，不得开写下一章')
    return npass == len(results)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', help='书目录（含 正文/）或正文目录')
    ap.add_argument('--file', help='单个正文文件')
    ap.add_argument('--part', default='正文/第一部', help='相对 book 的子目录')
    ap.add_argument('--pass', type=int, default=92, dest='threshold')
    ap.add_argument('--lo', type=int, default=LO)
    ap.add_argument('--hi', type=int, default=HI)
    ap.add_argument('--imagery', default='', help='追加本书母题，逗号分隔')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()

    imagery = list(IMAGERY_DEFAULT)
    for x in a.imagery.split(','):
        if x.strip():
            imagery.append(x.strip())

    files = []
    if a.file:
        files = [a.file]
    else:
        base = os.path.join(a.book, a.part) if a.book else a.book
        files = sorted(glob.glob(os.path.join(base, '第*.md')))
    if not files:
        print('未找到正文文件', file=sys.stderr)
        sys.exit(2)

    results = [check(f, imagery, lo=a.lo, hi=a.hi) for f in files]
    ok = render(results, a.verbose)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
