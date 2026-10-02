import re,glob,sys
def fix(t):
    n=0
    # 破折号后半句是完整句 -> 改句号
    t,k=re.subn(r'——(?=[^。！？\n]{4,}[。！？])','。',t); n+=k
    # 其余 -> 改冒号或逗号
    t,k=re.subn(r'——(?=[^。！？\n]{4,})','，',t); n+=k
    t=t.replace('——','，')
    # 清理重复标点
    t=re.sub(r'。，','。',t); t=re.sub(r'，，','，',t)
    t=re.sub(r'，。','。',t); t=re.sub(r'：，','：',t)
    t=re.sub(r'；，','；',t); t=re.sub(r'，，+','，',t)
    t=re.sub(r'。。','。',t); t=re.sub(r'，，','，',t)
    return t,n
for f in sys.argv[1:]:
    t=open(f,encoding='utf-8').read()
    b=t.count('——')
    t,n=fix(t)
    open(f,'w',encoding='utf-8').write(t)
    print('%-30s 破折 %2d -> %2d (改%d)'%(f.split('/')[-1][:28],b,t.count('——'),n))
