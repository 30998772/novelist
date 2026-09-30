import re, glob, collections

# Remove exact/near-exact paragraph recycling: for each duplicated paragraph,
# keep the FIRST occurrence (by file order) and drop the later copies.
def norm(s):
    return re.sub(r'[^一-鿿]', '', s)

paras = collections.defaultdict(list)
for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    for p in t.split('\n\n'):
        p = p.strip()
        if len(p) >= 18:
            paras[p].append(f)

exact = {p: fs for p, fs in paras.items() if len(fs) > 1}
print('exact recycled paragraphs:', len(exact))
removed = 0
for p, fs in exact.items():
    for f in fs[1:]:
        t = open(f, encoding='utf-8').read()
        if p in t:
            nt = t.replace('\n\n' + p, '', 1)
            if nt != t:
                nt = re.sub(r'\n{3,}', '\n\n', nt)
                open(f, 'w', encoding='utf-8').write(nt)
                removed += 1
print('copies removed', removed)
