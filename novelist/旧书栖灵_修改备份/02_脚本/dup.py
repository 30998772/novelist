import re, glob, collections

# Detect draft-interleave: a paragraph that restates the same scene as its
# neighbour, signalled by shared rare nouns within a short window.
for f in ['正文/第一部/第029章-岁岁平安册.md',
          '正文/第一部/第030章-执念终有归处.md',
          '正文/第四部/第066章-明年春天之前.md',
          '正文/第四部/第069章-护花的约定.md']:
    t = open(f, encoding='utf-8').read()
    paras = [p.strip() for p in t.split('\n\n') if p.strip()]
    print('===', f, 'paras', len(paras), 'chars', len(re.findall(r'[\u4e00-\u9fff]', t)))
    # find near-duplicate paragraph pairs via character 5-gram overlap
    def grams(s):
        s = re.sub(r'[^一-鿿]', '', s)
        return set(s[i:i+4] for i in range(max(0, len(s)-3)))
    g = [grams(p) for p in paras]
    for i in range(len(paras)-1):
        if not g[i] or not g[i+1]:
            continue
        j = len(g[i] & g[i+1]) / min(len(g[i]), len(g[i+1]))
        if j > 0.42:
            print('  DUPPAIR %.2f' % j)
            print('    A:', paras[i][:70])
            print('    B:', paras[i+1][:70])
