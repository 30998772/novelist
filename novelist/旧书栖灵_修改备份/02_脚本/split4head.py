import re, glob, os

d = '正文/第四部'
FIX = {
 '口袋里揣了六天': '口袋里揣了六天',
 '年轮的智慧': '年轮的智慧',
 '落叶的归途': '落叶的归途',
 '林越的礼物': '林越的礼物',
 '四季的精灵': '四季的精灵',
 '四季的完成': '四季的完成',
 '春泥的花园': '春泥的花园',
 '护花的约定': '护花的约定',
}
n = 0
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', t)
    if not m:
        continue
    head = m.group(2).strip()
    for title in FIX:
        if head.startswith(title) and len(head) > len(title):
            rest = head[len(title):]
            t = (t[:m.start()]
                 + '# 第%s章 %s\n\n%s' % (m.group(1), title, rest)
                 + t[m.end():])
            open(f, 'w', encoding='utf-8').write(t)
            n += 1
            break
print('fused headings split:', n)
for f in sorted(glob.glob('%s/*.md' % d)):
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', open(f, encoding='utf-8').read())
    if m and len(m.group(2).strip()) > 12:
        print('  仍长:', os.path.basename(f), m.group(2)[:40])
