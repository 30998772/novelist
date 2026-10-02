import re,sys
f,target=sys.argv[1],int(sys.argv[2])
t=open(f,encoding='utf-8').read()
HAND=r'摸|按|压|贴|碰|抓|捏|捧|托|抠|划|擦|戳|握|搁|攥|搓|蹭|甩|插|抽|挑|抖|拍|推|拉|翻|揭|抚|摩'
TOUCH=r'厚|薄|软|硬|涩|黏|糙|滑|毛|渣|屑|钝|粗|细|密|稀|脆|实|凸|凹|烫|凉|温|皱|裂|渗'
def c(s): return len(re.sub(r'\s','',s))
def cost(x):
    if x.startswith('"'): return 10**6
    if re.search(HAND,x) or re.search(TOUCH,x): return 10**6
    n=c(x)
    sc=n
    if re.search(r'陆栖想|她想|也许|大概|原来',x): sc+=n
    if not re.search(r'[：。「"“]',x): sc+=n//2
    return sc
L=[x.strip() for x in t.split('\n') if x.strip()]
title,body=L[0],L[1:]
cur=c(t)
guard=0
while cur>target and guard<400:
    guard+=1
    cands=[(cost(x),i) for i,x in enumerate(body) if c(x)>=45 and cost(x)<10**5]
    if not cands: print('无候选'); break
    cands.sort(reverse=True)
    _,idx=cands[0]
    cur-=c(body[idx]); body.pop(idx)
t=title+'\n\n'+'\n\n'.join(body)+'\n'
t=re.sub(r'\n{3,}','\n\n',t)
open(f,'w',encoding='utf-8').write(t)
print('%d→%d (目标%d) 删除%d段'%(cur+sum(c(x) for x in ['']) ,c(t),target,guard))
