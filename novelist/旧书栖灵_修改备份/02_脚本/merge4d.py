import re, glob, os, shutil

d = '正文/第四部'

# read all, keyed by title
items = []
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', t)
    items.append([m.group(2).strip(), t[m.end():].lstrip('\n')])

titles = [x[0] for x in items]
bodies = dict(items)

# 050-054 (春天的希望..四季的完成) become 3 chapters
i0 = titles.index('春天的希望')
big = ''
for t in ['春天的希望', '夏天的热情', '秋天的收获', '冬天的沉淀', '四季的完成']:
    big += bodies[t].rstrip() + '\n\n'

b1 = big.index('六月初三，陆栖在东北角碰那根芽。')
b2 = big.index('十一月初九，陆栖在东北角挖了三十公分')
b3 = big.index('十二月二十九，下午三点。陆栖在东北角。')

seg = [
    ('一年的东北角', big[:b1].strip()),
    ('夏与秋', big[b1:b2].strip()),
    ('冬与完成', (big[b2:b3].strip() + '\n\n' + big[b3:]).strip()),
]

new_titles = [t for t in titles if t not in
              ('春天的希望', '夏天的热情', '秋天的收获', '冬天的沉淀', '四季的完成')]
pos = titles.index('春天的希望')
new_titles = titles[:pos] + [s[0] for s in seg] + titles[pos + 5:]
new_bodies = {t: bodies[t] for t in titles}
for name, content in seg:
    new_bodies[name] = content

shutil.rmtree(d)
os.makedirs(d)
for i, t in enumerate(new_titles, 1):
    open('%s/第%03d章-%s.md' % (d, i, t), 'w', encoding='utf-8').write(
        '# 第%03d章 %s\n\n%s\n' % (i, t, new_bodies[t].rstrip()))

print('written', len(glob.glob('%s/*.md' % d)))
for i, t in enumerate(new_titles, 1):
    if i in range(pos - 1, pos + 5):
        print('  ', i, t)
