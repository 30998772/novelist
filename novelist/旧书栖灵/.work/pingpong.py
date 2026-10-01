import re, glob

# Detect ping-pong: a run of alternating short quotes where the CONTENT
# keeps restating. Report candidate runs so I can cut by hand, not blind.

def size(t): return len(re.sub(r'\s', '', t))

def load(d):
    fs = sorted(glob.glob('正文/%s/*.md' % d))
    return fs

PAT = re.compile(r'(?m)^[“"].{1,26}[”"]?[。？]?$')

def analyse(f):
    t = open(f, encoding='utf-8').read()
    lines = [l.strip() for l in t.split('\n') if l.strip()]
    # find maximal runs of consecutive quote-only lines
    runs = []
    i = 0
    while i < len(lines):
        if PAT.match(lines[i]):
            j = i
            while j < len(lines) and PAT.match(lines[j]):
                j += 1
            if j - i >= 6:
                runs.append((i, j - i))
            i = j
        else:
            i += 1
    return t, lines, runs

rows = []
for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
    for f in load(d):
        t, lines, runs = analyse(f)
        nq = sum(r[1] for r in runs)
        rows.append((nq, size(t), len(runs), f, runs, lines))

rows.sort(reverse=True)
print('按「对白连段」数排序，最长的25章：')
print('  段数 总字符  最长run  文件')
for nq, s, nr, f, runs, lines in rows[:25]:
    mx = max(r[1] for r in runs)
    print('  %4d %6d %5d   %s' % (nq, s, mx, f.split('/')[-1][:26]))
