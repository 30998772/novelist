#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os,re
ROOT="/mnt/d/devProject/writer/novelist/旧书栖灵"
TXT=os.path.join(ROOT,"正文")
SAMPLE={"第一部":[1,2,6,12,18,24,30,36,42,48,54,60],
 "第二部":[1,20,40,62,70],"第三部":[1,20,40,60,70],
 "第四部":[1,30,50,64,70],"第五部":[1,30,43,64,70],
 "第六部":[1,30,50,57,62,66,70]}
def cn(t): return len(re.findall(r'[\u4e00-\u9fff]',t))
for p,ns in SAMPLE.items():
    for n in ns:
        fn=[f for f in os.listdir(os.path.join(TXT,p)) if f.startswith(f"第{n:03d}章")][0]
        t=open(os.path.join(TXT,p,fn),encoding='utf-8').read()
        ps=[x.strip() for x in t.split("\n") if x.strip()]
        # 去掉 markdown 标题行
        body=[x for x in ps if not x.startswith("#")]
        a=body[0]; b=body[-1]
        dlg=len(re.findall(r'[“"]',t))
        print(f"\n{'='*100}")
        print(f"### {p} ch{n:03d} 《{fn[7:-3]}》 中文字={cn(t)}  段落数={len(body)}  引号对数≈{dlg//2}  引号密度={dlg/2/cn(t)*1000:.1f}对/千字")
        print(f"[开篇] {a[:300]}")
        print(f"[章末] ...{b[-320:]}")
