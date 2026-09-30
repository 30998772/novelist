#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, glob, json
from collections import Counter, defaultdict

ROOT = "/mnt/d/devProject/writer/novelist/旧书栖灵"
PARTS = ["第一部","第二部","第三部","第四部","第五部","第六部"]
TXT = os.path.join(ROOT, "正文")
CARD = os.path.join(ROOT, "章节大纲")

def cn(t):
    return len(re.findall(r'[\u4e00-\u9fff]', t))

# ---------- 正文文件清单 ----------
text_files = {}   # part -> {num: (filename, title, text)}
for p in PARTS:
    d = os.path.join(TXT, p)
    m = {}
    for f in sorted(os.listdir(d)):
        mm = re.match(r'第(\d+)章-(.+)\.md$', f)
        if not mm: 
            print("!! 异常文件名", p, f); continue
        num = int(mm.group(1)); title = mm.group(2)
        txt = open(os.path.join(d,f), encoding='utf-8').read()
        m[num] = (f, title, txt)
    text_files[p] = m

print("="*70)
print("【B】正文文件清单")
for p in PARTS:
    ns = sorted(text_files[p])
    print(f"{p}: {len(ns)}章  编号范围 {min(ns)}-{max(ns)}  连续={ns==list(range(1,len(ns)+1))}")

# ---------- 卡片解析 ----------
def parse_cards(part):
    path = os.path.join(CARD, part, "逐章卡片.md")
    txt = open(path, encoding='utf-8').read()
    lines = txt.split("\n")
    cards = {}   # num -> dict
    cur = None
    for i,l in enumerate(lines):
        m = re.match(r'^###\s*第(\d+)章\s*(.*)$', l)
        if m:
            cur = int(m.group(1))
            cards[cur] = {"title": m.group(2).strip(), "fields": {}, "line": i+1}
            continue
        if cur is not None:
            m2 = re.match(r'^-\s*\*\*(.+?)\*\*\s*[:：]?\s*(.*)$', l)
            if m2:
                cards[cur]["fields"][m2.group(1)] = m2.group(2)
            elif l.startswith('## ') or l.startswith('---'):
                cur = None
    return cards, txt

cards = {}
cardtexts = {}
for p in PARTS:
    cards[p], cardtexts[p] = parse_cards(p)

print("="*70)
print("【B】逐章卡片 vs 正文 对应一致性")
allstat = {}
for p in PARTS:
    c = cards[p]; t = text_files[p]
    ck, tk = set(c), set(t)
    only_card = sorted(ck-tk); only_text = sorted(tk-ck)
    mism = []
    for n in sorted(ck & tk):
        ct = c[n]["title"].strip(); tt = t[n][1].strip()
        if ct != tt: mism.append((n, ct, tt))
    allstat[p] = (len(ck), len(tk), only_card, only_text, mism)
    print(f"\n{p}: 卡片{len(ck)}个 / 正文{len(tk)}个")
    print(f"  卡片有正文缺: {only_card if only_card else '无'}")
    print(f"  正文有卡片缺: {only_text if only_text else '无'}")
    print(f"  标题不一致 {len(mism)} 个:")
    for n,a,b in mism: print(f"    ch{n:03d} 卡片《{a}》 vs 正文《{b}》")

# ---------- 卡片字段一致性 ----------
print("="*70)
print("【卡片字段一致度】")
FIELDS = ["场景","本章目标","事件","伏笔","钩子"]
for p in PARTS:
    cnt = Counter()
    miss = defaultdict(list)
    for n,c in cards[p].items():
        for f in FIELDS:
            if f in c["fields"]: cnt[f]+=1
            else: miss[f].append(n)
    tot = len(cards[p])
    print(f"\n{p} (共{tot}章): " + "  ".join(f"{f}={cnt[f]}/{tot}" for f in FIELDS))
    for f in FIELDS:
        if miss[f]:
            print(f"   缺「{f}」章: {miss[f]}")
    # 额外字段
    extra = Counter()
    for n,c in cards[p].items():
        for f in c["fields"]:
            if f not in FIELDS: extra[f]+=1
    if extra: print("   额外字段:", dict(extra))

# ---------- 占位/TODO ----------
print("="*70)
print("【占位/待补/TODO 扫描】(全库 md)")
for f in glob.glob(os.path.join(ROOT,"**","*.md"), recursive=True):
    t = open(f, encoding='utf-8', errors='ignore').read()
    hits = []
    for kw in ["TODO","待补","待写","占位","TBD","xxx","XXX","待定","略","（略）","待补齐","未完待续"]:
        n = t.count(kw)
        if n: hits.append(f"{kw}×{n}")
    if hits:
        print(f"  {f.replace(ROOT+'/','')}: {', '.join(hits)}")

# ---------- E 字数 ----------
print("="*70)
print("【E】字数达成 (>=3500中文字)")
grand_total = 0; grand_fail = 0
for p in PARTS:
    counts = {n: cn(t[2]) for n,t in text_files[p].items()}
    vals = list(counts.values())
    tot = sum(vals); grand_total += tot
    fail = [ (n,v) for n,v in sorted(counts.items()) if v < 3500 ]
    grand_fail += len(fail)
    below3200 = [(n,v) for n,v in sorted(counts.items()) if v < 3200]
    print(f"\n{p}: n={len(vals)} 合计={tot} ({tot/10000:.2f}万) 均章={tot/len(vals):.0f} 中位={sorted(vals)[len(vals)//2]}")
    print(f"  最小={min(vals)}(ch{[k for k,v in counts.items() if v==min(vals)][0]})  最大={max(vals)}(ch{[k for k,v in counts.items() if v==max(vals)][0]})")
    print(f"  <3500字章数: {len(fail)}/{len(vals)} = {len(fail)/len(vals)*100:.1f}%   <3200字: {len(below3200)}")
    print(f"  不达标清单(ch:字): {[(f'ch{n:03d}',v) for n,v in fail]}")
print(f"\n全书: 合计={grand_total} ({grand_total/10000:.2f}万字) 均章={grand_total/410:.0f}  <3500章占比={grand_fail/410*100:.1f}%")

json.dump({p:{str(n):cn(t[2]) for n,t in text_files[p].items()} for p in PARTS},
          open("/tmp/opencode/wordcounts.json","w"), ensure_ascii=False)
