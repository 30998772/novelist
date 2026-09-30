import re, glob, os, shutil

d = '正文/第一部'

# Read every chapter, keyed by its in-file title line (not the filename)
chapters = {}
for f in glob.glob('%s/*.md' % d):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'^# 第\d+章\s*(.+)$', t, re.M)
    if not m:
        print('NOHEAD', f)
        continue
    title = m.group(1).strip()
    if title in chapters:
        # duplicate title: keep the longer (more complete) one
        if len(t) > len(chapters[title]):
            chapters[title] = t
        print('dup title, kept longer:', title, os.path.basename(f))
    else:
        chapters[title] = t

print('unique chapters', len(chapters))

# Target order: move 交钥匙的春天 to the very end
order = list(chapters.keys())
if '交钥匙的春天' in order:
    order.remove('交钥匙的春天')
    order.append('交钥匙的春天')

# wipe and rewrite cleanly
shutil.rmtree(d)
os.makedirs(d)
for i, title in enumerate(order, 1):
    body = chapters[title]
    body = re.sub(r'^# 第\d+章.*$', '# 第%03d章 %s' % (i, title), body, count=1, flags=re.M)
    body = re.sub(r'\n{3,}', '\n\n', body).rstrip() + '\n'
    open('%s/第%03d章-%s.md' % (d, i, title), 'w', encoding='utf-8').write(body)

print('written', len(glob.glob('%s/*.md' % d)))
for i, t in enumerate(order, 1):
    if i <= 3 or i >= len(order) - 3:
        print(i, t)
