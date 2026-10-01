import re, glob, os

ORIG = '/mnt/d/devProject/writer/novelist/旧书栖灵_修改备份/00_原稿/第四部'
CUR = '正文/第四部'

def size(t): return len(re.sub(r'\s', '', t))
def paras(t):
    return [p.strip() for p in re.split(r'\n+', t) if p.strip()]
def title(t):
    m = re.search(r'(?m)^# 第\d+章\s*(.+?)\s*$', t)
    return m.group(1).strip() if m else '?'

def load(d):
    out = []
    for f in sorted(glob.glob(d + '/*.md')):
        t = open(f, encoding='utf-8').read()
        out.append((f, title(t), t))
    return out

orig = load(ORIG)
cur = load(CUR)

def ngrams(t, n=12):
    s = re.sub(r'[^一-鿿]', '', t)
    return set(s[i:i+n] for i in range(0, max(1, len(s)-n), 6))

# For each current chapter, find which original chapters it contains
print('当前章 -> 包含的原稿章（按内容重合度）')
print()
for cf, ct_, ctext in cur:
    cn = ngrams(ctext)
    hits = []
    for of, ot, otext in orig:
        on = ngrams(otext)
        if not on: continue
        r = len(cn & on) / len(on)
        if r > 0.30:
            hits.append((r, ot))
    hits.sort(reverse=True)
    if len(hits) >= 2 or (hits and hits[0][0] < 0.92):
        print('%-22s %5d字符' % (ct_, size(ctext)))
        for r, ot in hits:
            print('      %.0f%%  <- %s' % (r*100, ot))
        print()