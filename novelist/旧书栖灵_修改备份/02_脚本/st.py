import sys,re
for f in sys.argv[1:]:
    s=open(f,encoding='utf-8').read()
    w=len(re.sub(r'\s','',s))
    lines=[l for l in s.split('\n') if l.strip()]
    dial=[l for l in lines if re.search(r'[「」“”"]',l)]
    run=best=0;br=bestr=0
    for l in lines:
        if re.search(r'[「」“”"]',l): run+=1
        else: run=0
        best=max(best,run)
        if run>1: br+=1
        else: br=0
        bestr=max(bestr,br)
    print(f, 'w',w,'dial',len(dial),'per1k',round(len(dial)/(w/1000),1),'maxrun',best)
