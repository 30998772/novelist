import re
R = {18:'地脉草长到了膝盖',23:'三月，苏念看出那双手',25:'在手心里躺了九天',
     48:'树上还剩三十四颗',54:'四支温度计',57:'新人叫周允',60:'天黑以后周明远上楼'}
cf = '章节大纲/第四部/逐章卡片.md'
t = open(cf, encoding='utf-8').read()
for n, new in R.items():
    m = re.search(r'(?m)^### 第0*%d章[：:]\s*.+$' % n, t)
    if m:
        t = t[:m.start()] + '### 第%d章：%s' % (n, new) + t[m.end():]
    else:
        print('MISS', n)
open(cf, 'w', encoding='utf-8').write(t)
print('ok')
