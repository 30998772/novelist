#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连续性审计：年龄链 / 身份撞车 / 编号 / 标题行 / 基准冲突

用法:
    python3 audit.py                  # 全书审计
    python3 audit.py 正文/第一部       # 只扫一部
    python3 audit.py --ages           # 只看年龄链
    python3 audit.py --nums           # 只看编号与标题行

⚠️ 方法缺陷（必读）：
  1. 本脚本**不做**"某章说某人多少岁"的归属判定。年龄只输出"所在句"，
     归属由人判断。早期版本用 ±70 字上下文窗口自动归属，
     结果把别人的年龄算给主角（第三部 063「八十二岁」被记到陆栖头上）。
  2. 汉字数字必须支持：中文稿很少写「54岁」，多写「五十四岁」。
  3. 只报不改。年龄断裂牵扯剧情，改一个数字可能推翻一整段因果。
"""
import re
import sys
import glob
import os
import collections

CN = {'零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
      '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}

NAMES = ['陆栖', '林越', '苏晚', '周明远', '周荞', '顾松年', '顾念',
         '阿棠', '沈明棠', '方知远', '方小远', '林晓颂', '陈国华',
         '陈小满', '周秀兰', '苏晓棠', '周维德', '陈立夏', '苏晚晴']

AGES = r'([0-9]{2}|[一二三四五六七八九十]{2,3})\s*岁'


def cn2int(s):
    if s.isdigit():
        return int(s)
    if '十' in s:
        a, _, b = s.partition('十')
        return CN.get(a, 1) * 10 + (CN.get(b, 0) if b else 0)
    v = 0
    for ch in s:
        v = v * 10 + CN.get(ch, 0)
    return v


def sentence_of(t, i, j):
    """取 i..j 所在的完整句子。"""
    s = t.rfind('\n', 0, i) + 1
    e = t.find('\n', j)
    return t[s:e if e > 0 else j + 30].strip()


# ---------------------------------------------------------------- 年龄链
def audit_ages(paths):
    rows = []
    for f in paths:
        t = open(f, encoding='utf-8').read()
        for m in re.finditer(AGES, t):
            v = cn2int(m.group(1))
            if not v or v < 10:
                continue
            sent = sentence_of(t, m.start(), m.end())
            hit = [n for n in NAMES if n in sent]
            if hit:
                rows.append((f, v, '|'.join(hit), sent[:90]))
    if not rows:
        print('[年龄] 无')
        return
    print(f'[年龄] {len(rows)} 处（归属需人工确认，脚本不判定）\n')
    for part in sorted({r[0].split('/')[-2] for r in rows}):
        pr = [r for r in rows if r[0].split('/')[-2] == part]
        print(f'── {part} ──')
        for f, v, who, sent in pr:
            print(f'  {v:>3}  {who:<8} {os.path.basename(f)[:22]:<24} {sent}')
        print()


# ---------------------------------------------------------------- 身份
def audit_identity(paths):
    """同名撞车：一个人名在不同部承担互斥身份。"""
    print('[身份] 各人名出现的分部：')
    byname = collections.defaultdict(lambda: collections.defaultdict(set))
    for f in paths:
        t = open(f, encoding='utf-8').read()
        part = f.split('/')[-2]
        for n in NAMES:
            if n in t:
                byname[n][part].add(f)
    for n in sorted(byname):
        parts = sorted(byname[n])
        mark = '  ⚠ 跨部' if len(parts) > 1 else ''
        print(f'  {n:<8} {len(parts)} 部  {",".join(parts)}{mark}')

    # 同一部里同时出现 周明远 与 周荞 → 拆分后应完全分离
    for part in sorted({f.split('/')[-2] for f in paths}):
        ps = [f for f in paths if f.split('/')[-2] == part]
        a = sum(1 for f in ps if '周明远' in open(f, encoding='utf-8').read())
        b = sum(1 for f in ps if '周荞' in open(f, encoding='utf-8').read())
        if a and b:
            print(f'  🔴 {part}: 周明远({a}章) 与 周荞({b}章) 同部并存 —— 姓名撞车未拆干净')
    print()


# ---------------------------------------------------------------- 编号
def audit_nums(paths):
    print('[编号]')
    for part in sorted({f.split('/')[-2] for f in paths}):
        ps = sorted(f for f in paths if f.split('/')[-2] == part)
        ns, bad_hdr = [], []
        for f in ps:
            m = re.search(r'第(\d+)章', f)
            ns.append(int(m.group(1)) if m else 0)
            t = open(f, encoding='utf-8').read()
            h = re.match(r'\s*#\s*第(\d+)章\s*(.+)', t)
            if not h:
                bad_hdr.append((os.path.basename(f), '缺标题行'))
            elif int(h.group(1)) != int(m.group(1)):
                bad_hdr.append((os.path.basename(f), f'标题行{h.group(1)}≠文件{m.group(1)}'))
        cont = sorted(ns) == list(range(1, len(ns) + 1))
        dup = [x for x in set(ns) if ns.count(x) > 1]
        print(f'  {part:<5} {len(ps)} 章  编号{"连续" if cont else "断裂"}'
              f'{"  重号" + str(dup) if dup else ""}')
        for b in bad_hdr:
            print(f'        🔴 {b[0]}: {b[1]}')
    print()


# ---------------------------------------------------------------- 基准
def audit_baseline(root):
    f = os.path.join(root, '章节大纲', '年龄基准表.md')
    if not os.path.exists(f):
        print('[基准] 未找到 章节大纲/年龄基准表.md')
        return
    t = open(f, encoding='utf-8').read()
    for key, expect in [('陆栖', 54), ('林越', 56), ('苏晚', 34), ('周明远', 67)]:
        print(f'  {key}: 基准表 {"有" if key in t else "无"}  期望年龄 {expect}')
    q = re.findall(r'```\s*待办[^`]*```', t)
    if '待定项' in t or '待核' in t:
        print('  ⚠ 基准表仍有「待定项」或「待核」，先裁定再写作')
    print()


# ---------------------------------------------------------------- CLI
def main():
    a = sys.argv[1:]
    only = [k for k in ('--ages', '--nums', '--identity', '--baseline') if k in a]
    a = [x for x in a if not x.startswith('--')]

    root = '.'
    paths = []
    for p in a:
        if os.path.isdir(p):
            paths += sorted(glob.glob(os.path.join(p, '**', '*.md'), recursive=True))
        elif os.path.isfile(p):
            paths.append(p)
        else:
            paths += sorted(glob.glob(os.path.join(p, '**', '*.md'), recursive=True))
    if not paths:
        paths = sorted(glob.glob('正文/*/*.md'))
        root = os.getcwd()

    print('=' * 66)
    print(f'连续性审计：{len(paths)} 章')
    print('=' * 66 + '\n')

    if not only or '--ages' in only:
        audit_ages(paths)
    if not only or '--identity' in only:
        audit_identity(paths)
    if not only or '--nums' in only:
        audit_nums(paths)
    if not only or '--baseline' in only:
        audit_baseline(root)


if __name__ == '__main__':
    main()
