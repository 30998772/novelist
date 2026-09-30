import re, glob

# In 第三部 the chapters end with a slogan stack: a definition, then
# "这就是X的力量", then "不是A，而是B", then "从来如此".
# Cut the slogans; keep any concrete image that precedes them.

SLOGAN = re.compile(
    r'[^。\n]{0,30}这就是[^。\n]{1,10}的力量。[^\n]{0,4}\n?'
    r'(?:不是[^。\n]{1,20}[，。][^。\n]{1,20}。\n?)?'
    r'(?:风里[^。\n]{4,40}。\n?)?'
    r'[^。\n]{0,20}从来如此。')

n = 0
for f in sorted(glob.glob('正文/第三部/*.md')):
    t = open(f, encoding='utf-8').read()
    o = t
    t = SLOGAN.sub('', t)
    # the bare "X会永远存在" closers
    t = re.sub(r'\n[^。\n]{0,14}会永远存在。\n', '\n', t)
    t = re.sub(r'[，、]\s*([。！？])', r'\1', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    t = re.sub(r'(?m)^---\s*$', '', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    if t != o:
        open(f, 'w', encoding='utf-8').write(t)
        n += 1
print('files touched', n)
