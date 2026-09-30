import re, glob, collections

# sentence-level recycling across chapters
sent = collections.defaultdict(list)
for f in sorted(glob.glob('正文/第二部/*.md')):
    t = open(f, encoding='utf-8').read()
    for s in re.split(r'(?<=[。！？])', t):
        s = s.strip()
        if 12 <= len(s) <= 60 and '“' not in s and '"' not in s and '「' not in s:
            sent[s].append(f)

rep = {s: fs for s, fs in sent.items() if len(fs) > 1}
print('recycled sentences:', len(rep), 'instances', sum(len(v) for v in rep.values()))
removed = 0
for s, fs in rep.items():
    for f in fs[1:]:
        t = open(f, encoding='utf-8').read()
        nt = t.replace(s, '', 1)
        if nt != t:
            nt = re.sub(r'[，、]\s*([。！？])', r'\1', nt)
            nt = re.sub(r'\n{3,}', '\n\n', nt)
            open(f, 'w', encoding='utf-8').write(nt)
            removed += 1
print('copies removed', removed)
for s, fs in sorted(rep.items(), key=lambda kv: -len(kv[1]))[:12]:
    print(len(fs), s[:56])
