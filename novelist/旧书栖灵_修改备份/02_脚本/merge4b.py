import re, glob, os, shutil

d = '正文/第四部'

# collect all chapters keyed by their in-file title
chs = {}
for f in glob.glob('%s/*.md' % d):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'^# 第\d+章\s*(.+)$', t, re.M)
    title = m.group(1).strip()
    body = re.sub(r'(?m)^# 第\d+章.*$', '', t, count=1)
    body = re.sub(r'(?m)^---\s*$', '', body)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    chs[title] = body
print('chapters read:', len(chs))

# merge 春天/夏天/秋天/冬天/四季的完成 into a single chapter
MERGE = ['春天的希望', '夏天的热情', '秋天的收获', '冬天的沉淀', '四季的完成']
parts = ['## %s\n\n%s' % (t, chs[t]) for t in MERGE if t in chs]
merged_body = '\n\n'.join(parts)
print('merged chars', len(re.findall(r'[\u4e00-\u9fff]', merged_body)))

new = dict(chs)
new['四季的完成'] = merged_body
for t in MERGE[:-1]:
    new.pop(t, None)

order = [t for t in chs if t != '春天的希望']  # keep original relative order
# rebuild: take the original order minus removed titles
order = []
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    order.append(re.search(r'^# 第\d+章\s*(.+)$', t, re.M).group(1).strip())
order = [t for t in order if t in new]

shutil.rmtree(d)
os.makedirs(d)
for i, title in enumerate(order, 1):
    body = '# 第%03d章 %s\n\n%s\n' % (i, title, new[title])
    open('%s/第%03d章-%s.md' % (d, i, title), 'w', encoding='utf-8').write(body)

print('written', len(glob.glob('%s/*.md' % d)))
for i, t in enumerate(order[-6:], len(order) - 5):
    print(' ', i, t)
