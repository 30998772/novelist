import re, glob

d = '正文/第四部'
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    ttl = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', t).group(2).strip()
    body = t[re.search(r'(?m)^# 第\d+章.*$', t).end():].lstrip('\n')
    ps = [p.strip() for p in body.split('\n\n') if p.strip()]
    if not ps:
        continue
    first = ps[0]
    if re.match(r'^[一二三四五六七八九十\d]+月[一二三四五六七八九十\d]+日?，?', first):
        print('--- %s %s' % (re.search(r'第(\d+)章', f).group(1), ttl))
        for p in ps[:3]:
            print('    ', p[:78])
