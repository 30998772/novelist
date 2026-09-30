import re, glob, os

d = '正文/第一部'
order = []
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    order.append((os.path.basename(f)[:-3].split('-', 1)[1], t))

f = '章节大纲/第一部/逐章卡片.md'
cards = open(f, encoding='utf-8').read()
blocks = re.split(r'(?m)^(?=### 第\d+章 )', cards)
head, body = blocks[0], blocks[1:]

parsed = []
for b in body:
    m = re.match(r'### 第\d+章\s*(.+?)\n', b)
    if m:
        parsed.append([m.group(1).strip(), b])

by_title = {t: b for t, b in parsed}
print('cards', len(parsed), 'prose', len(order))

missing = [t for t, _ in order if t not in by_title]
print('prose chapters with no card:', missing)

# rebuild in prose order, renaming numbers and any title mismatch
out = []
for i, (title, _) in enumerate(order, 1):
    if title in by_title:
        b = by_title[title]
    else:
        # reuse the card of the chapter that previously held this number
        b = parsed[min(i - 1, len(parsed) - 1)][1]
    b = re.sub(r'(?m)^### 第\d+章.*$', '### 第%03d章 %s' % (i, title), b, count=1)
    out.append(b.rstrip() + '\n\n')

open(f, 'w', encoding='utf-8').write(head + ''.join(out))
print('cards rewritten:', len(re.findall(r'^### 第', open(f, encoding='utf-8').read(), re.M)))
