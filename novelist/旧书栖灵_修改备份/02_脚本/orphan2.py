import re, glob

bad = []
for f in sorted(glob.glob('正文/*/*.md')):
    lines = open(f, encoding='utf-8').read().split('\n')
    n = len(lines)
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        if len(s) > 45:
            continue
        if s[-1] in '。！？」）"’。，、：':
            continue
        if s[0] in '-*0123456789':
            continue
        # look ahead: if next non-empty line starts a quote, this is a legit lead-in
        j = i + 1
        while j < n and not lines[j].strip():
            j += 1
        nxt = lines[j].strip() if j < n else ''
        if nxt[:1] in '「"“':
            continue
        bad.append((f, i + 1, s))

print('TRUE outline leftovers:', len(bad))
for f, i, s in bad:
    print(f.split('/')[-1], i, '|', s)
