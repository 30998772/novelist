import re, glob

# 1) the stock closing line
END = [
 '不知道是说给谁听的。也许是说给这栋楼，也许是说给楼里的每一个人，也许是说给楼里的每一本书。',
 '不知道是说给谁听的。也许是说给这栋楼，也许是说给楼里的每一个人，也许是说给楼里的每一卷书。',
]
# 2) the tree-as-sage metaphor
TREE = [
 '像一个看透了世事的老人，不急不躁。',
 '像一个看透了世事的老人',
]
# 3) "心里暖一下" filler
WARM = [
 '她每次打扫卫生的时候都会看它一眼，心里暖一下。',
]

n = 0
for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    o = t
    for e in END:
        t = t.replace(e, '')
    for x in TREE:
        t = t.replace(x, '')
    for x in WARM:
        t = t.replace(x, '')
    t = re.sub(r'\n{3,}', '\n\n', t)
    t = re.sub(r'[ \t]+\n', '\n', t)
    if t != o:
        open(f, 'w', encoding='utf-8').write(t)
        n += 1
print('files touched', n)
