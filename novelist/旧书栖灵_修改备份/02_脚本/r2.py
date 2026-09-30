import re,sys
f=sys.argv[1]
lines=open(f,encoding='utf-8').read().split('\n')
runs=[];cur=[]
for i,l in enumerate(lines):
    if re.match(r'^\s*["「]',l): cur.append(i+1)
    elif l.strip()=='': pass
    else:
        if len(cur)>=3: runs.append((cur[0],cur[-1],len(cur)))
        cur=[]
if len(cur)>=3: runs.append((cur[0],cur[-1],len(cur)))
for a,b,n in runs: print(f"run {a}-{b} = {n}")
