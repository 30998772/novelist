import re, glob, collections

# A真乒乓段: >=8 consecutive quote-only lines AND no speaker tag in the run.
# Speaker tags: 某某说/某某道/某某问 etc. appear inside the line.
Q = re.compile(r'^["“].{1,30}["”]?[。？]?$')
TAG = re.compile(r'(说|道|问|答|喊|叫|笑|想|念|回头|站起来|看了看|摇了摇头)')

rows = []
for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
    for f in glob.glob('正文/%s/*.md' % d):
        t = open(f, encoding='utf-8').read()
        L = [l.strip() for l in t.split('\n') if l.strip()]
        tot = 0
        runs = 0
        i = 0
        while i < len(L):
            if Q.match(L[i]):
                j = i
                while j < len(L) and Q.match(L[j]):
                    j += 1
                n = j - i
                if n >= 8:
                    has_tag = any(TAG.search(x) for x in L[i:j])
                    if not has_tag:
                        runs += 1
                        tot += n
                i = j
            else:
                i += 1
        if runs:
            sz = len(re.sub(r'\s', '', t))
            rows.append((tot, runs, sz, f))

rows.sort(reverse=True)
print('真乒乓（连续>=8行无归属对白）')
print('行数  段数  总字符  文件')
for tot, runs, sz, f in rows[:20]:
    print('%4d %5d %7d  %s' % (tot, runs, sz, f.split('/')[-1][:26]))
print()
print('受影响的章：%d  总行数 %d  总字符占比 %.1f%%' % (
    len(rows), sum(r[0] for r in rows),
    sum(r[0] for r in rows) / sum(len(re.sub(r'\s','',open(f,encoding='utf-8').read()))
        for f in glob.glob('正文/*/*.md')) * 100))