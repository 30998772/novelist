import re, glob, os
D = '正文/第四部'
files = sorted(glob.glob(D + '/*.md'), key=lambda p: os.path.basename(p))
titles = []
for f in files:
    t = open(f, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第\d+章\s*(.+?)\s*$', t)
    titles.append((f, m.group(1).strip()))

# desired sequence for the split block
fixed = ['夏天的热情', '秋天的收获', '冬天的沉淀', '四季的完成']
rest = [t for _, t in titles if t not in fixed]
seq = rest[:50] + fixed + rest[50:]

seen = set()
assert len(seq) == len(titles), (len(seq), len(titles))
for i, title in enumerate(seq, 1):
    assert title not in seen, title
    seen.add(title)

by_title = dict(titles)
for f in files:
    os.remove(f)
for i, title in enumerate(seq, 1):
    t = by_title[title]
    t = re.sub(r'(?m)^# 第\d+章\s*.+$', '# 第%03d章 %s' % (i, title), t, count=1)
    open('%s/第%03d章-%s.md' % (D, i, title), 'w', encoding='utf-8').write(t.rstrip() + '\n')

print('第四部 %d 章，重排完成' % len(seq))
for f in sorted(glob.glob(D + '/*.md'))[49:56]:
    t = open(f, encoding='utf-8').read()
    print('  %-28s %5d' % (os.path.basename(f), len(re.sub(r'\s', '', t))))