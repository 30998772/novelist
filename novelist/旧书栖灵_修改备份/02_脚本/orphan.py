import re, glob

# orphan fragments: short standalone lines that are not dialogue, not headings,
# and end without sentence-final punctuation (leftover outline text)
orphans = []
for f in sorted(glob.glob('正文/*/*.md')):
    lines = open(f, encoding='utf-8').read().split('\n')
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if not s or s.startswith('#') or s.startswith('「') or s.startswith('"') or s.startswith('“'):
            continue
        if len(s) > 40:
            continue
        if s[-1] in '。！？」）"’':
            continue
        # must not be a quoted continuation or a list
        if s.startswith('-') or s.startswith('*') or s[0].isdigit():
            continue
        orphans.append((f, i, s))

print('orphan fragments:', len(orphans))
for f, i, s in orphans:
    print(f.split('/')[-1], i, '|', s)
