import re
f = '正文/第一部/第028章-温柔的目送.md'
t = open(f, encoding='utf-8').read()

fixes = [
 # duplicate of the 词典小姑娘 exchange
 ('词典小姑娘似懂非懂地点点头，又钻回她的词典里去了。过了一会儿，从书页里伸出一只小手，朝她挥了挥："哥哥，送别的时候你会难过吗？"她说会。小姑娘又问："那怎么办呢？"她想了想，说：\n\n"难过一会儿，然后替它们高兴。"\n\n',
  '词典小姑娘似懂非懂地点点头，又钻回她的词典里去了。\n\n'),

 # duplicate appraisal of the half-millimetre slip
 ('老头翻完第二遍的时候，把书合上了。他摘下老花镜，在手里转了两圈，然后说了那句「这页补纸的帘纹，斜了半分」。陆栖凑过去看，果然——补纸的帘纹比原纸偏了大约半毫米，不仔细看根本看不出来，可顾松年一眼就瞧出来了。\n\n',
  '老头翻完第二遍的时候，把书合上了。他摘下老花镜，在手里转了两圈。\n\n'),

 # outline leftover acting as a heading
 ('交活那天，老头戴上老花镜\n\n老头看东西很慢。',
  '交活那天，老头戴上老花镜。他看东西很慢。'),
]

for a, b in fixes:
    if a not in t:
        print('MISS >>>', repr(a[:50]))
    t = t.replace(a, b)

t = re.sub(r'\n{3,}', '\n\n', t)
open(f, 'w', encoding='utf-8').write(t)
print('chars', len(re.findall(r'[\u4e00-\u9fff]', t)))
