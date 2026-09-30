import re, glob, collections

# 1) "不是X。是Y。" / "不是X，是Y。" self-correction where the first half is
#    an abandoned phrasing -> keep only Y.
# Only collapse when X and Y are near-restatements (share a char) or X is a
# bare negation of a feeling word. Otherwise leave the real contrast alone.
NEG = re.compile(r'不是([^。！？，]{2,8})[，。](?:而是)?是([^。！？]{2,14})。')

def same_domain(x, y):
    return bool(set(x) & set(y))

report = []
for f in sorted(glob.glob('正文/第一部/*.md')):
    t = open(f, encoding='utf-8').read()
    hits = NEG.findall(t)
    if hits:
        report.append((f.split('/')[-1][:16], hits))

print('不是X，是Y instances in 第一部:', sum(len(h) for _, h in report))
for n, h in report[:30]:
    for x, y in h:
        print('  %-16s %s || %s' % (n, x, y))
