import re, glob

# "像是在回应" is a real motif (spirits answering) but 12 uses is too many.
# Keep the strongest, vary the rest by what actually moves.
subs = [
 ('蝉的触须动了动，像是在回应。', '蝉的触须动了动。'),
 ('蝉的翅膀动了一下，像是在回应。', '蝉的翅膀动了一下。'),
 ('蝉的动了动翅膀，很轻很轻的一下，像是在回应。', '蝉的动了动翅膀，很轻很轻的一下。'),
 ('树的叶子沙沙响了一阵，像是在回应。她觉得那声音比以前响了一些',
  '树的叶子沙沙响了一阵，比刚才密。她站住脚听了一会儿'),
 ('树的叶子沙沙响了一阵，像是在回应。他觉得那声音比以前响了一些',
  '树的叶子沙沙响了一阵，比刚才密。他站着没动，听了好一会儿'),
 ('树的叶子沙沙响了一阵，像是在回应。', '树的叶子沙沙响了一阵。'),
 ('树的叶子沙沙响了一下，像是在回应。', '树的叶子沙沙响了一下。'),
 ('绿萝的叶子轻轻颤了颤，像是在回应。', '绿萝的叶子轻轻颤了颤。'),
 ('灯焰晃了一下，像是在回应。', '灯焰晃了一下。'),
 ('书页轻轻掀动了一下，像是在回应。', '书页轻轻掀动了一下。'),
]

n = 0
for f in sorted(glob.glob('正文/第一部/*.md')):
    t = open(f, encoding='utf-8').read()
    o = t
    for a, b in subs:
        t = t.replace(a, b, 1)
    if t != o:
        t = re.sub(r'\n{3,}', '\n\n', t)
        open(f, 'w', encoding='utf-8').write(t)
        n += 1
print('files touched', n)
