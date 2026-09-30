import re, glob

# The stock three-part ending: a "风里带着…" line, then
# "那些X会永远存在。在A里，在B里，在每一个C里。"
PAT = re.compile(
    r'\n*风里带着[^。\n]{4,50}。[^\n]{0,4}\n*'
    r'[^。\n]{0,12}那些[^。\n]{1,8}会永远存在。在[^。\n]{2,40}。'
    r'\s*(?:---)?\s*')

n = 0
for f in sorted(glob.glob('正文/第三部/*.md')):
    t = open(f, encoding='utf-8').read()
    o = t
    t = PAT.sub('\n\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t).rstrip() + '\n'
    if t != o:
        open(f, 'w', encoding='utf-8').write(t)
        n += 1
        print(n, f.split('/')[-1][:18])
print('done', n)
