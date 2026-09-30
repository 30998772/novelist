import re, itertools
t = open('正文/第二部/第053章-林越的参与.md', encoding='utf-8').read()
ps = [p.strip() for p in t.split('\n\n') if p.strip()]
def g(s, k=5):
    s = re.sub(r'[^一-鿿]', '', s)
    return set(s[i:i+k] for i in range(max(0, len(s)-k+1)))
G = [g(p) for p in ps]
seen = set()
for i, j in itertools.combinations(range(len(ps)), 2):
    if not G[i] or not G[j]:
        continue
    ov = len(G[i] & G[j]) / min(len(G[i]), len(G[j]))
    if ov >= 0.45 and (i, j) not in seen:
        seen.add((i, j))
        print('%.2f [%d] %s' % (ov, i, ps[i][:78]))
        print('     [%d] %s' % (j, ps[j][:78]))
