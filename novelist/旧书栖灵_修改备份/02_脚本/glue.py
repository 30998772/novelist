import re, glob

pat = re.compile(r'((?:看着|盯着|瞅着|打量着|端详着|望着)[^。！？\n，]{0,10})((?:她|他|陆栖)(?:看着|盯着|瞅着|打量着|端详着|望着))')

for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    for m in pat.finditer(t):
        print(f.split('/')[-1], '||', repr(t[max(0,m.start()-25):m.end()+25]))
