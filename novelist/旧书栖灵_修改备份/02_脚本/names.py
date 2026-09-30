import re, glob, collections

KNOWN = ['陆栖','顾松年','苏晚','林越','林晓颂','方知远','方小远','周慎之','周明远','周小明',
         '李晓禾','阿棠','墨点灵','沈明远','沈念','江望归','方小满','苏晚晴','顾念','苏念']

# near-miss variants: names sharing >=2 chars with a known name but not equal
counts = collections.Counter()
where = collections.defaultdict(set)
for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    for m in re.finditer(r'[一-鿿]{2,4}(?=说|问|答|想|看|走|来|去|站|坐|拿|看)', t):
        s = m.group()
        if s in KNOWN:
            continue
        if any(s != k and (s in k or k in s) for k in KNOWN):
            counts[s] += 1
            where[s].add(f.split('/')[-1])

for s, c in counts.most_common(30):
    if c >= 3:
        print(c, s, sorted(where[s])[:4])
