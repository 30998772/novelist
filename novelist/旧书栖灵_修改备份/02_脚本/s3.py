import re, glob, collections

# Recycled sentence inventory for 第三部 — these are the machine tells.
sent = collections.defaultdict(list)
for f in sorted(glob.glob('正文/第三部/*.md')):
    t = open(f, encoding='utf-8').read()
    for s in re.split(r'(?<=[。！？])', t):
        s = s.strip()
        if 10 <= len(s) <= 60 and '“' not in s and '"' not in s and '「' not in s:
            sent[s].append(f)

rep = {s: fs for s, fs in sent.items() if len(fs) > 1}
print('recycled sentences:', len(rep), 'instances', sum(len(v) for v in rep.values()))
for s, fs in sorted(rep.items(), key=lambda kv: -len(kv[1]))[:30]:
    print(len(fs), [x.split('/')[-1][:12] for x in fs][:3])
    print('   ', s[:60])
