import re, glob, os, shutil

d = '正文/第四部'
KNOWN = set()
# rebuild titles from the backup, which had clean filenames
bak = '/tmp/opencode/bak_part4'
titles = []
for f in sorted(glob.glob('%s/*.md' % bak)):
    titles.append(os.path.basename(f)[:-3].split('-', 1)[1])
print('backup titles', len(titles))

cur = {}
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'^# 第\d+章\s*(.+)$', t, re.M)
    cur[f] = (m.group(1), t)

shutil.rmtree(d)
os.makedirs(d)
for i, title in enumerate(titles, 1):
    # find the current file whose heading starts with this title
    src = None
    for f, (h, t) in cur.items():
        if h.startswith(title) or title in h:
            src = t
            break
    if src is None:
        print('MISSING', title)
        continue
    body = re.sub(r'(?m)^# 第\d+章\s*' + re.escape(title), '', src, count=1)
    body = re.sub(r'(?m)^---\s*$', '', body)
    # if the heading fused the first sentence, keep the remainder as body
    m2 = re.match(r'(?s)^# 第\d+章\s*' + re.escape(title) + r'(.*?)(?:\n\n|\Z)', src)
    if m2 and m2.group(1).strip() and title not in cur.get('', ('',))[0]:
        pass
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    open('%s/第%03d章-%s.md' % (d, i, title), 'w', encoding='utf-8').write(
        '# 第%03d章 %s\n\n%s\n' % (i, title, body))

print('written', len(glob.glob('%s/*.md' % d)))
bad = [os.path.basename(f) for f in sorted(glob.glob('%s/*.md' % d))
       if int(re.match(r'第(\d+)章', os.path.basename(f)).group(1))
       != int(re.search(r'^# 第(\d+)章', open(f, encoding='utf-8').read(), re.M).group(1))]
print('head mismatch', len(bad))
