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

# ============ F 精准性别检查 ============
print("="*70); print("【F-2】精准：陆栖被当作男性/代词误用")
# 句首/主语位置 陆栖 后紧跟 他
pat1=re.compile(r'陆栖[，,]?\s*(?:又|也|便|就|才|已经|一直|终于|慢慢|轻轻|静静|忽然|微微|常常|从来|向来|从来)?\s*他')
pat2=re.compile(r'(?<![们他她])陆栖是[^。\n]{0,8}(先生|老师|师傅|小伙子|男人|男)')
pat3=re.compile(r'陆栖姐|小陆哥|陆先生|陆师傅')
hits=[]
for p,f,t in files:
    for i,l in enumerate(t.split("\n")):
        for pat,name in [(pat1,"陆栖…他"),(pat2,"陆栖是+男性称谓"),(pat3,"错误称谓")]:
            for m in pat.finditer(l):
                hits.append((name,p,f,i+1,l.strip()[:150]))
print(f"命中 {len(hits)} 处:")
for name,p,f,ln,l in hits: print(f"  [{name}] {p}/{f}:{ln}\n      {l}")

print("="*70); print("【F-3】大纲/设定文件中 陆栖 用「他」（逐行人工可读清单）")
for dp,dn,fn in os.walk(ROOT):
    if "/旧稿" in dp: continue
    for x in sorted(fn):
        if not x.endswith(".md"): continue
        fp=os.path.join(dp,x)
        for i,l in enumerate(open(fp,encoding='utf-8',errors='ignore').read().split("\n")):
            if re.search(r'陆栖',l) and re.search(r'他',l) and not re.search(r'其他|他们|他的(书|灵|故事|名字|工作|生活|决定|态度|眼神里|方式|位置|想法|记忆|世界|妈|爸爸|哥|弟|妹|爷|奶)',l):
                print(f"  {fp.replace(ROOT+'/','')}:{i+1}: {l.strip()[:170]}")

# ============ G 同一灵/同一故事 重复登场 ============
print("="*70); print("【G】主要灵/角色 全书出现章分布")
NAMES=["雪团","纸屑灵","阿棠","沈明棠","周慎之","足音先生","字典老先生","借阅册灵","乐谱灵","板书灵",
       "日记灵","李晓禾","小禾","灯笼灵","零零一","围裙灵","顾松年","林越","苏晚","苏晚晴","沈明远","沈念",
       "老槐树","槐叶灵","墨点灵","林晓颂","方知远","方小远","周明远","周小明","苏念","陈伯","陈老","周晓",
       "许老","顾念","方知远的母亲","土地灵","精灵"]
res=defaultdict(dict)
for name in NAMES:
    for p in PARTS:
        ns=[]
        for f in sorted(os.listdir(os.path.join(TXT,p))):
            t=open(os.path.join(TXT,p,f),encoding='utf-8').read()
            if name in t: ns.append(int(re.match(r'第(\d+)章',f).group(1)))
        if ns: res[name][p]=ns
for name in NAMES:
    if name not in res: continue
    tot=sum(len(v) for v in res[name].values())
    parts_present=len(res[name])
    print(f"\n{name}: 出现于 {parts_present} 部, 共 {tot} 章  " + " | ".join(f"{p}:{len(v)}章(首{','.join(map(str,v[:8]))}{'…' if len(v)>8 else ''})" for p,v in res[name].items()))

# 乐谱灵/土地灵 深查
print("="*70); print("【G-2】乐谱灵/老赵/土地灵 全书出现位置")
for name in ["乐谱灵","老赵","土地灵","土地精灵","音乐精灵","三块钱的煤球炉"]:
    lst=[]
    for p in PARTS:
        for f in sorted(os.listdir(os.path.join(TXT,p))):
            t=open(os.path.join(TXT,p,f),encoding='utf-8').read()
            c=t.count(name)
            if c: lst.append((p,f[:-3],c))
    print(f"\n{name}: {len(lst)}章 合计{sum(x[2] for x in lst)}次")
    for x in lst: print(f"   {x[0]} {x[1]}  x{x[2]}")

# ============ H AI 痕迹 高频词 ============
print("="*70); print("【H】AI 痕迹高频词组")
alltext="".join(t for _,_,t in files)
chapcnt=defaultdict(set)
def count(gram, n):
    tot=0
    for p,f,t in files:
        c=len(re.findall(gram,t))
        if c: tot+=c; chapcnt[gram].add(f"{p}/{f}")
    return tot
WORDS=["温柔","晚风","灯","轻轻","静静地","静静","弯了弯","没有说话","灯火","轻声","慢慢","淡淡地",
       "微微","一丝","笑了笑","点点头","说：","她说","他说","眼眶","鼻子一酸","心里","像是","仿佛",
       "轻轻地","一点一点","一年一年","岁岁","旧书","纸页","天井","木楼梯","茉莉花茶","光","暖黄",
       "忽然","记得","等着","慢慢长","亮起来","发亮","不急不缓","安安静静","很多年","一直","终于",
       "是啊","好吗","笑了","温柔地","安静地","慢慢地","轻轻地说","远远地","小心地","认真地"]
rows=[]
for w in WORDS:
    g=re.escape(w)
    tot=len(re.findall(g,alltext))
    chs=chapcnt.get(g,set())
    rows.append((tot,w,len(chs)))
for tot,w,nc in sorted(rows,reverse=True):
    print(f"  {w:<10} 全书{tot:>5}次  出现于{nc:>3}章")

# 4-6字 n-gram Top
print("="*70); print("【H-2】全书 Top40 四字及以上高频词组")
clean=re.sub(r'\s+','',alltext)
cc=Counter()
for n in [4,5,6]:
    for i in range(len(clean)-n+1):
        g=clean[i:i+n]
        if re.fullmatch(r'[\u4e00-\u9fff]+',g): cc[g]+=1
top=[(g,c) for g,c in cc.most_common(4000)]
seen=set(); res=[]
for g,c in top:
    if any(g in s for s in seen): continue
    seen.add(g); res.append((g,c))
    if len(res)>=40: break
for g,c in res: print(f"  {g:<8} {c:>5}")
