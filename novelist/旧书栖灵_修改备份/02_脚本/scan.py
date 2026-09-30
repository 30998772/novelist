import re, glob, collections, os

# AI-ism signatures found by reading, as regexes
pats = {
 'explain-emotion':   r'不是真的|不是不[^。]{0,4}，是|她忽然觉得|她终于明白|她明白了|原来这就是',
 'neg-then-define':  r'不是[一-龥]{2,8}[，。]是[一-龥]{2,8}[。]',
 'not-but-two':      r'不是[一-龥]{1,10}，(?:而是|是)[一-龥]{1,10}[。]',
 'summary-line':     r'[^。]{4,30}。丢的和在的|有些东西在丢|这就是[一-龥]{2,10}的意思|说到底|归根到底',
 'aphorism-end':     r'[^。]{0,40}，(?:可|但)[^。]{0,10}一(?:盏|本|册|个|棵|条|件|口|把|块|张|片|滴|点|阵|丝|道|群|排|串|行|面|阵|轮|味|点|痕|些)(?:也|都)?不[一-龥]{1,6}[。]',
 'simile-eqn':       r'像[一-龥]{1,6}的[一-龥]{1,6}[，。]',
 'tell-shoulder':    r'不是.{1,6}，(?:是|而是)[^。]{1,20}。',
 'know-not-tell':    r'像有人[在从][^。]{0,20}[望看][^。]{0,10}。',
 'tree-elder':       r'像一个[^。]{0,10}老人|看透了世事|不急不躁',
 'apoc-formula':     r'不是[一-龥]{1,8}，(?:是|而是)[一-龥]{1,8}。[^。]{0,6}(?:是|而是)[一-龥]{1,8}。',
 'restate-end':      r'不知道是说给谁听的|也许是说给这栋楼|这些都是她的|一盏也不会灭',
 'warm-generic':     r'心里(?:是|有一(?:点|种|些)?)[^。]{0,8}(?:暖|热|满|踏实|复杂|不是滋味)',
 'set-piece-sum':    r'不是把[一-龥]{1,8}，(?:是|而是)把[一-龥]{1,8}。',
}

rows = []
for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    n = len(re.findall(r'[\u4e00-\u9fff]', t))
    score = 0
    hits = {}
    for k, p in pats.items():
        c = len(re.findall(p, t))
        if c:
            score += c
            hits[k] = c
    rows.append((score, n, f, hits))

rows.sort(reverse=True)
print('chapters', len(rows))
tot = sum(r[0] for r in rows)
print('total hits', tot, 'mean', round(tot/len(rows), 1))
print()
for s, n, f, h in rows[:25]:
    print(s, n, f)
    print('    ', h)
