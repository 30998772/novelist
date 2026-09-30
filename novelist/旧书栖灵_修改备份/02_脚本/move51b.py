import re, glob, os

d = '正文/第一部'
files = sorted(glob.glob('%s/*.md' % d))
print('before', len(files))

# 1) repair the stray file: 晚风年年都来 should be 063
src063='%s/第062章-晚风年年都来.md' % d
if os.path.exists(src063): os.rename(src063,'%s/第063章-晚风年年都来.md' % d)

# 2) shift 052..063 -> 051..062 (descending)
for n in range(63, 51, -1):
    old = glob.glob('%s/第%03d章-*.md' % (d, n))
    assert len(old) == 1, (n, old)
    ti = os.path.basename(old[0]).split('-', 1)[1][:-3]
    os.rename(old[0], '%s/第%03d章-%s.md' % (d, n - 1, ti))

# 3) 交钥匙的春天 becomes the epilogue
src = glob.glob('%s/第051章-*.md' % d)[0]
ti = os.path.basename(src).split('-', 1)[1][:-3]
os.rename(src, '%s/第064章-%s.md' % (d, ti))

# 4) align every in-file heading with its filename
for f in sorted(glob.glob('%s/*.md' % d)):
    fn = int(re.match(r'第(\d+)章', os.path.basename(f)).group(1))
    t = open(f, encoding='utf-8').read()
    m = re.search(r'^# 第(\d+)章(.*)$', t, re.M)
    if m and int(m.group(1)) != fn:
        t = t[:m.start()] + '# 第%03d章%s' % (fn, m.group(2)) + t[m.end():]
        open(f, 'w', encoding='utf-8').write(t)

print('after', len(glob.glob('%s/*.md' % d)))
bad = [os.path.basename(f) for f in sorted(glob.glob('%s/*.md' % d))
       if int(re.match(r'第(\d+)章', os.path.basename(f)).group(1))
       != int(re.search(r'^# 第(\d+)章', open(f, encoding='utf-8').read(), re.M).group(1))]
print('head mismatch', len(bad))
