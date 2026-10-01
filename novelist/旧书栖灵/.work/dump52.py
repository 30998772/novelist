import re, sys

f = '正文/第四部/第052章-冬与完成.md'
t = open(f, encoding='utf-8').read()
Q = re.compile(r'^["“].{1,26}["”]?[。？]?$')

lines = [l.strip() for l in t.split('\n') if l.strip()]
runs = []
i = 0
while i < len(lines):
    if Q.match(lines[i]):
        j = i
        while j < len(lines) and Q.match(lines[j]):
            j += 1
        runs.append((i, j))
        i = j
    else:
        i += 1

print('乒乓段 %d 个，共 %d 行' % (len(runs), sum(j-i for i, j in runs)))
print()
for st, en in runs:
    n = en - st
    if n >= 8:
        print('--- line %d, %d 行' % (st, n))
        for k in range(st, en):
            print('   ', lines[k][:64])
        print()