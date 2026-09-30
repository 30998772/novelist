import re, glob, collections

# Does each chapter actually contain a change of state?
# Signals of real narrative: a decision, a discovery, a loss, a handover,
# something that is different at the end than at the beginning.
DECIDE = re.compile(r'决定|下了.{0,4}决心|答应|拒绝|辞|走|留下|回来|找到了|发现了|不见了|没了|散了|走掉|辞了|退了|接了|交给|点了|烧了|埋了')
REALISE = re.compile(r'忽然明白|这才懂|原来|才发现|这才发现|终于')
STATIC = re.compile(r'她想了想|她点了点头|她笑了笑|她没有说话|沉默了一会儿|点了点头|没有回答')

rows = []
for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    n = len(re.findall(r'[\u4e00-\u9fff]', t))
    dec = len(DECIDE.findall(t))
    rea = len(REALISE.findall(t))
    sta = len(STATIC.findall(t))
    ps = [p.strip() for p in t.split('\n\n') if p.strip()]
    rows.append((dec + rea, sta, n, f, dec, rea))

rows.sort()
print('=== 事件性最弱的 25 章（事件数 / 静态句 / 字数）')
for ev, sta, n, f, dec, rea in rows[:25]:
    print('%2d %2d %5d %-22s 事件%d 醒悟%d' % (ev, sta, n, f.split('/')[-1][:20], dec, rea))
print()
tot_ev = sum(r[0] for r in rows)
tot_sta = sum(r[1] for r in rows)
print('全书 事件句 %d，静态句 %d，比值 %.2f' % (tot_ev, tot_sta, tot_ev / max(1, tot_sta)))
