import re, glob, collections, itertools

def grams(s, k=5):
    s = re.sub(r'[^一-鿿]', '', s)
    return set(s[i:i+k] for i in range(max(0, len(s)-k+1)))

paras = []  # (file, text, gramset)
for f in sorted(glob.glob('正文/*/*.md')):
    for p in open(f, encoding='utf-8').read().split('\n\n'):
        p = p.strip()
        if len(p) >= 30:
            paras.append((f, p, grams(p)))

# bucket by length to limit comparisons
buck = collections.defaultdict(list)
for i, (f, p, g) in enumerate(paras):
    buck[len(p) // 20].append(i)

pairs = []
for b in buck.values():
    for a, bb in itertools.combinations(b, 2):
        fa, pa, ga = paras[a]
        fb, pb, gb = paras[bb]
        if fa == fb:
            continue
        if not ga or not gb:
            continue
        j = len(ga & gb) / min(len(ga), len(gb))
        if j >= 0.55:
            pairs.append((j, fa, pa, fb, pb))

pairs.sort(reverse=True)
print('near-duplicate paragraph pairs across chapters:', len(pairs))
for j, fa, pa, fb, pb in pairs[:25]:
    print('%.2f  %s | %s' % (j, fa.split('/')[-1][:12], pa[:60]))
    print('      %s | %s' % (fb.split('/')[-1][:12], pb[:60]))
