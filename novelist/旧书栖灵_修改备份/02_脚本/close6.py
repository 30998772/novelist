import re, glob

# Book-wide closing templates in 第六部. Keep one, drop the rest.
DROP_SOUND = '她踩着楼梯上楼，脚步很轻，楼梯的吱呀声反而比脚步声还响。'
DROP_SOUND2 = '她踩着楼梯下楼，脚步声很轻，楼梯的吱呀声反而比脚步声还响。'
pat_who = re.compile(r'不知道是说给谁听的。也许是说给[^。]{2,40}。', re.S)
pat_sound = re.compile(r'(?:她|他)?踩着楼梯(?:上楼|下楼)，(?:脚步声|脚步)很轻，楼梯的吱呀声反而比(?:脚步声|脚步)还响。')

removed = 0
for f in sorted(glob.glob('正文/第六部/*.md')):
    t = open(f, encoding='utf-8').read()
    o = t
    t = pat_who.sub('', t)
    t = pat_sound.sub('', t)
    if t != o:
        t = re.sub(r'[，、]\s*([。！？])', r'\1', t)
        t = re.sub(r'\n{3,}', '\n\n', t)
        open(f, 'w', encoding='utf-8').write(t)
        removed += 1
print('files cleaned', removed)
