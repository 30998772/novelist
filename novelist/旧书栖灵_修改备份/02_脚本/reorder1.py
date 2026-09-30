import re, glob, os, shutil

d = '正文/第一部'
chapters = {}
for f in glob.glob('%s/*.md' % d):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'^# 第\d+章\s*(.+)$', t, re.M)
    chapters[m.group(1).strip()] = t

order = list(chapters.keys())

# enforce the correct closing sequence:
#   守到最后一盏灯 (顾松年决定退休)
#   晚风里的约定   (顾松年搬走)
#   晚风年年都来   (陆栖独自留灯)
#   交钥匙的春天   (数十年后的交棒)
tail = ['守到最后一盏灯', '晚风里的约定', '晚风年年都来', '交钥匙的春天']
for t in tail:
    order.remove(t)
order = order + tail

shutil.rmtree(d)
os.makedirs(d)
for i, title in enumerate(order, 1):
    body = re.sub(r'^# 第\d+章.*$', '# 第%03d章 %s' % (i, title),
                  chapters[title], count=1, flags=re.M)
    body = re.sub(r'\n{3,}', '\n\n', body).rstrip() + '\n'
    open('%s/第%03d章-%s.md' % (d, i, title), 'w', encoding='utf-8').write(body)

print('chapters', len(glob.glob('%s/*.md' % d)))
for i, t in enumerate(order[-5:], len(order) - 4):
    print(i, t)
