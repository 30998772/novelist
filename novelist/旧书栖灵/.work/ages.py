import re, glob

# Canonical ages for 第四部 (总纲: 陆栖 52-60)
#   陆栖 54   方知远 59 (他说过"明年六十")   苏晚 27 (005里21岁, 六年过去)
#   周明远 67 (1983年26岁)   苏念 26
AGE = {
    '陆栖': ('五十一', '五十四'),
    '苏晚': ('五十一', '二十七'),
    '苏念': ('五十一', '二十六'),
    '方知远': ('五十一', '五十九'),
}

ORDER = ['周明远', '方知远', '陆栖', '苏念', '苏晚']

changed = {}
for f in sorted(glob.glob('正文/第四部/*.md')):
    t = open(f, encoding='utf-8').read()
    out = t
    n = 0
    for m in re.finditer(r'五十一', t):
        # nearest speaker name before this point, within a reasonable window
        i = m.start()
        who = None
        for d in range(i, max(0, i - 420), -1):
            hit = None
            for nm in ORDER:
                p = t.rfind(nm, d - 25, d + 25)
                if p >= 0 and (hit is None or p > hit[0]):
                    hit = (p, nm)
            if hit:
                who = hit[1]
                break
        if who in AGE:
            old, new = AGE[who]
            out = out[:i] + new + out[i + len(old):]
            t2 = t[:i] + new + t[i + 3:]      # keep offsets in sync
            t = t2
            n += 1
    if out != open(f, encoding='utf-8').read():
        open(f, 'w', encoding='utf-8').write(out)
        changed[f.split('/')[-1]] = n

for k, v in changed.items():
    print('%-28s %d' % (k, v))
print('总改', sum(changed.values()))