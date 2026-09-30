import re, glob, itertools, collections

d = '正文/第四部'
for f in sorted(glob.glob(d + '/*.md')):
    t = open(f, encoding='utf-8').read()
    paras = [p.strip() for p in t.split('\n\n') if p.strip()]
    if len(paras) < 20:
        continue
    def g(s, k=5):
        s = re.sub(r'[^一-鿿]', '', s)
        return set(s[i:i+k] for i in range(max(0, len(s)-k+1)))
    G = [g(p) for p in paras]
    hits = []
    for i, j in itertools.combinations(range(len(paras)), 2):
        if not G[i] or not G[j]:
            continue
        ov = len(G[i] & G[j]) / min(len(G[i]), len(G[j]))
        if ov >= 0.45:
            hits.append((ov, i, j))
    if hits:
        hits.sort(reverse=True)
        n = len(re.findall(r'[\u4e00-\u9fff]', t))
        print('=== %s  %d字 %d段  dup%d' % (f.split('/')[-1][:20], n, len(paras), len(hits)))
        for ov, i, j in hits[:4]:
            print('   %.2f %s' % (ov, paras[i][:64]))
            print('        %s' % paras[j][:64])
