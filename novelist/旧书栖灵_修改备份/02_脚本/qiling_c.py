#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re
from collections import Counter, defaultdict
ROOT="/mnt/d/devProject/writer/novelist/旧书栖灵"
PARTS=["第一部","第二部","第三部","第四部","第五部","第六部"]
TXT=os.path.join(ROOT,"正文")
files=[]
for p in PARTS:
    for f in sorted(os.listdir(os.path.join(TXT,p))):
        files.append((p,f,open(os.path.join(TXT,p,f),encoding='utf-8').read()))

print("="*70); print("【F-4】陆栖姐 使用分布（SKILL.md 允许但需看一致性）")
for p in PARTS:
    n=0; chs=set()
    for pp,f,t in files:
        if pp!=p: continue
        c=t.count("陆栖姐")
        if c: n+=c; chs.add(f)
    print(f"  {p}: 陆栖姐 {n}次, 分布于 {len(chs)} 章")
print("\n  苏晚/苏念 对陆栖的其它称谓:")
for term in ["陆老师","老师","师傅","陆栖姐","陆栖","小陆"]:
    c=sum(t.count(term) for _,_,t in files)
    print(f"    「{term}」全书 {c} 次")

print("="*70); print("【F-5】正文里把 陆栖 当男性/第三人称他 误用（严格模式：陆栖作主语+他）")
# 只在短距离内、且他出现在 陆栖 之后作主语的位置
pats=[r'陆栖[，,]?[  ]*(?:也|又|便|就|才|已经|一直|终于|慢慢|轻轻|静静|忽然|微微|常常|从来|向来|还|正|在|想|说|看|走|坐|站|笑|点头|摇头|伸手|低头|抬头|转身|把|拿|听|问|答|嗯|哦|呀|啊|地)?[  ]*他',
      r'陆栖(并|也|则)?[ 　]*(?:是|为)(?:一[个名位])?(?:男人|男性|先生|男)',
      r'(?<![顾林沈苏周])他[ 　]*(?:是|就是)陆栖']
hits=[]
for p,f,t in files:
    lines=t.split("\n")
    for i,l in enumerate(lines):
        for pat in pats:
            m=re.search(pat,l)
            if m:
                # 排除：他 明确指向前面出现的男性名词
                pre=l[:m.start()]
                if re.search(r'[老顾顾松年林越沈念苏晚周慎之陈伯陈老周明远许老苏晓棠陈立夏方知远]'
                             r'[^。！？，、"]{0,8}[，,、]?[ 　]*$', pre): continue
                if re.search(r'(他|它|他们)(就是|正是|便是)?$', pre): continue
                hits.append((p,f,i+1,l.strip()[:170],m.group(0)))
print(f"疑似 {len(hits)} 处:")
for p,f,i,l,g in hits: print(f"  {p}/{f}:{i}  [{g}]\n     {l}")

print("="*70); print("【F-6】灵/角色 代词一致性抽查：日记灵 小禾/李晓禾 性别")
for p in PARTS:
    for pp,f,t in files:
        if pp!=p: continue
        if "小禾" in t or "李晓禾" in t:
            he=len(re.findall(r'小禾[^。\n]{0,10}他|他[^。\n]{0,6}小禾',t))
            she=len(re.findall(r'小禾[^。\n]{0,10}她|她[^。\n]{0,6}小禾',t))
            if he or she:
                print(f"  {p}/{f[:-3]}: 小禾+他={he} 小禾+她={she} 李晓禾出现{t.count('李晓禾')}次")

print("="*70); print("【F-7】角色档案 vs 实际出场（主要有名有姓角色）")
allt="".join(t for _,_,t in files)
roles=["顾松年","林越","苏晚","苏晚晴","沈明远","沈念","周慎之","沈明棠","阿棠","李晓禾","小禾","林晓颂",
       "方知远","方小远","周明远","周小明","苏念","陈伯","陈老","周晓","许老","顾念","方知远的母亲",
       "苏晓棠","陈立夏","陈志远","刘小红","林溪","方家骏","周叔","老周","小许","阿宝"]
missing=[r for r in roles if r not in allt]
print("  出现于正文的角色:", " ".join(f"{r}({allt.count(r)})" for r in roles if r in allt))
print("\n  角色设定/ 目录中存在的档案文件:")
for f in sorted(os.listdir(os.path.join(ROOT,"设定","角色设定"))):
    has = f[:-3] in allt
    print(f"    {f[:-3]:<14} 档案存在, 正文出现={'是' if has else '★否'}")
print("\n  正文高频人名但档案缺失（出现>=20次且无同名档案）:")
arch=set(f[:-3] for f in os.listdir(os.path.join(ROOT,"设定","角色设定")))
for m,n in Counter(re.findall(r'[\u4e00-\u9fff]{2,3}', allt)):
    if m not in arch:
        c=allt.count(m)
        if c>=20: print(f"    {m}: {c}次")
