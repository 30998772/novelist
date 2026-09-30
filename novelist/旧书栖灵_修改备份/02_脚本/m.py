import re,sys
for p in sys.argv[1:]:
    t=open(p,encoding='utf-8').read()
    c=len(re.findall(r'[\u4e00-\u9fff]',t))
    n=len(re.findall(r'^\s*["「]',t,flags=re.M))
    run=mx=0
    for l in t.split('\n'):
        if l.lstrip().startswith(('"','「')): run+=1; mx=max(mx,run)
        elif l.strip() and not l.startswith('#'): run=0
    print('字数%d 对话%d 密度%.1f 最长%d  %s'%(c,n,n/c*1000,mx,p))
