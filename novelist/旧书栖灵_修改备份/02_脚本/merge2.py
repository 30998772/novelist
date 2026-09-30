import re

targets = [l.strip() for l in open('/tmp/opencode/echo_files.txt', encoding='utf-8').read().split('\n') if l.strip()]

MAXLEN = 58      # never build a paragraph longer than this
MAXFRAG = 4      # never glue more than this many fragments

def cjk(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))

total = 0
for path in targets:
    raw = open(path, encoding='utf-8').read()
    paras = raw.split('\n\n')
    out = []
    buf = ''
    nfrag = 0
    prev_dlg = False

    def flush(b, nf):
        if b:
            out.append(b)
        return '', 0

    for p in paras:
        s = p.strip()
        if not s:
            continue
        hard = s.startswith('#') or s == '---' or s.startswith('---')
        dlg = bool(re.match(r'^[""「『]', s))
        # eligible to continue a run of fragments?
        if (buf and not hard and not dlg and not prev_dlg
                and cjk(s) < 14
                and cjk(buf) + cjk(s) <= MAXLEN
                and nfrag < MAXFRAG):
            buf = buf + s
            nfrag += 1
        else:
            buf, nfrag = flush(buf, nfrag)
            buf, nfrag = s, 1
        prev_dlg = dlg
    buf, nfrag = flush(buf, nfrag)

    new = '\n\n'.join(out)
    if new != raw:
        open(path, 'w', encoding='utf-8').write(new)
        total += len(paras) - len(out)
print('merged', total)
