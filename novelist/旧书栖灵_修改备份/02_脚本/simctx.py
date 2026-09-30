import re, glob

TARGETS = ['像一盏小小的灯', '像是在回应', '像一首很安静的歌', '像一条河', '像一条安静的河',
           '像一把巨伞', '像一把撑开的巨伞', '像一颗小小的心脏在跳动', '像冬天的炭炉', '像风铃']

for f in sorted(glob.glob('正文/第一部/*.md')):
    t = open(f, encoding='utf-8').read()
    name = f.split('/')[-1][:14]
    for tg in TARGETS:
        for m in re.finditer(re.escape(tg), t):
            s = max(0, m.start() - 32)
            print('%-14s | %-12s | %s' % (name, tg, t[s:m.end() + 18].replace('\n', ' ')))
