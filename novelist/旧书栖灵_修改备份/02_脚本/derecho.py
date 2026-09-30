import re

targets = [l.strip() for l in open('/tmp/opencode/echo_files.txt', encoding='utf-8').read().split('\n') if l.strip()]

total = 0
for path in targets:
    raw = open(path, encoding='utf-8').read()
    paras = [p for p in raw.split('\n\n')]
    out = []
    removed = 0
    i = 0
    while i < len(paras):
        p = paras[i].strip()
        m = re.fullmatch(r'([""])(.{1,16})\1', p)
        if m:
            core = m.group(2)
            j = i + 1
            run = 0
            while j < len(paras):
                s2 = paras[j].strip()
                m2 = re.fullmatch(r'([""])(.{1,16})\1', s2)
                if not m2:
                    break
                c2 = m2.group(2)
                if c2 == core or c2 == core[1:] or c2 == '您' + core[1:] or c2 == '我' + core[1:]:
                    run += 1
                    j += 1
                else:
                    break
            if run:
                out.append(paras[i])
                removed += run
                i = j
                continue
        out.append(paras[i])
        i += 1
    if removed:
        open(path, 'w', encoding='utf-8').write('\n\n'.join(out))
        total += removed
        print(removed, path.split('/')[-1])
print('total removed', total)
