import re, glob, collections

SIM = re.compile(r'像[^，。！？“"]{2,16}')
d = '第二部'
c = collections.Counter()
where = collections.defaultdict(list)
for f in sorted(glob.glob('正文/%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    for m in SIM.finditer(t):
        s = m.group()
        c[s] += 1
        where[s].append((f.split('/')[-1][:13], t[max(0, m.start()-26):m.end()+14].replace('\n', ' ')))

for s, n in c.most_common(14):
    if n < 4:
        break
    print('=== %d  %s' % (n, s))
    for fn, ctx in where[s]:
        print('   ', fn, '|', ctx)
