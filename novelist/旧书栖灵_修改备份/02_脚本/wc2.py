import sys,re
for f in sys.argv[1:]:
    t=open(f,encoding='utf-8').read()
    n=len(re.sub(r'\s','',t))
    print(n,f)
