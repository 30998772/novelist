import re, glob, os

# rebuild 第一部 cards: 63 chapters in prose, renumber cards to match
prose = sorted(glob.glob('正文/第一部/*.md'))
titles = {}
for f in prose:
    b = os.path.basename(f)[:-3]
    m = re.match(r'第(\d+)章-(.+)', b)
    titles[int(m.group(1))] = m.group(2)
print('prose chapters', len(titles), min(titles), max(titles))

f = '章节大纲/第一部/逐章卡片.md'
t = open(f, encoding='utf-8').read()

# list existing cards in order with their body
blocks = re.split(r'(?m)^(?=### 第\d+章 )', t)
head = blocks[0]
cards = []
for b in blocks[1:]:
    m = re.match(r'### 第(\d+)章 ([^\n]*)\n', b)
    if m:
        cards.append([int(m.group(1)), m.group(2).strip(), b])
print('cards found', len(cards))

# insert the new 032 各述所等 right after 执念终有归处
for i, c in enumerate(cards):
    if c[1] == '执念终有归处':
        new = [32, '各述所等', """### 第032章 各述所等
- **场景**：文献馆，雪夜
- **本章目标**：诸灵各述所等
- **事件**：灯灵那封没寄出的信；板书灵点破"我们等的是被看见"
- **钩子**：阿棠那四句诗被念出来

"""]
        cards.insert(i + 1, new)
        break

# renumber sequentially
for i, c in enumerate(cards, 1):
    c[0] = i
    c[2] = re.sub(r'(?m)^### 第\d+章 .*$', '### 第%03d章 %s' % (i, c[1]), c[2], count=1)

t = head + ''.join(c[2] for c in cards)
# fix volume ranges: 63 chapters / 10 volumes
t = re.sub(r'（0\d\d-0\d\d）', '', t)
open(f, 'w', encoding='utf-8').write(t)
print('cards now', len(re.findall(r'^### 第', t, re.M)))
