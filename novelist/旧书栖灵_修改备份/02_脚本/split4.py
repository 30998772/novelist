import re, glob, os, shutil

d = '正文/第四部'
f = '%s/第050章-四季的完成.md' % d
t = open(f, encoding='utf-8').read()
m = re.search(r'(?m)^# 第\d+章 四季的完成\s*$', t)
body = t[m.end():].lstrip('\n')

# split on the season-opening paragraphs
marks = ['六月初三，陆栖在东北角碰那根芽。',
         '十一月初九，陆栖在东北角挖了三十公分',
         '十二月二十九，下午三点。陆栖在东北角。']
pos = [body.index(x) for x in marks]
parts = [body[:pos[0]], body[pos[0]:pos[1]], body[pos[1]:pos[2]], body[pos[2]:]]

titles = ['一年的东北角', '夏与秋', '冬与完成']
chapters = ['# 第050章 %s\n\n%s' % (titles[0], parts[0].strip()),
            '# 第051章 %s\n\n%s' % (titles[1], parts[1].strip()),
            '# 第052章 %s\n\n%s' % (titles[2], parts[2].strip() + '\n\n' + parts[3].strip())]

# rewrite the part of 第四部 starting here, shifting the rest by +2
rest = []
for g in sorted(glob.glob('%s/*.md' % d)):
    if g == f:
        continue
    tt = open(g, encoding='utf-8').read()
    mm = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', tt)
    rest.append((int(mm.group(1)), mm.group(2).strip(), tt[mm.end():].lstrip('\n')))
rest.sort()

shutil.rmtree(d)
os.makedirs(d)
for i, c in enumerate(chapters, 1):
    open('%s/第%03d章-%s.md' % (d, i, re.match(r'# 第\d+章 (.+)', c).group(1)),
         'w', encoding='utf-8').write(c.rstrip() + '\n')
for n, title, body2 in rest:
    newn = n + 2
    open('%s/第%03d章-%s.md' % (d, newn, title), 'w', encoding='utf-8').write(
        '# 第%03d章 %s\n\n%s' % (newn, title, body2.rstrip()) + '\n')

print('chapters', len(glob.glob('%s/*.md' % d)))
for c in chapters:
    print('  ', c.split('\n')[0], len(re.findall(r'[\u4e00-\u9fff]', c)))
