import sys
t=open(sys.argv[1],encoding='utf-8').read().split('\n')
run=[];runs=[]
for i,l in enumerate(t,1):
    d=l.lstrip().startswith(('"','「'))
    if d: run.append(i)
    elif l.strip() and not l.startswith('#'):
        if run: runs.append(run)
        run=[]
if run: runs.append(run)
for r in runs: print(r[0],'-',r[-1],'len',len(r))
