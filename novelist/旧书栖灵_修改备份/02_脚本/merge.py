import re

targets = [l.strip() for l in open('/tmp/opencode/echo_files.txt', encoding='utf-8').read().split('\n') if l.strip()]

def is_dialogue(p):
    s = p.strip()
    return bool(re.match(r'^[""「『]', s))

def is_long(p):
    return len(re.sub(r'[^一-鿿]', '', p)) >= 22

total = 0
for path in targets:
    raw = open(path, encoding='utf-8').read()
    paras = raw.split('\n\n')
    out = []
    buf = ''
    for p in paras:
        s = p.strip()
        if not s:
            continue
        # a short narrative fragment continues the current buffer
        if buf and not is_dialogue(s) and not is_long(s) and not s.startswith('#'):
            buf = buf + s
        else:
            if buf:
                out.append(buf)
            buf = s
    if buf:
        out.append(buf)
    new = '\n\n'.join(out)
    if new != raw:
        open(path, 'w', encoding='utf-8').write(new)
        n = len(paras) - len(out)
        total += n
        print(n, path.split('/')[-1])
print('paragraphs merged', total)
