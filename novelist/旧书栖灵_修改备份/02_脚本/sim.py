import re, glob, collections

SIM = re.compile(r'像[^，。！？“"]{2,16}')
d = '第一部'
c = collections.Counter()
where = collections.defaultdict(list)
for f in sorted(glob.glob('正文/%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    for m in SIM.finditer(t):
        s = m.group()
        c[s] += 1
        where[s].append(f.split('/')[-1][:12])

print('distinct similes', len(c), 'total', sum(c.values()))
for s, n in c.most_common(40):
    print(n, s, where[s][:3])
