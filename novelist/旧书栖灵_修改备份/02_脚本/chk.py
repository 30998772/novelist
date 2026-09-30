import re,sys
BAN=['微微','轻轻','缓缓','某种','仿佛','似乎','像是','那一刻']
NAYS=re.compile(r'不是[^。！？，]{1,20}[，](?:而是|是)[^。！？]{1,25}')
for f in sys.argv[1:]:
    t=open(f,encoding='utf-8').read()
    n=len(re.findall(r'[\u4e00-\u9fff]',t))
    b={w:t.count(w) for w in BAN if t.count(w)}
    m=NAYS.findall(t)
    print(f"{f} 字数={n} 禁用={b} 句式={len(m)}")
    for x in m: print("   ",x)
