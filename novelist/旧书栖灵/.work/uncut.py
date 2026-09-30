"""Remove the invented filler blocks appended in the last two batches.

The rewrites (speaker attribution, number/age fixes) stay. Only the
appended scenes -- which I wrote to hit a word count rather than because
they belonged to the story -- are cut back out.
"""
import re, glob, os

CUTS = {
 '正文/第四部/第028章-种子的传播.md': ['\n---\n\n十月里她去了一趟城南。'],
 '正文/第四部/第061章-约定的开始.md': ['\n---\n\n八月，苏念来记。'],
 '正文/第四部/第055章-四千零一十一行.md': ['\n---\n\n十一月初九，陆栖把方知远的册子搬到二楼'],
 '正文/第四部/第053章-花园的成长.md': ['\n---\n\n十月，老陶没有来。'],
 '正文/第四部/第060章-天黑以后周明远上楼.md': ['\n---\n\n九月，周明远把那张底片洗出来了。'],
 '正文/第四部/第034章-时间的礼物.md': ['\n---\n\n八月十九，陆栖又去了一趟东北角。'],
 '正文/第四部/第039章-落叶的归途.md': ['\n---\n\n次年三月十九，陆栖在东墙根看见一个东西。'],
 '正文/第四部/第037章-陈老的回忆.md': ['\n---\n\n十二月初九，陆栖又去了柳巷。'],
 '正文/第二部/第055章-时光的礼物.md': ['\n---\n\n三月十九，苏晚把展览的名单抄完'],
 '正文/第六部/第064章-冬至守护.md': ['\n---\n\n冬至过后的第三天，她病了一场。'],
 '正文/第四部/第059章-春泥的花园.md': ['\n---\n\n七月中旬，陆栖开始每天去东墙根。'],
 '正文/第四部/第027章-重逢的温暖.md': ['\n---\n\n十一月十九，东墙根那片新土上出了东西。'],
 '正文/第三部/第053章-林越的帮助.md': ['\n---\n\n第三个月，她交稿了。'],
 '正文/第四部/第032章-年轮的智慧.md': ['\n---\n\n四月十九，陆栖带了一把钢锯去。'],
 '正文/第一部/第062章-晚风年年都来.md': ['\n---\n\n转年开春，二月底，老馆里来了一批孩子。'],
}

def cjk(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))

for f, marks in CUTS.items():
    t = open(f, encoding='utf-8').read()
    before = cjk(t)
    for m in marks:
        if m not in t:
            print('MARK MISSING', f, m[:22])
            continue
        t = t[:t.index(m)].rstrip() + '\n'
    open(f, 'w', encoding='utf-8').write(t)
    print('%-34s %5d -> %5d  (-%d)' % (f.split('/')[-1][:32], before, cjk(t), before - cjk(t)))