import re, glob, os, shutil

d = '正文/第五部'
# abstract titles -> the concrete event in that chapter
RENAME = {
 '传承的开始': '第一份借阅登记单',
 '传承的挑战': '南墙的编号乱了',
 '家庭的传承': '书房支起窗来',
 '永恒的约定': '檐上停了一只燕子',
 '灯火的永恒': '没开灯下楼',
 '守望的完成': '头一场黄叶雨',
 '方小远的传承': '一夜之间绿了满枝',
 '守望的永恒': '晒书会第二天',
 '守望的意义': '天台落了一地槐花',
 '家庭的永恒': '石榴开的第一朵',
 '传承的完成': '把馆里的事录成一册',
}

items = []
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', t)
    items.append([m.group(2).strip(), t[m.end():].lstrip('\n')])

titles, bodies = [], {}
for ti, body in items:
    new = RENAME.get(ti, ti)
    titles.append(new)
    bodies[new] = bodies.get(new, '') + ('\n\n' if new in bodies else '') + body.strip()

shutil.rmtree(d)
os.makedirs(d)
for i, t in enumerate(titles, 1):
    open('%s/第%03d章-%s.md' % (d, i, t), 'w', encoding='utf-8').write(
        '# 第%03d章 %s\n\n%s\n' % (i, t, bodies[t].rstrip()))

f = '章节大纲/第五部/逐章卡片.md'
cards = open(f, encoding='utf-8').read()
blocks = re.split(r'(?m)^(?=### 第\d+章)', cards)
head = blocks[0]
by = {}
for b in blocks[1:]:
    m = re.match(r'### 第\d+章[：:]\s*(.+?)\n', b)
    if m and m.group(1).strip() not in by:
        by[m.group(1).strip()] = b
out = []
for i, t in enumerate(titles, 1):
    b = by.get(t)
    if b is None:
        print('NOCARD', i, t)
        continue
    b = re.sub(r'(?m)^### 第\d+章[：:].*$', '### 第%d章：%s' % (i, t), b, count=1)
    out.append(b.rstrip() + '\n\n')
open(f, 'w', encoding='utf-8').write(head + ''.join(out))

print('chapters', len(glob.glob('%s/*.md' % d)))
AB = re.compile('永恒|完成|圆满|传承|升华|觉醒|归宿|无限')
print('抽象标题剩:', [t for t in titles if AB.search(t)])
