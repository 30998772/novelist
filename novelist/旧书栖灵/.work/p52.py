import re, glob

# 第052章 冬与完成: 875行里约800行是"一问一答"的乒乓对白，且多处说话人混乱。
# 作者真正写的是三件事：根会自己挪（六根三根挪到东墙根）、
# 黄葛今年一米八落叶十七片一片不掉、以及东墙根那一畦的事。
# 下面逐段手改，不是脚本批改。

f = '正文/第四部/第052章-冬与完成.md'
t = open(f, encoding='utf-8').read()

def size(s): return len(re.sub(r'\s', '', s))

print('原', size(t), '字符,', len([l for l in t.split('\n') if l.strip()]), '行')
