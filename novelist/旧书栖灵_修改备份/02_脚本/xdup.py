import re, glob, collections

allp = collections.defaultdict(list)
for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    for p in t.split('\n\n'):
        p = p.strip()
        if len(p) >= 18:
            allp[p].append(f)

multi = {p: fs for p, fs in allp.items() if len(fs) > 1}
print('paragraphs in >1 chapter:', len(multi), ' total instances', sum(len(v) for v in multi.values()))
percount = collections.Counter()
for p, fs in multi.items():
    percount[len(fs)] += 1
print('by spread:', dict(sorted(percount.items())))
print()
for p, fs in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:20]:
    print(len(fs), [x.split('/')[-1][:12] for x in fs])
    print('    ', p[:78])
