import re,collections,sys,os
D='正文/第一部/'
def chk(f):
    t=open(D+f,encoding='utf-8').read()
    L=[x.strip() for x in t.split('\n') if x.strip() and not x.startswith('#')]
    d=[x for x in L if x.startswith('"') and x.count('"')>=2]   # 独占行引语=对白
    narr=[len(re.sub(r'\s','',x)) for x in L if not x.startswith('"')]
    sl=[len(re.sub(r'\s','',x)) for x in re.split(r'(?<=[。！？])',t) if x.strip()]
    s=[x.strip() for x in re.split(r'[。\n]',t) if x.strip() and x.strip() not in ('"','」','「','』')]
    c=collections.Counter(s)
    q=len(re.findall(r'厚|薄|软|硬|涩|黏|糙|滑|毛|渣|屑|钝|粗|细|密|稀|脆|实|凸|凹|烫|凉|温',t))
    h=len(re.findall(r'摸|按|压|贴|碰|抓|捏|捧|托|抠|划|擦|戳|握|搁|攥|搓|蹭|甩|插|抽|挑|抖|拍|推|拉',t))
    ban=re.findall(r'仿佛|宛如|犹如|一丝|涌起|似乎在|不仅仅|涌上心头|眼底闪过',t)
    return dict(c=len(re.sub(r'\s','',t)),seg=sum(narr)//max(len(narr),1),dlg=100*len(d)//max(len(L),1),
      med=sorted(sl)[len(sl)//2],lg=sum(1 for x in sl if x>=45),rep=c.most_common(1)[0][1],
      q=q,h=h,ban=len(ban),dash=t.count('——'),im=sum(t.count(w) for w in ['灰','霜','墨','屑','霉']),
      end=L[-1][:30],nd=len(d))
rows=[]
for f in sys.argv[1:]:
    rows.append((f[:3],chk(f)))
print('%-5s %5s %5s %5s %5s %5s %4s %4s %4s %4s %4s %4s'%('章','字符','段均','对白','句中位','长句','复读','质感','手部','破折','禁用','意象'))
for n,v in rows:
    ok=lambda b:'✓' if b else '✗'
    print('%-5s %5d%s %5d%s %4d%s%s %5d %5d %4d%s %4d %4d %4d%s %4d'%(
      n,v['c'],ok(3600<=v['c']<=4000),v['seg'],ok(60<=v['seg']<=180),v['dlg'],'%',ok(10<=v['dlg']<=25),
      v['med'],v['lg'],v['rep'],ok(v['rep']<=1),v['q'],v['h'],v['dash'],ok(v['ban']==0),v['im']))
for n,v in rows: print('%s 末: %s'%(n,v['end']))
