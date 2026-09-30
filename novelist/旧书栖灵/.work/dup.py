import re, glob, collections
def norm(p): return re.sub(r'[^一-鿿]','',p)
para=collections.defaultdict(set); sent=collections.defaultdict(set)
for f in sorted(glob.glob('正文/*/*.md')):
    b=f.split('/')[-1][:16]; t=open(f,encoding='utf-8').read()
    for p in re.split(r'[\n。！？]+',t):
        p=p.strip()
        if len(norm(p))>=22: sent[norm(p)].add(b)
pd=[(len(v),k) for k,v in para.items() if len(v)>=2]
sd=[(len(v),k) for k,v in sent.items() if len(v)>=3]
sd.sort(reverse=True)
print('整句 跨3章以上重复: %d'%len(sd))
for n,k in sd[:12]: print('  %d  %s'%(n,k[:58]))
