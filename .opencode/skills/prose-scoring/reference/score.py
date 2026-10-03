#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
18 维评分的数据准备与合成

用法:
    python3 score.py 正文/第一部              # 逐章客观数据
    python3 score.py 正文/第一部 --synth      # 附合成表（需先填主观分）

三套体系（权重固定，不要改）:
    章总分 = prose_8维 × 0.5 + craft_6维 × 0.2 + outline_逐章8维 × 0.3

⚠️ 本脚本只做两件事：
   1. 客观数据（字数/段长/破折号/复读/焊接/手感词/意象）
   2. 把三套分数合成
   **它不打分。** 维度 2-7 必须通读后由人给依据，无出处的分不接受。
"""
import re
import sys
import glob
import os
import collections

QUOTES = ('"', '「', '」', '『', '』')
TOUCH = r'厚|薄|软|硬|涩|黏|糙|滑|毛|渣|屑|钝|粗|细|密|稀|脆|实|凸|凹|烫|凉|温'
HAND = r'摸|按|压|贴|碰|抓|捏|捧|托|抠|划|擦|戳|握|搁|攥|搓|蹭|甩|插|抽|挑|抖|拍|推|拉'
# 意象链：本书的复现意象。密度低于 2 判意象系统空缺。
# 本书复现意象链。六部正文各有侧重，但全书共同的母题是
# 灰 / 霜 / 墨 / 屑 / 霉 加上本书自有的 纸 / 印 / 瓦 / 绳 / 门框。
# 只统计前五个会漏掉本书最核心的四个母题，导致意象列大面积空缺。
IMAGERY = ['灰', '霜', '墨', '屑', '霉', '纸', '印', '瓦', '绳', '门框']

# 字数区间。以项目 SKILL.md 为唯一口径（2026-10-03 定），
# 旧默认 3600-4000 与本书 3200-3800 冲突，会让门禁每次结论不同。
LO, HI = 3200, 3800




def strip_comments(t):
    """剥离 HTML 注释块（修订记录、审计批注）。

    章末的 <!-- 修订 --> 块不计入字数/句法，否则一次修订就把字数撑出上限，
    门禁每次结论都不同。
    """
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def data(path):
    t = strip_comments(open(path, encoding='utf-8').read())
    L = [x.strip() for x in t.split('\n') if x.strip() and not x.startswith('#')]

    sents = [x.strip() for x in re.split(r'[。\n]', t)
             if x.strip() and x.strip() not in QUOTES]
    c = collections.Counter(sents)
    dup = max([v for k, v in c.items() if v > 1] or [1])

    longl = [x for x in L if len(x) >= 30]
    blk = ['␟'.join(longl[i:i + 3]) for i in range(len(longl) - 2)]
    weld = sum(1 for k, v in collections.Counter(blk).items() if v > 1)

    # 段均按「段」（\n\n）算，不是按行。多轮对白并进同一段落后，
    # 按行算会把并段后的对白章误判为段均过短。
    _ps = [x for x in t.split('\n\n') if x.strip() and not x.strip().startswith('#')]
    narr = [len(re.sub(r'\s', '', x)) for x in _ps]
    sl = [len(re.sub(r'\s', '', x)) for x in re.split(r'(?<=[。！？])', t) if x.strip()]

    return dict(
        chars=len(re.sub(r'\s', '', t)),
        seg=sum(narr) // max(len(narr), 1),
        dash=t.count('——'),
        uniq=round(len(c) / max(len(sents), 1), 2),
        dup=dup,
        weld=weld,
        med=sorted(sl)[len(sl) // 2] if sl else 0,
        long=sum(1 for x in sl if x >= 45),
        touch=len(re.findall(TOUCH, t)),
        hand=len(re.findall(HAND, t)),
        imagery={w: t.count(w) for w in IMAGERY if t.count(w)},
        quotes=len(re.findall(r'"[^"]{2,}"', t)),
        dlg_line=sum(1 for x in L if x.startswith('"') and x.count('"') >= 2),
    )


def synth(prose, craft, outline):
    """prose/craft/outline 各为 0-100 的整数。"""
    return round(prose * 0.5 + craft * 0.2 + outline * 0.3, 1)


def grade(s):
    if s >= 90: return 'S 可直接投稿'
    if s >= 80: return 'A 小修后投稿'
    if s >= 70: return 'B 需针对性优化'
    if s >= 60: return 'C 需较大改动'
    return 'D 建议重构'


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    paths = []
    for p in a:
        if os.path.isdir(p):
            paths += sorted(x for x in glob.glob(os.path.join(p, '*.md'))
                       if not os.path.basename(x).startswith('_')
                       )
        else:
            paths += sorted(glob.glob(p))
    if not paths:
        paths = sorted(x for x in glob.glob('正文/第一部/*.md')
                        if not os.path.basename(x).startswith('_'))

    W = [5, 6, 5, 5, 6, 5, 7, 5, 5, 5, 5, 11, 24]
    hdr = ('章', '字数', '段均', '破折', '句中位', '长句', '唯一句', '复读',
           '焊接', '质感', '手法', '引语/独行', '意象')
    print(''.join(h.rjust(w) for h, w in zip(hdr, W)))
    rows = []
    for p in paths:
        v = data(p)
        name = re.search(r'第(\d+)章', p)
        num = name.group(1) if name else '?'
        im = ' '.join(f'{k}{n}' for k, n in v['imagery'].items()) or '—'
        print(''.join(str(x).rjust(w) for x, w in zip(
            [num, v['chars'], v['seg'], v['dash'], v['med'], v['long'],
             v['uniq'], v['dup'], v['weld'], v['touch'], v['hand'],
             f"{v['quotes']}/{v['dlg_line']}", im], W)))
        rows.append((num, v))

    print('\n注：引语格式「总数/独占行」。独占行≈对白，段中引语多时对白被低估。')
    print('    对白占比必须人工判，脚本不可用。')

    hard = [(n, v) for n, v in rows
            if not (LO <= v['chars'] <= HI) or v['seg'] < 35
            or v['dash'] > 8 or v['weld'] or v['uniq'] < 0.55]
    print(f'\n硬指标 FAIL：{len(hard)}/{len(rows)} 章')
    for n, v in hard:
        why = []
        if not (LO <= v['chars'] <= HI): why.append(f"字数{v['chars']}")
        if v['seg'] < 35: why.append(f"段均{v['seg']}")
        if v['dash'] > 8: why.append(f"破折{v['dash']}")
        if v['weld']: why.append(f"焊接×{v['weld']}")
        if v['uniq'] < 0.55: why.append(f"唯一句{v['uniq']}")
        print(f'  {n}  ' + ' '.join(why))

    print('\n合成示例：synth(88, 96, 89) =', synth(88, 96, 89), grade(synth(88, 96, 89)))


if __name__ == '__main__':
    main()
