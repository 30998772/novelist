import re, glob, collections

files = sorted(glob.glob('正文/*/*.md'))
print('chapters:', len(files))

tot = 0
short = collections.Counter()
dupintra = 0
gap = 0
oddq = 0
for f in files:
    t = open(f, encoding='utf-8').read()
    n = len(re.findall(r'[\u4e00-\u9fff]', t))
    tot += n
    part = f.split('/')[1]
    if n < 3000:
        short[part] += 1
    if '\n\n\n' in t:
        gap += 1
    if t.count('"') % 2:
        oddq += 1
    ps = [p.strip() for p in t.split('\n') if len(p.strip()) >= 20]
    c = collections.Counter(ps)
    for k, v in c.items():
        if v > 1 and '眼睛——看不见' not in k:
            dupintra += 1
            print('INTRA-DUP', f, v, k[:40])

print('total chars:', tot)
print('under 3000 by part:', dict(short))
print('blank-gap files:', gap)
print('odd-quote files:', oddq)
print('intra-file dup paragraphs:', dupintra)
