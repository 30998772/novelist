import re, glob
def cjk(s): return len(re.findall(r'[\u4e00-\u9fff]', s))
rows=[]
for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
    for f in sorted(glob.glob('正文/%s/*.md'%d)):
        t=open(f,encoding='utf-8').read()
        if cjk(t)>=2800: continue
        # unattributed dialogue: a quoted line with no speaker tag on the same line
        q=len(re.findall(r'(?m)^[""].{1,40}["”]?$', t))
        tagged=len(re.findall(r'(?m)^["”][^"”]{0,8}["“]?[，。]', t))
        rows.append((q, cjk(t), d, f.split('/')[-1]))
rows.sort(reverse=True)
print('%-4s %6s %5s  %s'%('对话','字数','部','章'))
for q,n,d,f in rows[:20]: print('%-4d %6d %5s  %s'%(q,n,d,f[:24]))
