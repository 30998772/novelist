import re, glob, os, shutil

d = '正文/第四部'
MERGE = ['春天的希望', '夏天的热情', '秋天的收获', '冬天的沉淀']

order, bodies = [], {}
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', t)
    title = m.group(2).strip()
    body = t[m.end():].lstrip('\n')
    bodies[title] = body
    order.append(title)
print('read', len(order))

# append the three middle seasons onto 四季的完成, keep 春天 as its own opener
idx = order.index('四季的完成')
merged = bodies['春天的希望'].rstrip() + '\n\n'
for s in ['夏天的热情', '秋天的收获', '冬天的沉淀']:
    merged += bodies[s].rstrip() + '\n\n'
merged += bodies['四季的完成'].lstrip()
bodies['四季的完成'] = merged

new_order = [t for t in order if t not in ('春天的希望', '夏天的热情', '秋天的收获', '冬天的沉淀')]

shutil.rmtree(d)
os.makedirs(d)
for i, title in enumerate(new_order, 1):
    open('%s/第%03d章-%s.md' % (d, i, title), 'w', encoding='utf-8').write(
        '# 第%03d章 %s\n\n%s\n' % (i, title, bodies[title].rstrip()))

print('written', len(glob.glob('%s/*.md' % d)))
for i, t in enumerate(new_order, 1):
    if t in MERGE or t == '四季的完成':
        print('  ', i, t)
