#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
human-prose 章节体检器

用法:
    python3 check.py                      # 扫全书
    python3 check.py 正文/第一部           # 扫一个部
    python3 check.py 正文/第一部/第001章-*.md   # 扫指定章
    python3 check.py --fix-dash 正文/第一部    # 把破折号降级为句号/逗号
    python3 check.py --lo 3400 --hi 4200        # 改字数区间

判废线（任一命中即判 FAIL，须重写而非润色）:
    字数越界 / 段均 <35 / 破折号 >8 / 唯一句占比 <0.55
    焊接（三行块重复） / 正文出现 ** / 两套引号混用
"""
import re
import sys
import glob
import os
import collections

# ---------------------------------------------------------------- 配置
QUOTES = ('"', '「', '」', '『', '』')

# 必须与 .opencode/agent/novelist.md 第一优先级第 2 条同表。
# 两处不同步就会漏 —— 实测一次批量清理只清了「仿佛/一丝」这类，
# 漏掉「微微/轻轻」，结果每章还剩 5-7 个。
BAN = ['微微', '轻轻', '缓缓', '某种', '仿佛', '似乎', '宛如', '犹如',
       '一丝', '涌起', '涌上心头', '眼底闪过', '似乎在', '不仅仅',
       '不由', '一闪而过', '一抹', '勾起', '五味杂陈', '眸']

# 手感词：质量指标，不判废。低于 20 基本可判定为「提纲扩写」。
TOUCH = r'厚|薄|软|硬|涩|黏|糙|滑|毛|渣|屑|钝|粗|细|密|稀|脆|实|凸|凹|烫|凉|温'
HAND = r'摸|按|压|贴|碰|抓|捏|捧|托|抠|划|擦|戳|握|搁|攥|搓|蹭|甩|插|抽|挑|抖|拍|推|拉'


# ---------------------------------------------------------------- 工具
def chars(t):
    """字数唯一口径：含标点，不含空白。"""
    return len(re.sub(r'\s', '', t))


def sentences(t):
    """切句。必须排除行尾裸引号，否则整章对白行会被当成重复句。"""
    return [x.strip() for x in re.split(r'[。\n]', t)
            if x.strip() and x.strip() not in QUOTES]


def weld_blocks(t, minlen=30, span=3):
    """
    焊接检测：同一段剧情写了两遍（前半摘要版 + 后半真章）。
    单句复读抓不到它 —— 重复的是连续多行。取任意 span 行做锚点。
    返回 [(次数, 片段)]。
    """
    lines = [x.strip() for x in t.split('\n') if len(x.strip()) >= minlen]
    out = []
    for w in (1, span):
        keys = ['␟'.join(lines[i:i + w]) for i in range(len(lines) - w + 1)]
        for k, v in collections.Counter(keys).items():
            if v > 1:
                out.append((v, k[:60]))
        if out:
            break
    return sorted(set(out), key=lambda x: -x[0])


def fix_dash(t):
    """破折号降级：后接完整句改句号，后接半句改逗号。返回 (新文, 原个数)。"""
    n = t.count('——')
    if not n:
        return t, 0
    t = re.sub(r'——(?=[^。！？\n]{4,}[。！？])', '。', t)
    t = re.sub(r'——(?=[^。！？\n]{4,})', '，', t)
    t = t.replace('——', '，')
    t = re.sub(r'。，|，，|。。|：，|；，|，、', lambda m: m.group(0)[0], t)
    return t, n


def merge_paragraphs(path, lo=60):
    """
    段长合并到 60-180。两个必须避开的坑：
      1. 吞掉节拍  —— 长度 <26 字的独立短句不并
      2. 吞掉转折  —— 合并后须回读，在话题切换处补回空行
    """
    src = open(path, encoding='utf-8').read()
    lines = [x for x in src.split('\n') if x.strip()]
    out, i = [], 0
    while i < len(lines):
        cur, j = lines[i], i + 1
        if not cur.startswith(('#', '"', '>')):
            while (j < len(lines)
                   and not lines[j].startswith(('#', '"', '>'))
                   and len(re.sub(r'\s', '', cur)) < lo
                   and len(re.sub(r'\s', '', lines[j])) >= 26):
                cur, j = cur + lines[j], j + 1
        out.append(cur)
        i = j
    open(path, 'w', encoding='utf-8').write('\n\n'.join(out) + '\n')


# ---------------------------------------------------------------- 主检



def strip_comments(t):
    """剥离 HTML 注释块（修订记录、审计批注），不计入字数/句法。"""
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def check(path, lo=3600, hi=4000, show_pass=True):
    t = strip_comments(open(path, encoding='utf-8').read())
    L = [x.strip() for x in t.split('\n') if x.strip() and not x.startswith('#')]

    n = chars(t)
    dash = t.count('——')

    sents = sentences(t)
    c = collections.Counter(sents)
    dup = [(v, k[:40]) for k, v in c.most_common(8) if v > 1]
    uniq = round(len(c) / max(len(sents), 1), 2)

    weld = weld_blocks(t)

    # 段均按「段」（\n\n 分隔）算，不是按行。
    # 理由：多轮对白并进同一段后每行仍短，但那是正常小说的写法，
    # 按行算会把并段后的对白章误判为「段均过短」。
    seg_raw = [chars(x) for x in t.split('\n\n') if x.strip() and not x.strip().startswith('#')]
    seg = sum(seg_raw) // max(len(seg_raw), 1) if seg_raw else 0

    sl = [chars(x) for x in re.split(r'(?<=[。！？])', t) if x.strip()]
    med = sorted(sl)[len(sl) // 2] if sl else 0
    long_sent = sum(1 for x in sl if x >= 45)

    ban = {w: t.count(w) for w in BAN if w in t}
    bold = '**' in t
    quote_mix = ('「' in t and '"' in t) or ('『' in t and '"' in t)

    touch = len(re.findall(TOUCH, t))
    hand = len(re.findall(HAND, t))
    quotes_all = len(re.findall(r'"[^"]{2,}"', t))
    dlg_line = sum(1 for x in L if x.startswith('"') and x.count('"') >= 2)

    fatal = {
        '字数': not (lo <= n <= hi),
        '段均<35': seg < 35,
        '破折>8': dash > 8,
        '唯一句<.55': uniq < 0.55,
        '焊接': bool(weld),
        '加粗': bold,
        '混引号': quote_mix,
    }
    ok = not any(fatal.values())

    if ok and show_pass:
        print(f'PASS {os.path.basename(path)}')
    else:
        print(f'{"FAIL" if not ok else "WARN"} {os.path.basename(path)}'
              f'  ← ' + ' '.join(k for k, v in fatal.items() if v) if fatal else '')
    print(f'   字数{n}[{lo}-{hi}]  段均{seg}[60-180]  破折{dash}[<=8]  '
          f'句中位{med}  长句{long_sent}  唯一句{uniq}')
    print(f'   手感 质感{touch} 手法{hand}   引语{quotes_all}(独占行{dlg_line})   '
          f'禁用{ban or "无"}')
    if dup:
        print('   ⚠ 复读  ', dup)
    if weld:
        print('   🔴 焊接  ', weld)
    return ok


# ---------------------------------------------------------------- CLI
def main():
    a = sys.argv[1:]
    lo = hi = None
    if '--lo' in a:
        lo = int(a[a.index('--lo') + 1])
        hi = int(a[a.index('--hi') + 1])
        a = [x for x in a if x not in ('--lo', '--hi', str(lo), str(hi))]
    lo = lo if lo is not None else 3600
    hi = hi if hi is not None else 4000

    fix = '--fix-dash' in a
    if fix:
        a = [x for x in a if x != '--fix-dash']

    paths = []
    for p in a:
        if os.path.isdir(p):
            paths += sorted(x for x in glob.glob(os.path.join(p, '*.md'))
                       if not os.path.basename(x).startswith('_')
                       )
        elif os.path.isfile(p):
            paths.append(p)
        else:
            paths += sorted(glob.glob(p))
    if not paths:
        paths = sorted(x for x in glob.glob('正文/*/*.md')
                       if not os.path.basename(x).startswith('_'))

    npass = 0
    for p in paths:
        if fix:
            t, n = fix_dash(open(p, encoding='utf-8').read())
            if n:
                open(p, 'w', encoding='utf-8').write(t)
                print(f'FIX  {os.path.basename(p)}  破折 {n} → 0')
        else:
            npass += check(p, lo, hi, show_pass=len(paths) < 15)

    if not fix:
        print(f'\n{npass}/{len(paths)} PASS')


if __name__ == '__main__':
    main()
