import re, glob, sys
def cjk(s): return len(re.findall(r'[\u4e00-\u9fff]', s))
def show(th=2800):
    tot=0
    print('%-4s %5s %8s %6s'%('部','章','字','均'))
    for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
        fs=sorted(glob.glob('正文/%s/*.md'%d))
        n=sum(cjk(open(f,encoding='utf-8').read()) for f in fs); tot+=n
        print('%-4s %5d %8d %6d'%(d,len(fs),n,n//len(fs)))
    print('合计 %d 章 %d 字'%(sum(len(glob.glob('正文/%s/*.md'%d)) for d in ['第一部','第二部','第三部','第四部','第五部','第六部']),tot))
    if th:
        print('\n<%d 字的章：'%th)
        rows=[]
        for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
            for f in sorted(glob.glob('正文/%s/*.md'%d)):
                n=cjk(open(f,encoding='utf-8').read())
                if n<th: rows.append((n,d,f))
        rows.sort()
        for n,d,f in rows: print('  %5d %s/%s'%(n,d,f.split('/')[-1]))
        print('共',len(rows))
if __name__=='__main__':
    show(int(sys.argv[1]) if len(sys.argv)>1 else 2800)
