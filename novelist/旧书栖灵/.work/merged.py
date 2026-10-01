import re, glob, os

ORIG = '/mnt/d/devProject/writer/novelist/旧书栖灵_修改备份/00_原稿/第四部'
CUR = '正文/第四部'

def size(t): return len(re.sub(r'\s', '', t))
def ttl(t):
    m = re.search(r'(?m)^# 第\d+章\s*(.+?)\s*$', t)
    return m.group(1).strip() if m else '?'

o = {}
for f in glob.glob(ORIG + '/*.md'):
    t = open(f, encoding='utf-8').read()
    o[ttl(t)] = (os.path.basename(f), size(t))
c = {}
for f in glob.glob(CUR + '/*.md'):
    t = open(f, encoding='utf-8').read()
    c[ttl(t)] = (os.path.basename(f), size(t))

# merged = current chapter much bigger than any single original, AND
# its title is one of the merged-into titles
MERGED_INTO = ['夏与秋', '冬与完成']
print('确定被合并的（标题即合并产物）:')
for k in MERGED_INTO:
    print('  %-10s %5d' % (k, c[k][1]))
print()
print('原稿有、当前无章名（丢失的12章）:')
for k in o:
    if k not in c:
        print('  %-14s %5d' % (k, o[k][1]))
print()
print('超4000的章，及其原稿对照:')
for k, v in sorted(c.items(), key=lambda x: -x[1][1]):
    if v[1] > 4000:
        orig_sz = o[k][1] if k in o else 0
        delta = v[1] - orig_sz
        tag = '【被撑大 +%d】' % delta if delta > 400 else ''
        print('  %-18s %5d  原稿%5d %s' % (k, v[1], orig_sz, tag))