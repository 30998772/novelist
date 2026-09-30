import re, glob, os, shutil

d = '正文/第一部'

# 1) fix the dangling lead-in left at the end of the first half
p = '/tmp/opencode/split2/029.md'
t = open(p, encoding='utf-8').read()
t = t.replace('\n\n走到古籍区，他把灯凑近印章灵\n', '\n')
open(p, 'w', encoding='utf-8').write(t)
print('029 now', len(re.findall(r'[\u4e00-\u9fff]', t)))

# 2) push 030..061 up by one so the new chapter can take 030
for n in range(61, 29, -1):
    old = glob.glob('%s/第%03d章-*.md' % (d, n))
    assert len(old) == 1, (n, old)
    base = os.path.basename(old[0])
    title = base.split('-', 1)[1][:-3]
    os.rename(old[0], '%s/第%03d章-%s.md' % (d, n + 1, title))

# 3) install
shutil.copy('/tmp/opencode/split2/029.md', '%s/第029章-岁岁平安册.md' % d)
shutil.copy('/tmp/opencode/split2/030.md', '%s/第030章-提灯巡馆.md' % d)
print('installed')
