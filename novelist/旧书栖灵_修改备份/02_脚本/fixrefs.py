import re, glob, os

# title -> current number for 第一部
m = {}
for f in sorted(glob.glob('正文/第一部/*.md')):
    b = os.path.basename(f)
    n = int(re.match(r'第(\d+)章', b).group(1))
    m[b.split('-', 1)[1][:-3]] = n
print('prose map built:', len(m))

for f in ['章节大纲/总纲.md', '章节大纲/第一部/逐章卡片.md']:
    t = open(f, encoding='utf-8').read()
    o = t

    def fix(mo):
        num, title = mo.group(1), mo.group(2)
        if title in m and m[title] != int(num):
            print('  %s: 第一部ch%s -> ch%03d  %s' % (f.split('/')[-1], num, m[title], title))
            return '第一部ch%03d《%s》' % (m[title], title)
        return mo.group()

    t = re.sub(r'第一部ch(\d+)《([^》]+)》', fix, t)
    if t != o:
        open(f, 'w', encoding='utf-8').write(t)
        print('updated', f)
