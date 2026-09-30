import re, glob

f = '章节大纲/第四部/逐章卡片.md'
t = open(f, encoding='utf-8').read()
blocks = re.split(r'(?m)^(?=### 第\d+章)', t)
head = blocks[0]
rest = blocks[1:]

# index by title, preferring the fullest block
by = {}
for b in rest:
    m = re.match(r'### 第\d+章?[：:]?\s*(.+?)\n', b)
    if not m:
        continue
    title = m.group(1).strip()
    if title not in by or len(b) > len(by[title]):
        by[title] = b
print('unique card titles', len(by))

prose = [re.search(r'(?m)^# 第\d+章\s*(.+)$', open(x, encoding='utf-8').read()).group(1).strip()
         for x in sorted(glob.glob('正文/第四部/*.md'))]
print('prose', len(prose))
missing = [x for x in prose if x not in by]
print('missing cards for:', missing)

out = []
for i, title in enumerate(prose, 1):
    b = by.get(title)
    if b is None:
        continue
    b = re.sub(r'(?m)^### 第\d+章?[：:]?.*$', '### 第%d章：%s' % (i, title), b, count=1)
    out.append(b.rstrip() + '\n\n')

open(f, 'w', encoding='utf-8').write(head + ''.join(out))
print('written cards', len(re.findall(r'(?m)^### 第', open(f, encoding='utf-8').read())))
