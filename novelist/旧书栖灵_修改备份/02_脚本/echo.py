import re, glob

# pathology: consecutive dialogue lines where one echoes the other verbatim
rows = []
for f in sorted(glob.glob('正文/*/*.md')):
    lines = [l.strip() for l in open(f, encoding='utf-8').read().split('\n')]
    dl = [l for l in lines if re.fullmatch(r'[""].{1,14}[""]', l)]
    echo = 0
    for i in range(len(dl) - 1):
        a = re.sub(r'[""]', '', dl[i])
        b = re.sub(r'[""]', '', dl[i + 1])
        if a == b:
            echo += 1
    # also: ultra-fragmented (median line length very low)
    body = [l for l in lines[1:] if l]
    short = sum(1 for l in body if len(l) <= 6)
    frag = short / max(1, len(body))
    if echo >= 5 or frag > 0.55:
        rows.append((echo, round(frag, 2), len(body), f))

rows.sort(reverse=True)
print('chapters with echo-fragmentation:', len(rows))
for e, fr, n, f in rows:
    print(e, fr, n, f)
