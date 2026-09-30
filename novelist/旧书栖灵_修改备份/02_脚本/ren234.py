import re, glob, os, shutil

RENAME = {
 '正文/第二部/第012章-完成的定义.md': '今夜有客',
 '正文/第二部/第020章-味道的传承.md': '小满接手了舅舅的店',
 '正文/第二部/第034章-匠心的传承.md': '去找陈伯',
 '正文/第二部/第057章-未完成的诗行.md': '林越走了以后',
 '正文/第三部/第033章-歌曲的传承.md': '视频慢慢传开',
 '正文/第三部/第034章-精灵的完成.md': '陈国华完成心愿那天',
 '正文/第三部/第051章-回声的永恒.md': '陆栖独自在旧书区',
 '正文/第三部/第056章-故事的完成.md': '写完最后一个字',
 '正文/第三部/第063章-永恒的文字.md': '陆栖在图书馆的夜里',
 '正文/第三部/第069章-共鸣的永恒.md': '共鸣节第十二年',
}

for src, new in RENAME.items():
    t = open(src, encoding='utf-8').read()
    m = re.search(r'(?m)^# 第(\d+)章\s*(.+)$', t)
    n, old = m.group(1), m.group(2).strip()
    t = t[:m.start()] + '# 第%s章 %s' % (n, new) + t[m.end():]
    open(src, 'w', encoding='utf-8').write(t)
    dst = os.path.dirname(src) + '/第%s章-%s.md' % (n, new)
    if dst != src:
        shutil.move(src, dst)
    # card
    d = os.path.dirname(src).split('/')[1]
    cf = '章节大纲/%s/逐章卡片.md' % d
    ct = open(cf, encoding='utf-8').read()
    cm = re.search(r'(?m)^### 第%s章[：:]\s*%s\s*$' % (n, re.escape(old)), ct)
    if cm:
        ct = ct[:cm.start()] + '### 第%s章：%s' % (n, new) + ct[cm.end():]
        open(cf, 'w', encoding='utf-8').write(ct)
    else:
        print('NOCARD', d, n, old)

print('done')
