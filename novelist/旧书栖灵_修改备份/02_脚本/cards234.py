import re
RENAME = {
 '第二部': {12:'今夜有客',20:'小满接手了舅舅的店',34:'去找陈伯',57:'林越走了以后'},
 '第三部': {33:'视频慢慢传开',34:'陈国华完成心愿那天',51:'陆栖独自在旧书区',
            56:'写完最后一个字',63:'陆栖在图书馆的夜里',69:'共鸣节第十二年'},
}
for d, m in RENAME.items():
    cf = '章节大纲/%s/逐章卡片.md' % d
    t = open(cf, encoding='utf-8').read()
    for n, new in m.items():
        pat = r'(?m)^### 第0*%d章[：:]\s*.+$' % n
        mm = re.search(pat, t)
        if mm:
            t = t[:mm.start()] + '### 第%d章：%s' % (n, new) + t[mm.end():]
        else:
            print('MISS', d, n)
    open(cf, 'w', encoding='utf-8').write(t)
print('ok')
