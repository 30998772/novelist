import re, glob, collections

d = '正文/第四部'

# 1) AI tells
TELL = [
 (r'不是[^。！？，]{1,10}[，。](?:而)?是[^。！？]{1,14}。', '否定-修正'),
 (r'她忽然觉得|他忽然觉得|她终于明白|她明白了|这就是[^。]{1,8}的意义', '宣布情绪'),
 (r'说到底|归根到底|这便是|这才是', '总结句'),
 (r'像[^，。！？]{2,12}[，。]', '比喻'),
 (r'—{2,}—|——', '破折号'),
 (r'[。！？]\s*[^。！？]{0,6}(?:守|在|家|光|根|灯)[。！？]', '格言收束'),
 (r'不是[^。]{0,20}，(?:不是|而是)[^。]{0,20}。', '三重否定'),
]

rows = []
for f in sorted(glob.glob('%s/*.md' % d)):
    t = open(f, encoding='utf-8').read()
    n = len(re.findall(r'[\u4e00-\u9fff]', t))
    ps = [p.strip() for p in t.split('\n\n') if p.strip()]
    hits = {}
    score = 0
    for pat, name in TELL:
        c = len(re.findall(pat, t))
        if c:
            hits[name] = c
            score += c
    # short-paragraph inflation: many tiny paragraphs
    tiny = sum(1 for p in ps if len(re.sub(r'[^一-鿿]', '', p)) <= 10)
    ratio = tiny / max(1, len(ps))
    rows.append((score, round(ratio, 2), n, f, hits, len(ps)))

rows.sort(reverse=True)
print('第四部 AI 指数排序（分高=最像机器）')
print('%-5s %-5s %-6s %-4s %s' % ('AI', '碎段', '字数', '段数', '章名'))
for s, r, n, f, h, np in rows[:24]:
    ttl = f.split('/')[-1][7:-3]
    print('%-5d %-5.2f %-6d %-4d %-20s %s' % (s, r, n, np, ttl, h))
