import re, glob, os, shutil

d = '正文/第一部'
src = '%s/第029章-岁岁平安册.md' % d
t = open(src, encoding='utf-8').read()
paras = [p.strip() for p in t.split('\n\n') if p.strip()]
paras = [p for p in paras if not p.startswith('# 第029章')]

idx = next(i for i, p in enumerate(paras) if p.startswith('印章灵正蹲在一本线装书的封面上'))

a = '# 第029章 岁岁平安册\n\n' + '\n\n'.join(paras[:idx]).rstrip() + '\n'
b = '# 第030章 提灯巡馆\n\n' + '\n\n'.join(paras[idx:]).rstrip() + '\n'

os.makedirs('/tmp/opencode/split2', exist_ok=True)
open('/tmp/opencode/split2/029.md', 'w', encoding='utf-8').write(a)
open('/tmp/opencode/split2/030.md', 'w', encoding='utf-8').write(b)

def wc(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))
print('029', wc(a))
print('030', wc(b))
