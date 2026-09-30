import re, glob, os, shutil

d = '正文/第一部'

# 1) move 051 交钥匙的春天 to the end as the epilogue
src = glob.glob('%s/第051章-*.md' % d)[0]
title = os.path.basename(src).split('-', 1)[1][:-3]

# shift 052..063 up by one
for n in range(63, 51, -1):
    old = glob.glob('%s/第%03d章-*.md' % (d, n))
    assert len(old) == 1, (n, old)
    ti = os.path.basename(old[0]).split('-', 1)[1][:-3]
    os.rename(old[0], '%s/第%03d章-%s.md' % (d, n - 1, ti))

os.rename(src, '%s/第064章-%s.md' % (d, title))
print('051 ->', '第064章-' + title)

# 2) fix in-file headings
for f in sorted(glob.glob('%s/*.md' % d)):
    fn = int(re.match(r'第(\d+)章', os.path.basename(f)).group(1))
    t = open(f, encoding='utf-8').read()
    m = re.search(r'^# 第(\d+)章(.*)$', t, re.M)
    if m and int(m.group(1)) != fn:
        t = t[:m.start()] + '# 第%03d章%s' % (fn, m.group(2)) + t[m.end():]
        open(f, 'w', encoding='utf-8').write(t)
print('headings aligned')
