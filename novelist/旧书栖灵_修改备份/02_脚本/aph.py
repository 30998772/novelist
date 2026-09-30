import re, glob, collections

# exact aphoristic sentences that repeat verbatim across files
sent = collections.defaultdict(list)
for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    for s in re.split(r'(?<=[。！？])', t):
        s = s.strip()
        # short declarative aphorisms, no quotes, no names-heavy
        if 8 <= len(s) <= 34 and '“' not in s and '"' not in s and '：' not in s:
            sent[s].append(f)

rep = {s: fs for s, fs in sent.items() if len(fs) >= 3}
print('repeated >=3x:', len(rep))
for s, fs in sorted(rep.items(), key=lambda kv: -len(kv[1]))[:60]:
    print(len(fs), s)
