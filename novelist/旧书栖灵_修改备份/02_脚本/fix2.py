import re, glob

# exact/near recycled paragraphs in 第二部 -> keep first, replace the rest
pairs = [
 # the 十二封信 letter, quoted twice
 ('第三页的日期是一九八七年冬。"婉：如今可以通信了。我在打听桂花巷的下落，你等我的信。"也断在这里。',
  '第三页的日期是一九八七年冬，笔迹和前面几页一样工整。往后翻，是空的。'),
 # the 遗憾离世的年轻女子 explanation
 ('陆栖明白了。这是一个带着遗憾离世的年轻女子，她的灵因为未完成的心愿而留在了那本书里。',
  '陆栖把那本书合上，手指在封面上停了一会儿。'),
 # the "杯子注满水" metaphor
 ('陆栖看着屏幕上的文件夹，心里有一种很满的东西，像一只杯子，被慢慢地注满了水。',
  '陆栖看着屏幕上的文件夹，把窗口一个一个关掉。'),
 # the 心里松了/暖了一下 pair
 ('陆栖听到这句话，心里忽然暖了一下。她知道，这句话，就是陈志远等了更久的那句话。',
  '陆栖没有说话，把那本登记册翻回前一页，对照了一下日期。'),
 # the 抚过封面 pair
 ('她走回桌前，拿起那本书，放回书架。手指抚过那本暗红色的封面，像是在安抚一个睡着的孩子。',
  '她走回桌前，拿起那本书，放回书架。'),
 # the 今夜这风 pair
 ('今夜这风，替她也替这栋楼里所有的灵，把苏晚的成长，吹进了这栋楼的墙壁里。',
  '窗外的风把那阵琴声送进来，一直送到天井里。'),
 ('今夜这风，替她也替这栋楼里所有的灵，把这个愿望，吹向了新的一年。',
  '钟声散尽以后，阅览室里安静下来。'),
]

n = 0
for a, b in pairs:
    hit = False
    for f in sorted(glob.glob('正文/第二部/*.md')):
        t = open(f, encoding='utf-8').read()
        if a in t:
            t = t.replace(a, b, 1)
            t = re.sub(r'\n{3,}', '\n\n', t)
            open(f, 'w', encoding='utf-8').write(t)
            hit = True
            n += 1
    if not hit:
        print('MISS', repr(a[:36]))
print('files touched', n)
