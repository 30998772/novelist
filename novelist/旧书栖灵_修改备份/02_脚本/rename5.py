import re, glob, os, shutil

d = '正文/第五部'
# "新一代的X" names nobody. Rename to what actually happens in the chapter.
RENAME = {
 '新一代的学习': '林晓颂第一次当班',
 '新一代的成长': '她比谁都早',
 '新一代的故事': '旧课本区的那排架子',
 '新一代的崛起': '馆里热闹起来了',
 '新一代的承诺': '一场雷阵雨',
 '新一代的开始': '一夜之间绿了',
 '新一代的约定': '蓝布面的馆簿',
 '新一代的贡献': '三份捐赠清册',
 '新一代的独立': '她一个人待了三天',
}

items = []
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', t)
    items.append([m.group(2).strip(), t[m.end():].lstrip('\n')])

titles, bodies, miss = [], {}, []
for ti, body in items:
    new = RENAME.get(ti, ti)
    if ti in RENAME and new == ti:
        miss.append(ti)
    titles.append(new)
    bodies[new] = bodies.get(new, '') + ('\n\n' if new in bodies else '') + body.strip()
for x in miss:
    print('NOT FOUND', x)

shutil.rmtree(d)
os.makedirs(d)
for i, t in enumerate(titles, 1):
    open('%s/第%03d章-%s.md' % (d, i, t), 'w', encoding='utf-8').write(
        '# 第%03d章 %s\n\n%s\n' % (i, t, bodies[t].rstrip()))

print('chapters', len(glob.glob('%s/*.md' % d)))
print('remaining 新一代:', [t for t in titles if '新一代' in t])
