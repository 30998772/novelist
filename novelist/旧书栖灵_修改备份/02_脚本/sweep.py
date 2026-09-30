import re, glob, collections

# Systematic residual-tic sweep, book-wide.
CHECKS = [
 ('否定-修正',   r'(?<!["「])不是[^。！？，\n"]{1,10}[，。](?:而)?是[^。！？\n"]{1,14}。'),
 ('不只是',     r'不只是[^。！？，\n]{1,20}[，。][^。！？\n]{0,4}是[^。！？\n]{1,20}'),
 ('格言',       r'(?<!["「])(?:从来如此|这就是[^。\n]{1,10}的力量|[^。\n]{1,10}会永远存在)[。]'),
 ('宣布情绪',   r'(?<!["「])她忽然觉得|她终于明白|她明白了'),
 ('拟人回应',   r'像(?:是)?在回应'),
 ('像是在说',   r'像(?:是)?在说|像(?:是)?在告诉'),
 ('叠喻',       r'，?像[^，。！？\n]{2,14}[，]?像是'),
 ('小小的',     r'小小的'),
]

rows = []
for d in ['第一部', '第二部', '第三部', '第四部', '第五部', '第六部']:
    for f in sorted(glob.glob('正文/%s/*.md' % d)):
        t = open(f, encoding='utf-8').read()
        h = {}
        for name, pat in CHECKS:
            c = len(re.findall(pat, t))
            if c:
                h[name] = c
        rows.append((sum(h.values()), d, f, h))

rows.sort(reverse=True)
print('=== 残留 AI 特征最重的 25 章')
for s, d, f, h in rows[:25]:
    print('%-3d %-4s %-22s %s' % (s, d, f.split('/')[-1][:20], h))
print()
tot = collections.Counter()
for s, d, f, h in rows:
    for k, v in h.items():
        tot[k] += v
print('全书合计:', dict(tot))
