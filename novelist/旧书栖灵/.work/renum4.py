import re, glob, os, shutil

# Renumber the whole part after inserting new chapters.
D = '正文/第四部'

def info(f):
    m = re.match(r'第(\d+)章', os.path.basename(f))
    return int(m.group(1)), re.search(r'(?m)^# 第(\d+)章\s*(.+?)\s*$',
                                      open(f, encoding='utf-8').read())

fs = sorted(glob.glob(D + '/*.md'), key=lambda p: int(re.match(r'第(\d+)章', os.path.basename(p)).group(1)))

# 1. drop the duplicated number from every filename, keep order
order = []
for f in fs:
    n, _ = info(f)
    order.append(f)

# 2. renumber sequentially from 1
for i, f in enumerate(order, 1):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+?)\s*$', t)
    title = m.group(2).strip()
    newname = '%s/第%03d章-%s.md' % (D, i, title)
    newtext = re.sub(r'(?m)^# 第\d+章\s*.+$', '# 第%03d章 %s' % (i, title), t, count=1)
    if os.path.abspath(newname) != os.path.abspath(f):
        os.remove(f)
    open(newname, 'w', encoding='utf-8').write(newtext)

print('第四部重排完成')
for f in sorted(glob.glob(D + '/*.md'))[:3]:
    print(' ', os.path.basename(f))
print('  ...')
for f in sorted(glob.glob(D + '/*.md'))[-3:]:
    print(' ', os.path.basename(f))
print(' 共', len(glob.glob(D + '/*.md')), '章')