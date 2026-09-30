import re, glob, os, shutil

src = '正文/第一部/第030章-执念终有归处.md'
t = open(src, encoding='utf-8').read()
paras = [p.strip() for p in t.split('\n\n') if p.strip()]

# locate the split anchor
idx = next(i for i, p in enumerate(paras)
           if p.startswith('顾松年把陆栖留下来的时候'))

head = paras[:idx]
tail = paras[idx:]

# strip the original heading from head, and give each part its own
head = [p for p in head if not p.startswith('# 第030章')]
tail = [p for p in tail if not p.startswith('# 第030章')]

a = '# 第030章 执念终有归处\n\n' + '\n\n'.join(head).rstrip() + '\n'
b = '# 第031章 交灯\n\n' + '\n\n'.join(tail).rstrip() + '\n'

os.makedirs('/tmp/opencode/split', exist_ok=True)
open('/tmp/opencode/split/030.md', 'w', encoding='utf-8').write(a)
open('/tmp/opencode/split/031.md', 'w', encoding='utf-8').write(b)

def wc(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))
print('030', wc(a), 'paras', len(head))
print('031', wc(b), 'paras', len(tail))
