import re, glob
pat = re.compile(r'不知道是说给谁听的。也许是说给[^。]{2,60}。'
                 r'(?:(?:她|他)(?:接着|继续)?踩着楼梯(?:上楼| downstairs|下楼)，'
                 r'(?:脚步声|脚步)很轻，楼梯的吱呀声反而比(?:脚步声|脚步)还响。?)?'
                 .replace(' downstairs', '下楼'))
n = 0
for f in sorted(glob.glob('正文/第六部/*.md')):
    t = open(f, encoding='utf-8').read()
    o = t
    t = pat.sub('', t)
    if t != o:
        t = re.sub(r'[，、]\s*([。！？])', r'\1', t)
        t = re.sub(r'\n{3,}', '\n\n', t)
        open(f, 'w', encoding='utf-8').write(t)
        n += 1
print('cleaned', n)
