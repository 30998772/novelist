#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, hashlib
from collections import Counter, defaultdict
ROOT="/mnt/d/devProject/writer/novelist/旧书栖灵"
PARTS=["第一部","第二部","第三部","第四部","第五部","第六部"]
TXT=os.path.join(ROOT,"正文")
files=[]
for p in PARTS:
    for f in sorted(os.listdir(os.path.join(TXT,p))):
        files.append((p,f,open(os.path.join(TXT,p,f),encoding='utf-8').read()))

print("="*70); print("【重复段落扫描】完全相同的段落（>=25字）跨文件复用")
para=defaultdict(list)
for p,f,t in files:
    for i,l in enumerate(t.split("\n")):
        s=l.strip()
        if len(s)>=25: para[s].append((p,f[:-3],i+1))
dups={k:v for k,v in para.items() if len(v)>1}
print(f"重复段落（原文逐字相同）: {len(dups)} 条, 涉及 {sum(len(v) for v in dups.values())} 处")
for k,v in sorted(dups.items(), key=lambda x:-len(x[1]))[:60]:
    print(f"\n  ×{len(v)}  「{k[:90]}」")
    for p,f,i in v: print(f"      {p}/{f}:{i}")

print("="*70); print("【重复句扫描】>=12字的重复句子（句级）")
sent=defaultdict(list)
for p,f,t in files:
    for i,l in enumerate(t.split("\n")):
        for s in re.split(r'(?<=[。！？…])', l):
            s=s.strip()
            if len(s)>=12: sent[s].append((p,f[:-3],i+1))
ds={k:v for k,v in sent.items() if len(v)>1}
tot_dup=sum(len(v)-1 for v in ds.values())
print(f"重复句型: {len(ds)} 种, 冗余出现 {tot_dup} 次")
for k,v in sorted(ds.items(), key=lambda x:-len(x[1]))[:45]:
    print(f"  ×{len(v):<3} 「{k[:80]}」  例: {v[0][0]}/ch{v[0][1][:3]}…{v[-1][0]}/ch{v[-1][1][:3]}")

print("="*70); print("【首段/末段 形式统计】全书")
def paras(t):
    return [x.strip() for x in t.split("\n") if x.strip()]
firsts=Counter(); lasts=Counter()
for p,f,t in files:
    ps=paras(t)
    if not ps: continue
    a=ps[0]; b=ps[-1]
    # 分类开篇
    if re.match(r'^#',a): a=ps[1] if len(ps)>1 else a
    if a.startswith("第") and "章" in a[:8] and len(a)<40:
        firsts['标题行']+=1
    elif a[0] in '"“': firsts['对话开篇']+=1
    elif re.search(r'^(那天|那一年|这一年|后来|从前|很多年后|第二天|第三天|第[一二三四五六七八九十]+天|)',a): firsts['时间状语开篇']+=1
    else: firsts['叙述/场景开篇']+=1
    if b.endswith('”') or b.endswith('"'): lasts['对话收束']+=1
    elif re.search(r'[。]$',b) and re.search(r'(风|灯|光|茶|树|晚风|雨|雪)',b): lasts['景物句收束']+=1
    else: lasts['叙述收束']+=1
print(" 开篇形式:", dict(firsts))
print(" 章末形式:", dict(lasts))

print("="*70); print("【逐章卡片 梗概互抄检测】")
CARD=os.path.join(ROOT,"章节大纲")
def parse(part):
    path=os.path.join(CARD,part,"逐章卡片.md")
    lines=open(path,encoding='utf-8').read().split("\n")
    cards={}; cur=None
    for i,l in enumerate(lines):
        m=re.match(r'^###\s*第(\d+)章\s*[:：]?\s*(.*)$',l)
        if m: cur=int(m.group(1)); cards[cur]={"t":m.group(2).strip(),"f":{},"line":i+1}; continue
        if cur is not None:
            m2=re.match(r'^-\s*\*\*(.+?)\*\*\s*[:：]?\s*(.*)$',l)
            if m2: cards[cur]["f"][m2.group(1)]=m2.group(2)
            elif l.startswith('## ') or l.startswith('---'): cur=None
    return cards
allcards={p:parse(p) for p in PARTS}
# 事件字段 4-gram 重复
ev=defaultdict(list)
for p in PARTS:
    for n,c in allcards[p].items():
        s=c["f"].get("事件","")
        for i in range(len(s)-11):
            g=s[i:i+12]
            if re.fullmatch(r'[\u4e00-\u9fff、，]{12}',g): ev[g].append((p,n))
big=[(g,v) for g,v in ev.items() if len(v)>1]
print(f"卡片「事件」字段 12字连续片段跨卡重复: {len(big)} 种")
for g,v in sorted(big,key=lambda x:-len(x[1]))[:25]:
    print(f"  ×{len(v)}  「{g}」  {v[:6]}")
# 完全相同的事件文本
evx=defaultdict(list)
for p in PARTS:
    for n,c in allcards[p].items():
        s=c["f"].get("事件","").strip()
        if len(s)>=15: evx[s].append((p,n))
d2={k:v for k,v in evx.items() if len(v)>1}
print(f"\n卡片「事件」字段逐字重复: {len(d2)} 条")
for k,v in sorted(d2.items(),key=lambda x:-len(x[1]))[:20]:
    print(f"  ×{len(v)}: 「{k[:70]}」 {v}")
# 钩子字段
hk=defaultdict(list)
for p in PARTS:
    for n,c in allcards[p].items():
        s=c["f"].get("钩子","").strip()
        if len(s)>=8: hk[s].append((p,n))
d3={k:v for k,v in hk.items() if len(v)>1}
print(f"\n卡片「钩子」字段逐字重复: {len(d3)} 条")
for k,v in sorted(d3.items(),key=lambda x:-len(x[1]))[:20]:
    print(f"  ×{len(v)}: 「{k[:60]}」 {v}")
