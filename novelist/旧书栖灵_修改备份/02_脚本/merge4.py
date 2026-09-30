import re, glob, os

d = '正文/第四部'
merge = ['第050章', '第051章', '第052章', '第053章', '第054章']

parts, titles = [], []
for pre in merge:
    f = glob.glob('%s/%s-*.md' % (d, pre))
    assert len(f) == 1, (pre, f)
    t = open(f[0], encoding='utf-8').read()
    title = os.path.basename(f[0]).split('-', 1)[1][:-3]
    titles.append(title)
    body = re.sub(r'(?m)^# 第\d+章.*$', '', t, count=1)
    # drop scene-break rules and stray separators
    body = re.sub(r'(?m)^---\s*$', '', body)
    body = body.strip()
    parts.append('## %s\n\n%s' % (title, body))

merged = '# 第050章 四季的完成\n\n' + '\n\n'.join(parts) + '\n'
merged = re.sub(r'\n{3,}', '\n\n', merged)
open('%s/第050章-四季的完成.md' % d, 'w', encoding='utf-8').write(merged)

# delete the merged-away files (052/053/054) and keep 050/051 as they are
# -> rewrite: remove 051..054, and let 050 hold the merged body
for pre in ['第051章', '第052章', '第053章', '第054章']:
    f = glob.glob('%s/%s-*.md' % (d, pre))
    if f:
        os.remove(f[0])

# renumber 055..070 down by four
for n in range(70, 53, -1):
    old = glob.glob('%s/第%03d章-*.md' % (d, n))
    if len(old) != 1:
        continue
    ti = os.path.basename(old[0]).split('-', 1)[1][:-3]
    os.rename(old[0], '%s/第%03d章-%s.md' % (d, n - 4, ti))

for f in sorted(glob.glob('%s/*.md' % d)):
    fn = int(re.match(r'第(\d+)章', os.path.basename(f)).group(1))
    t = open(f, encoding='utf-8').read()
    m = re.search(r'^# 第(\d+)章(.*)$', t, re.M)
    if m and int(m.group(1)) != fn:
        t = t[:m.start()] + '# 第%03d章%s' % (fn, m.group(2)) + t[m.end():]
        open(f, 'w', encoding='utf-8').write(t)

print('merged titles:', titles)
print('chapters now', len(glob.glob('%s/*.md' % d)))
print('merged chapter chars', len(re.findall(r'[\u4e00-\u9fff]', merged)))
