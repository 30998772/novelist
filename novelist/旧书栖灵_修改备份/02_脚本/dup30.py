import re, itertools, collections

f = '正文/第一部/第030章-执念终有归处.md'
t = open(f, encoding='utf-8').read()
paras = [p.strip() for p in t.split('\n\n') if p.strip()]

def g(s, k=5):
    s = re.sub(r'[^一-鿿]', '', s)
    return set(s[i:i+k] for i in range(max(0, len(s)-k+1)))

G = [g(p) for p in paras]
seen = []
for i, j in itertools.combinations(range(len(paras)), 2):
    if not G[i] or not G[j]:
        continue
    ov = len(G[i] & G[j]) / min(len(G[i]), len(G[j]))
    if ov >= 0.40:
        seen.append((ov, i, j))
seen.sort(reverse=True)
print('paras', len(paras), 'near-dup pairs', len(seen))
for ov, i, j in seen[:20]:
    print('%.2f [%d] %s' % (ov, i, paras[i][:74]))
    print('      [%d] %s' % (j, paras[j][:74]))
