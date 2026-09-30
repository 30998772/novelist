import re, glob, os, shutil
d = '正文/第六部'
RENAME = {
 '旧书的完成':   '那本册子开始发光',
 '永恒的回声':   '风换了方向',
 '花园的传承':   '方小远在初冬最忙',
 '传承的永恒':   '楼在清喉咙',
 '爱的传承':     '惊蛰先响了一声雷',
 '爱的永恒':     '记忆又少了一页',
 '礼物的永恒':   '冬至那摞纸箱',
 '花园的永恒':   '紫藤开花了',
 '守护的完成':   '雨后她做了个决定',
 '永恒的温暖':   '六月入梅',
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
shutil.rmtree(d); os.makedirs(d)
for i, t in enumerate(titles, 1):
    open('%s/第%03d章-%s.md' % (d, i, t), 'w', encoding='utf-8').write(
        '# 第%03d章 %s\n\n%s\n' % (i, t, bodies[t].rstrip()))
print('chapters', len(glob.glob('%s/*.md' % d)))
AB = re.compile('永恒|完成|圆满|传承|升华|觉醒|归宿|无限')
print('抽象标题剩:', [t for t in titles if AB.search(t)])
