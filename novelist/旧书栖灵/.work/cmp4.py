import re, glob, os

ORIG = '/mnt/d/devProject/writer/novelist/旧书栖灵_修改备份/00_原稿/第四部'
CUR = '正文/第四部'

def size(t): return len(re.sub(r'\s', '', t))
def title(t):
    m = re.search(r'(?m)^# 第\d+章\s*(.+?)\s*$', t)
    return m.group(1).strip() if m else '?'

orig = []
for f in sorted(glob.glob(ORIG + '/*.md')):
    t = open(f, encoding='utf-8').read()
    orig.append((os.path.basename(f), title(t), size(t)))

cur = []
for f in sorted(glob.glob(CUR + '/*.md')):
    t = open(f, encoding='utf-8').read()
    cur.append((os.path.basename(f), title(t), size(t)))

print('原稿 %d 章 / %d 字符' % (len(orig), sum(x[2] for x in orig)))
print('当前 %d 章 / %d 字符' % (len(cur), sum(x[2] for x in cur)))
print()

ot = [x[1] for x in orig]
ct = [x[1] for x in cur]

# titles present in orig but not current
lost = [t for t in ot if t not in ct]
gained = [t for t in ct if t not in ot]
print('原稿有、当前没有的章名 (%d):' % len(lost))
for t in lost: print('   ', t)
print()
print('当前有、原稿没有的章名 (%d):' % len(gained))
for t in gained: print('   ', t)