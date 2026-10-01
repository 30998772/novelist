import re, glob, sys

def han(t):  return len(re.findall(r'[\u4e00-\u9fff]', t))
def size(t): return len(re.sub(r'\s', '', t))   # 总字符，不含空白

PARTS = ['第一部','第二部','第三部','第四部','第五部','第六部']

def rows():
    out = []
    for d in PARTS:
        for f in sorted(glob.glob('正文/%s/*.md' % d)):
            t = open(f, encoding='utf-8').read()
            out.append((size(t), han(t), f))
    return out

def report(lo=3500, hi=3500):
    r = rows()
    r.sort()
    tot = sum(x[0] for x in r)
    print('总 %d章  %d总字符  均%d' % (len(r), tot, tot // len(r)))
    under = [x for x in r if x[0] < lo]
    over  = [x for x in r if x[0] > hi]
    print('不足%d: %d章    超过%d: %d章' % (lo, len(under), hi, len(over)))
    return r, under, over

if __name__ == '__main__':
    r, u, o = report()
    print('\n--- 最短 20 章')
    for s, h, f in r[:20]:
        print('  %5d (%4d汉字)  %s' % (s, h, f.split('/')[-1][:24]))
    print('\n--- 最长 25 章')
    for s, h, f in r[-25:]:
        print('  %5d (%4d汉字)  %s' % (s, h, f.split('/')[-1][:26]))
