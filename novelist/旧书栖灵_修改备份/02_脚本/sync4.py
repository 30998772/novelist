import re, glob, os

prose = []
for f in sorted(glob.glob('正文/第四部/*.md')):
    t = open(f, encoding='utf-8').read()
    prose.append(re.search(r'(?m)^# 第\d+章\s*(.+)$', t).group(1).strip())

f = '章节大纲/第四部/逐章卡片.md'
cards = open(f, encoding='utf-8').read()
blocks = re.split(r'(?m)^(?=### 第\d+章 )', cards)
head, body = blocks[0], blocks[1:]
parsed = []
for b in body:
    m = re.match(r'### 第\d+章\s*(.+?)\n', b)
    if m:
        parsed.append([m.group(1).strip(), b])
print('cards', len(parsed), 'prose', len(prose))

by_title = {t: b for t, b in parsed}
out = []
for i, title in enumerate(prose, 1):
    b = by_title.get(title)
    if b is None:
        b = parsed[min(i - 1, len(parsed) - 1)][1]
    b = re.sub(r'(?m)^### 第\d+章.*$', '### 第%03d章 %s' % (i, title), b, count=1)
    out.append(b.rstrip() + '\n\n')

open(f, 'w', encoding='utf-8').write(head + ''.join(out))
print('cards now', len(re.findall(r'(?m)^### 第', open(f, encoding='utf-8').read())))
