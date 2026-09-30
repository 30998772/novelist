import re, glob, collections

ABSTRACT = re.compile(r'永远|传承|存在|感觉|温暖|记得|记住|意义|守护|爱|家|根|光|活着|传递|延续|呼吸|心跳|温度|不再|永远|一辈子|一生|轮回|羁绊|光阴|岁月|时间')

sent = collections.defaultdict(list)
for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    for s in re.split(r'(?<=[。！？])', t):
        s = s.strip()
        if 6 <= len(s) <= 30 and '“' not in s and '"' not in s and '：' not in s and not s.startswith('#'):
            sent[s].append(f)

rep = {s: fs for s, fs in sent.items() if len(fs) >= 3 and ABSTRACT.search(s)}
print('abstract aphorisms >=3x:', len(rep), 'total instances', sum(len(v) for v in rep.values()))
for s, fs in sorted(rep.items(), key=lambda kv: -len(kv[1])):
    print(len(fs), s)
