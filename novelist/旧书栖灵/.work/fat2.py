import re, glob, collections

def size(t): return len(re.sub(r'\s', '', t))

def sents(t):
    out = []
    for p in re.split(r'\n+', t):
        for s in re.split(r'(?<=[。！？])', p):
            s = s.strip()
            if len(re.findall(r'[\u4e00-\u9fff]', s)) >= 8:
                out.append(re.sub(r'[^一-鿿]', '', s))
    return out

dup_chars = 0          # 章内完全重复的句子
near = 0
restate = collections.Counter()
tot = 0

for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
    for f in glob.glob('正文/%s/*.md' % d):
        t = open(f, encoding='utf-8').read()
        tot += size(t)
        ss = sents(t)
        c = collections.Counter(ss)
        for s, n in c.items():
            if n > 1:
                dup_chars += size(s) * (n - 1)

print('总字符                        %d' % tot)
print('章内整句重复浪费               %d  (%.1f%%)' % (dup_chars, dup_chars * 100.0 / tot))

# 主题总结句 / 抽象收束
THEME = [
 (r'她想起[^。]{6,40}。', '她想起'),
 (r'她想[，,]?\s*(当年|那年|从前|以前)', '她想当年'),
 (r'她知道[^。]{6,40}。', '她知道'),
 (r'这就是[^。]{2,24}。', '这就是'),
 (r'原来[^。]{2,24}。', '原来'),
 (r'不是[^。]{2,20}[，,][^。]{2,20}[。，]', '不是…而是'),
 (r'她这辈子[^。]{4,30}。', '她这辈子'),
 (r'年年都来', '年年都来'),
]
tc = collections.Counter()
for d in ['第一部','第二部','第三部','第四部','第五部','第六部']:
    for f in glob.glob('正文/%s/*.md' % d):
        t = open(f, encoding='utf-8').read()
        for p, name in THEME:
            for m in re.finditer(p, t):
                tc[name] += size(m.group(0))
print()
print('高频总结/抽象句式:')
for k, v in tc.most_common():
    print('  %-12s %6d' % (k, v))
print('  合计        %6d  (%.1f%%)' % (sum(tc.values()), sum(tc.values())*100.0/tot))