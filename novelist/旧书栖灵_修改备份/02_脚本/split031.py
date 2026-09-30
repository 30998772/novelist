import re, os, shutil, glob

d = '正文/第一部'
src = '%s/第031章-执念终有归处.md' % d
t = open(src, encoding='utf-8').read()
paras = [p.strip() for p in t.split('\n\n') if p.strip()]
paras = [p for p in paras if not p.startswith('# 第030章')]
for i, p in enumerate(paras):
    if p.endswith('亮了起来，圆满了起来。'):
        paras[i] = p[:-len('亮了起来，圆满了起来。')].rstrip()

# 031 keeps 茶话会开场; 032 takes the round of stories onward
idx = next(i for i, p in enumerate(paras) if p.startswith('灯灵等的是一封信'))

a = '# 第031章 执念终有归处\n\n' + '\n\n'.join(paras[:idx]).rstrip() + '\n'
b = '# 第032章 各述所等\n\n' + '\n\n'.join(paras[idx:]).rstrip() + '\n'

os.makedirs('/tmp/opencode/split3', exist_ok=True)
open('/tmp/opencode/split3/031.md', 'w', encoding='utf-8').write(a)
open('/tmp/opencode/split3/032.md', 'w', encoding='utf-8').write(b)

def wc(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))
print('031', wc(a), '| 032', wc(b))
