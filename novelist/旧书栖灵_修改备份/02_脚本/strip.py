import re, glob, collections

# aphorisms to reduce: keep the FIRST occurrence book-wide, drop the rest.
TARGETS = [
 '风会记得回的。',
 '一个灵有了名字，就有了家。',
 '那种爱会永远存在。',
 '根在，树就在。',
 '那种感觉，和它自己被人写在借阅册上的感觉，是一样的。',
 '你给它们起名字，就是给它们一个家。',
 '在音乐里，在文字里，在每一个被记住的故事里。',
 '这就是传承。',
 '那些温度会永远存在。',
 '不会消失，就永远在。',
 '做得久了，就变成了永远的一部分。',
 '而记住，就是永恒。',
 '那个余韵会永远存在。',
 '它来自每一个曾经在这个世界上存在过的生命。',
 '他不再是一个孤独的灵。',
 '一年，十年，一辈子。',
 '守护，不是把东西锁在柜子里，是把东西的故事讲给更多人听。',
 '守护，不是一个人守到底，是一群人接力守下去。',
 '守护，不是阻止时光流逝，是接收时光留下的礼物。',
 '不是消散，是释然。',
 '可文献馆里，很暖。',
 '这栋楼的灯，亮着。',
 '所有的灵都在这里。',
 '她想，阿棠知道了。',
 '你慢慢就会懂了。',
 '不是灯，是读它的人。',
 '不是用耳朵，是用心。',
 '不是时间��延续，而是精神的传承。',
 '不是让灵永远存在，而是让灵的心意永远传递。',
 '不是把东西保存在玻璃柜里，而是让它们活在人们的生活中。',
 '不是记录事实，而是传递心意。',
 '不是看见之后才信，是信了之后才会看见。',
 '不是用嘴笑，而是用整个身体笑。',
 '不是来自音量，而是来自深度。',
 '不是翻身，是抬头。',
 '不是灵，是人。',
 '不是死物，是活的。',
 '不是浪费，是信仰。',
 '不是热，是一种很轻很轻的"活着"的感觉。',
 '不是空，是"满"。',
 '不是灵的气息，是一种更深的、更暖的东西。',
 '不是触感，而是一种情绪。',
 '不是叹息，是释然。',
 '不是消散，是释然。',
]

# for each target, keep one (the first in sorted file order), remove the rest as
# standalone sentences including their trailing newline
removed = collections.Counter()
for tgt in TARGETS:
    if '�' in tgt:
        continue
    hit_files = []
    for f in sorted(glob.glob('正文/*/*.md')):
        t = open(f, encoding='utf-8').read()
        n = t.count(tgt)
        if n:
            hit_files.append((f, t, n))
    for i, (f, t, n) in enumerate(hit_files):
        if i == 0:
            continue  # keep first
        # drop all occurrences in this file
        nt = t.replace(tgt, '')
        # tidy leftover blank line runs
        nt = re.sub(r'\n{3,}', '\n\n', nt)
        nt = re.sub(r'^[ \t]*\n', '', nt, flags=re.M)
        open(f, 'w', encoding='utf-8').write(nt)
        removed[tgt] += n

for k, v in removed.most_common():
    print(v, k)
print('total sentences removed', sum(removed.values()))
