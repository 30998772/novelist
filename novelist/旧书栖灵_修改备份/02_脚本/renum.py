import re, glob, os, shutil

d = '正文/第一部'

# 1) renumber existing 060 -> 061 down to 031 -> 032 (descending to avoid clashes)
for n in range(60, 30, -1):
    old = glob.glob('%s/第%03d章-*.md' % (d, n))
    assert len(old) == 1, (n, old)
    src = old[0]
    base = os.path.basename(src)
    title = base.split('-', 1)[1][:-3]
    dst = '%s/第%03d章-%s.md' % (d, n + 1, title)
    os.rename(src, dst)
    print('renamed', base, '->', os.path.basename(dst))

# 2) install the two split halves
shutil.copy('/tmp/opencode/split/030.md', '%s/第030章-执念终有归处.md' % d)
shutil.copy('/tmp/opencode/split/031.md', '%s/第031章-交灯.md' % d)
print('installed split halves')
