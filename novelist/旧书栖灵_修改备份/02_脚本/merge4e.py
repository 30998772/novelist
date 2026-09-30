import re, glob, os, shutil

d = '正文/第四部'

items = []
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', t)
    items.append([m.group(2).strip(), t[m.end():].lstrip('\n')])

order = [x[0] for x in items]
bodies = dict(items)

# merge thin chapters that share one thread; the new title names the thread
MERGES = [
    (['重逢的温暖', '种子的传播'], '四月十九'),
    (['陈老的故事', '陈老的回忆'], '陈老'),
    (['年轮的智慧', '时间的礼物'], '年轮精灵'),
    (['落叶的思念', '落叶的归途', '叶落归根'], '落叶精灵'),
    (['苏念的收获', '果实的馈赠', '果实的完成'], '老榕的结果'),
    (['花园的成长', '永恒的循环'], '花园'),
    (['苏晚的传承', '春泥的花园'], '春泥'),
    (['永恒的守护', '约定的开始'], '守与约'),
]

new_titles = []
used = set()
for group, title in MERGES:
    present = [g for g in group if g in bodies]
    if len(present) < 2:
        print('skip', title, present)
        continue
    bodies[title] = '\n\n'.join(bodies[g].strip() for g in present)
    used.update(present)
    new_titles.append(title)

# rebuild the order: replace each merged member with the new title at its position
out_order = []
i = 0
while i < len(order):
    t = order[i]
    if t in used:
        if t == [g for g in dict((x[0], 0) for x in MERGES) and g][0] if False else False:
            pass
        if not any(o for o in out_order if o in [m[1] for m in MERGES] and bodies.get(o)):
            pass
        # insert the merged title only at the first member
        grp = next((m for m in MERGES if t in m[0]), None)
        if grp and t == [g for g in grp[0] if g in bodies][0] and grp[1] not in out_order:
            out_order.append(grp[1])
    else:
        out_order.append(t)
    i += 1

# keep original relative order for everything else, inserting merges at first member
final = []
inserted = set()
for t in order:
    grp = next((m for m in MERGES if t in m[0]), None)
    if grp:
        if grp[1] not in inserted:
            final.append(grp[1])
            inserted.add(grp[1])
    else:
        final.append(t)

shutil.rmtree(d)
os.makedirs(d)
for i, t in enumerate(final, 1):
    open('%s/第%03d章-%s.md' % (d, i, t), 'w', encoding='utf-8').write(
        '# 第%03d章 %s\n\n%s\n' % (i, t, bodies[t].rstrip()))

print('chapters', len(glob.glob('%s/*.md' % d), ))
for t in sorted(bodies):
    if t in [m[1] for m in MERGES]:
        print('  %-12s %5d' % (t, len(re.findall(r'[\u4e00-\u9fff]', bodies[t]))))
