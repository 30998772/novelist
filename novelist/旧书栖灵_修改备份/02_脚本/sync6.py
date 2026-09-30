import re, glob, os
d = '正文/第六部'
RENAME = {
 '旧书的完成':'那本册子开始发光','永恒的回声':'风换了方向','花园的传承':'方小远在初冬最忙',
 '传承的永恒':'楼在清喉咙','爱的传承':'惊蛰先响了一声雷','爱的永恒':'记忆又少了一页',
 '礼物的永恒':'冬至那摞纸箱','花园的永恒':'紫藤开���了','守护的完成':'雨后她做了个决定',
 '永恒的温暖':'六月入梅'}
f = '章节大纲/第六部/逐章卡片.md'
t = open(f, encoding='utf-8').read()
n = 0
for o, w in RENAME.items():
    m = re.search(r'(?m)^### 第(\d+)章[：:]\s*' + re.escape(o) + r'\s*$', t)
    if m:
        t = t[:m.start()] + '### 第%s章：%s' % (m.group(1), w) + t[m.end():]
        n += 1
    else:
        print('MISS', o)
open(f, 'w', encoding='utf-8').write(t)
print('cards renamed', n)
c = [(int(re.match(r'第(\d+)章', os.path.basename(x)).group(1)),
      os.path.basename(x).split('-', 1)[1][:-3]) for x in sorted(glob.glob('%s/*.md' % d))]
k = [(int(m.group(1)), m.group(2).strip())
     for m in re.finditer(r'(?m)^### 第(\d+)章[：:]\s*(.+?)\s*$', t)]
print('正文', len(c), '卡片', len(k), '一致' if k == c else '不一致')
for a, b in zip(c, k):
    if a != b:
        print('  ', a, '|', b)
