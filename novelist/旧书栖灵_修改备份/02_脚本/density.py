import re, glob, collections

SIM = re.compile(r'，?像[^，。！？]{2,14}[，。]')
NEG = re.compile(r'不是[^。！？，]{1,10}[，。](?:而)?是[^。！？]{1,14}。')
TELL = re.compile(r'她忽然觉得|他忽然觉得|她忽然明白|她终于明白|她觉得|她知道|她想，|她心里')

for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
    fs = sorted(glob.glob('正文/%s/*.md' % d))
    sim = neg = tell = tot = 0
    for f in fs:
        t = open(f, encoding='utf-8').read()
        tot += len(re.findall(r'[\u4e00-\u9fff]', t))
        sim += len(SIM.findall(t))
        neg += len(NEG.findall(t))
        tell += len(TELL.findall(t))
    print('%s 字%7d  像:%4d  不是X是Y:%4d  心理叙述:%4d  每千字 %.1f' %
          (d, tot, sim, neg, tell, (sim+neg+tell)/tot*1000))
