#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, itertools
from collections import Counter, defaultdict
ROOT="/mnt/d/devProject/writer/novelist/旧书栖灵"
PARTS=["第一部","第二部","第三部","第四部","第五部","第六部"]
TXT=os.path.join(ROOT,"正文")

titles={}; 
for p in PARTS:
    titles[p]={}
    for f in os.listdir(os.path.join(TXT,p)):
        m=re.match(r'第(\d+)章-(.+)\.md$',f)
        titles[p][int(m.group(1))]=m.group(2)

print("="*70); print("【A-1】章标题跨部重名（完全相同）")
allt=defaultdict(list)
for p in PARTS:
    for n,t in titles[p].items(): allt[t].append(f"{p}ch{n:03d}")
dup={k:v for k,v in allt.items() if len(v)>1}
print(f"全书唯一标题数: {len(allt)} / 410章")
print(f"跨部(或部内)完全重名标题: {len(dup)} 个")
for k,v in sorted(dup.items(), key=lambda x:-len(x[1])): print(f"  《{k}》 x{len(v)}: {v}")

print("="*70); print("【A-2】第五部/第六部 vs 前四部 标题主题词重合")
THEMES={"灯/灯火":["灯"],"永恒/常明":["永恒","常明","不灭"],"传承/传递":["传承","传递","交","递"],
        "约定/誓言":["约定","承诺","誓言"],"守护/守望/守住":["守护","守望","守住","守","守的"],
        "温暖/暖":["温暖","暖"],"成长/新生":["成长","新生","崛起"],"故事/记忆/回忆":["故事","记忆","回忆","记忆"],
        "新一代":["新一代"],"回声/共鸣":["回声","共鸣"],"礼/礼物":["礼","礼物"],"生命/闭环":["生命","闭环","完成"],
        "花园/种子/年轮":["花园","种子","年轮","落叶","果实"],"时间/岁月/四季":["时间","岁月","四季","季节"]}
def hit(t,ws): return [w for w in ws if w in t]
prev=[f"第{x}部" for x in "一二三四"]
for later in ["第五部","第六部"]:
    print(f"\n--- {later} (70章) 标题命中主题词 ---")
    for theme,ws in THEMES.items():
        hp=[(n,t) for n,t in titles[later].items() if hit(t,ws)]
        # 前四部命中率
        prevtot=sum(len([1 for n,t in titles[q].items() if hit(t,ws)]) for q in prev)
        prevn=sum(len(titles[q]) for q in prev)
        print(f"  {theme:<12} {later}={len(hp):>2}/70 ({len(hp)/70*100:>4.1f}%)  前四部={prevtot}/{prevn} ({prevtot/prevn*100:.1f}%)  {len(hp)*7>prevtot and '★后部>前部' or ''}")

print("="*70); print("【A-3】永恒/常明/灯/约定/守护 类标题全书占比（逐部）")
KEY=["永恒","常明","灯火","灯","守护","守望","约定","传承","传递"]
for p in PARTS:
    c=Counter()
    for n,t in titles[p].items():
        for k in KEY:
            if k in t: c[k]+=1
    tot=sum(1 for n,t in titles[p].items() if any(k in t for k in KEY))
    print(f"{p}: 命中任一关键词 {tot}/{len(titles[p])} = {tot/len(titles[p])*100:.1f}%  明细={dict(c)}")

print("="*70); print("【A-4】标题2-gram 重复度（后两部 vs 前四部）")
def grams(p,n=2):
    g=Counter()
    for t in titles[p].values():
        for i in range(len(t)-n+1): g[t[i:i+n]]+=1
    return g
for p in PARTS:
    g=grams(p)
    rep=sum(v-1 for v in g.values() if v>1)
    print(f"{p}: 二元组总数={sum(g.values())} 唯一={len(g)} 重复条数={rep} 重复率={rep/sum(g.values())*100:.1f}%  Top: {g.most_common(5)}")

print("="*70); print("【A-5】第五/六部 标题 与 前四部标题 的字符级 Jaccard 近重复(>=0.5)")
def jac(a,b):
    A,B=set(a),set(b)
    return len(A&B)/len(A|B)
prevpairs=[(n,t) for q in prev for n,t in titles[q].items()]
for later in ["第五部","第六部"]:
    sims=[]
    for n,t in titles[later].items():
        best=max(((jac(t,pt),pn,pt) for pn,pt in prevpairs))
        sims.append((best[0],f"{later}ch{n:03d}《{t}》",f"~{best[2]}《{best[1]}》"))
    sims.sort(reverse=True)
    hi=[s for s in sims if s[0]>=0.5]
    print(f"\n{later}: 与前四部标题字符相似度>=0.5 的章: {len(hi)}/70 ({len(hi)/70*100:.1f}%)")
    for s in sims[:12]: print(f"  {s[0]:.2f}  {s[1]}  ~  {s[2]}")

# ---------- F 性别 ----------
print("="*70); print("【F-1】陆栖性别一致性（正文）")
he=[];she=0;tot=0
for p in PARTS:
    for n in sorted(titles[p]):
        f=[x for x in os.listdir(os.path.join(TXT,p)) if x.startswith(f"第{n:03d}章")][0]
        t=open(os.path.join(TXT,p,f),encoding='utf-8').read()
        for i,l in enumerate(t.split("\n")):
            if "陆栖" in l:
                tot+=1
                if re.search(r'陆栖[^。！？，、"”\']{0,12}他',l) or re.search(r'他[^。！？，、"”\']{0,6}陆栖',l):
                    he.append((p,n,i+1,l.strip()[:120]))
print(f"含'陆栖'的行数: {tot}; 疑似用'他'指代陆栖的行数: {len(he)}")
for p,n,ln,l in he[:40]: print(f"  {p}ch{n:03d}:{ln}: {l}")

print("="*70); print("【F-1b】全部大纲/设定文件中 陆栖…他")
for dp,dn,fn in os.walk(ROOT):
    if "旧稿" in dp: continue
    for x in fn:
        if not x.endswith(".md"): continue
        fp=os.path.join(dp,x)
        t=open(fp,encoding='utf-8',errors='ignore').read()
        for i,l in enumerate(t.split("\n")):
            if re.search(r'(陆栖|小栖)[^。\n]{0,14}他',l) or re.search(r'他[^。\n]{0,8}(说|走|看|想|笑)',l) and '陆栖' in l:
                print(f"  {fp.replace(ROOT+'/','')}:{i+1}: {l.strip()[:140]}")
