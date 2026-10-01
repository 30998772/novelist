import re
f = '正文/第四部/第061章-春泥的花园.md'
t = open(f, encoding='utf-8').read()
print('原', len(re.sub(r'\s', '', t)), '字符,', len([l for l in t.split('\n') if l.strip()]), '行')
L = [l.strip() for l in t.split('\n') if l.strip()]
for l in L[:60]:
    if not l.startswith('"'):
        print(' ', l[:88])