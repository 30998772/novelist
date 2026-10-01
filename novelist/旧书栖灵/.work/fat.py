import re, glob, collections

def size(t): return len(re.sub(r'\s', '', t))
def han(t): return len(re.findall(r'[\u4e00-\u9fff]', t))

Q = re.compile(r'(?m)^["“].{1,26}["”]?[。？]?\s*$')

stats = collections.Counter()
tot = 0
dlg_lines = 0
dlg_chars = 0
all_lines = 0

for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
    for f in glob.glob('正文/%s/*.md' % d):
        t = open(f, encoding='utf-8').read()
        tot += size(t)
        for l in t.split('\n'):
            l = l.strip()
            if not l: continue
            all_lines += 1
            if Q.match(l):
                dlg_lines += 1
                dlg_chars += size(l)

print('总字符            %d' % tot)
print('非空行            %d' % all_lines)
print('独立成段的对白行  %d  (%.0f%% of lines)' % (dlg_lines, dlg_lines*100//all_lines))
print('对白行占的字符    %d  (%.1f%% of total)' % (dlg_chars, dlg_chars*100.0/tot))
print()

# 乒乓对白：连续 >=6 行的对白段
def runs(t):
    lines = [l.strip() for l in t.split('\n') if l.strip()]
    out = []
    i = 0
    while i < len(lines):
        if Q.match(lines[i]):
            j = i
            while j < len(lines) and Q.match(lines[j]): j += 1
            if j - i >= 6: out.append((i, j - i))
            i = j
        else:
            i += 1
    return out

r_tot = 0
r_chars = 0
chapters_with = 0
for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
    for f in glob.glob('正文/%s/*.md' % d):
        t = open(f, encoding='utf-8').read()
        rs = runs(t)
        if rs:
            chapters_with += 1
            lines = [l.strip() for l in t.split('\n') if l.strip()]
            for st, n in rs:
                r_tot += n
                r_chars += sum(size(x) for x in lines[st:st+n])
print('含乒乓段的章      %d / 411' % chapters_with)
print('乒乓段内的行数    %d' % r_tot)
print('乒乓段占的字符    %d  (%.1f%% of total)' % (r_chars, r_chars*100.0/tot))