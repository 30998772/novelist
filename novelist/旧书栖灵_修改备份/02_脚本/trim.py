import re
drops={
"第015章-针对性校验.md":[136,140],
"第016章-落雁谷围杀.md":[74,78],
"第017章-死亡不掉落.md":[135,151],
"第020章-倒计时72小时.md":[102],
"第022章-三秒溃败.md":[136],
"第024章-特例单位.md":[36,38],
"第033章-数据之海.md":[60],
"第036章-握住那根触手.md":[238,240],
"第040章-银白丝线.md":[255,263,265],
"第044章-四万次推演.md":[371,375,379,385,387],
"第045章-河床.md":[286,288],
"第046章-半块干粮.md":[78,86,88],
}
import os
os.chdir("/mnt/d/devProject/writer/novelist/BUG 玩家：我能卡出游戏规则/正文/第一部")
for f,idxs in drops.items():
    ls=open(f,encoding='utf-8').read().split('\n')
    for i in idxs:
        assert re.fullmatch(r'「.+」',ls[i]), (f,i,ls[i])
    kill=set()
    for i in idxs:
        kill.add(i)
        if ls[i+1]=='' and ls[i+2]=='':
            kill.update([i+1,i+2])
    out=[l for i,l in enumerate(ls) if i not in kill]
    open(f,'w',encoding='utf-8').write('\n'.join(out))
    print(f,len(idxs),sum(1 for l in out if re.fullmatch(r'「.+」',l)))
