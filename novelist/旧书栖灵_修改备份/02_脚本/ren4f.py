import re, os, shutil
R = {
 '正文/第四部/第018章-土地的完成.md':   '地脉草长到了膝盖',
 '正文/第四部/第023章-方知远的传承.md': '三月，苏念看出那双手',
 '正文/第四部/第025章-种子的归宿.md':   '在手心里躺了九天',
 '正文/第四部/第048章-果实的完成.md':   '树上还剩三十四颗',
 '正文/第四部/第054章-永恒的循环.md':   '四支温度计',
 '正文/第四部/第057章-苏晚的传承.md':   '新人叫周允',
 '正文/第四部/第060章-永恒的守护.md':   '天黑以后周明远上楼',
}
for src, new in R.items():
    t = open(src, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', t)
    n, old = m.group(1), m.group(2).strip()
    t = t[:m.start()] + '# 第%s章 %s' % (n, new) + t[m.end():]
    open(src, 'w', encoding='utf-8').write(t)
    dst = os.path.dirname(src) + '/第%s章-%s.md' % (n, new)
    if dst != src:
        shutil.move(src, dst)
    cf = '章节大纲/第四部/逐章卡片.md'
    ct = open(cf, encoding='utf-8').read()
    cm = re.search(r'(?m)^### 第0*%s章[：:]\s*%s\s*$' % (n, re.escape(old)), ct)
    if cm:
        ct = ct[:cm.start()] + '### 第%s章：%s' % (n, new) + ct[cm.end():]
        open(cf, 'w', encoding='utf-8').write(ct)
    else:
        print('NOCARD', n, old)
print('ok')
