import re

f = '章节大纲/第一部/逐章卡片.md'
t = open(f, encoding='utf-8').read()

# insert a card for the new 030 提灯巡馆, and renumber 030..061 -> 031..062
old = """### 第030章 执念终有归处"""
new = """### 第030章 提灯巡馆
- **场景**：文献馆各区，入夜
- **本章目标**：提灯童子逐区照看住户
- **事件**：印章灵、纸屑灵、糖画灵、词典小姑娘各得一灯
- **钩子**：灯归函套，"都记下了"

### 第031章 执念终有归处"""
assert old in t
t = t.replace(old, new, 1)

for n in range(61, 29, -1):
    pat = '### 第%03d章 ' % n
    if pat in t:
        t = t.replace(pat, '### 第%03d章 ' % (n + 1), 1)

t = t.replace('（025-030）', '（025-030）')
t = t.replace('（032-037）', '（033-038）')
for old, new in [('038-043', '039-044'), ('044-049', '045-050'),
                 ('050-055', '051-056'), ('056-061', '057-062')]:
    t = t.replace('（%s）' % old, '（%s）' % new)

open(f, 'w', encoding='utf-8').write(t)
print('cards:', len(re.findall(r'^### 第', t, re.M)))
