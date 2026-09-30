import re, glob, collections

# same scene told twice with only the speaker's name changed
blocks = []
for f in sorted(glob.glob('正文/*/*.md')):
    part = f.split('/')[1]
    t = open(f, encoding='utf-8').read()
    for p in t.split('\n\n'):
        p = p.strip()
        if len(p) < 30:
            continue
        # normalise: strip all person names so only the wording remains
        s = re.sub(r'陆栖|林越|苏晚|苏晚晴|林晓颂|方小远|方知远|周小明|周明远|陈立夏|苏念|顾念|李晓禾|阿棠|江望归|沈明远', 'X', p)
        s = re.sub(r'[^X一-鿿]', '', s)
        if len(s) >= 24:
            blocks.append((s, f, p))

by = collections.defaultdict(list)
for s, f, p in blocks:
    by[s].append((f, p))

hits = [(s, v) for s, v in by.items() if len(v) > 1]
print('去掉人名后完全相同的段落:', len(hits))
for s, v in hits:
    fs = set(x[0] for x in v)
    if len(fs) > 1:
        print('---', [x[0].split('/')[-1][:18] for x in v][:3])
        print('   ', v[0][1][:78])
