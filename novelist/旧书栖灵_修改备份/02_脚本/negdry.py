import re, glob, collections

# "不是X，是Y" where X and Y are near-synonyms or the clause is a
# self-correction of a previous clause -> collapse to just Y.
# Only touch the high-confidence shape: 不是<2-6字>，是<same-length>。
pat = re.compile(r'不是([^。！？，]{2,6})，(?:而)?是([^。！？]{2,8})。')

changed = 0
samples = []
for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    o = t
    def rep(m):
        global changed
        x, y = m.group(1), m.group(2)
        # skip if it reads as a genuine contrast (different domains)
        return m.group()
    # Instead: only collapse the exact rhetorical frame
    # "不是X，是Y。" -> "是Y。"  ONLY when the preceding clause already said Y
    t2 = re.sub(r'不是([^。！？，]{2,6})，(?:而)?是([^。！？]{2,10})。', rep, t)
    if t2 != o:
        open(f, 'w', encoding='utf-8').write(t2)
        changed += 1
print('dry-run only, changed', changed)
