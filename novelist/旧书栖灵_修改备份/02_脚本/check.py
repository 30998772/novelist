import re, glob, collections

files = sorted(glob.glob('正文/*/*.md'))
issues = collections.defaultdict(list)

for f in files:
    t = open(f, encoding='utf-8').read()
    name = f.split('/')[-1]
    if '\n\n\n' in t:
        issues['blank-gap'].append(name)
    if t.count('"') % 2:
        issues['odd-quote'].append(name)
    if re.search(r'[，。、；：]{2,}', t):
        issues['punct-run'].append(name)
    # two identical verbs glued together
    for m in re.finditer(r'(?:看着|盯着|瞅着|打量着|端详着|望着)[^。！？\n]{0,8}(?:看着|盯着|瞅着|打量着|端详着|望着)', t):
        issues['glued-verb'].append(name + ' :: ' + m.group())
    # subject repeated
    for m in re.finditer(r'(她|他)[\u4e00-\u9fff]{0,4}\1', t):
        issues['dup-subject'].append(name + ' :: ' + m.group())
    # banned AI constructions
    for p in ['不是真的看', '打量着那扇门', '端详着那本书', '直到书页泛黄',
              '直到门轴', '直到灯芯结出', '直到天色暗下来', '直到叶子落尽',
              '名字是根', '，Unt', '，只是']:
        if p in t:
            issues['banned:' + p].append(name)

for k, v in sorted(issues.items()):
    if k in ('banned:，只是',):
        continue
    print('==', k, len(v))
    for x in v[:8]:
        print('   ', x)
print('total chapters', len(files))
