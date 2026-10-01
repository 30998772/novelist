import re

f = '正文/第四部/第052章-冬与完成.md'
t = open(f, encoding='utf-8').read()

# The remaining ping-pong. Work on NORMALISED whitespace so exact-match
# failures can't happen, then restore paragraph structure.

def norm(txt):
    txt = re.sub(r'[ \t]+', '', txt)
    txt = re.sub(r'\n{2,}', '\n', txt)
    return txt

# Split into blocks (paragraph-separated), then find quote-only runs.
blocks = re.split(r'\n\n+', t)

R = [
# 霜 / 挑根
(['"你怎么不掉。"','"我等。"','"等什么。"','"等风。"','"今天没风。"','"今天有霜。"',
  '"霜是竖着落下来的。风是横着。"','"横着落得快还是慢。"','"竖着落得快。"',
  '"落得快怎么。"','"落得快，我能自己挑地方。"','"你挑哪儿。"','"我挑根。"'],
 ['"你怎么不掉。"','"我等。风是横着，霜是竖着。横着落得快。"','"落得快怎么。"',
  '"落得快，我能自己挑地方。"','"你挑哪儿。"','"我挑根。"']),

# 我先是土
(['"你不是土。"','"我先是土。"','"你先是叶。"','"然后呢。"','"然后我是土。"',
  '"你落了，烂了。"','"我烂得慢。我一个月，你半个月。"','"为什么。"',
  '"因为我不是纯的。你是黄葛，我是那根桩的。"'],
 ['"你不是土。"','"我先是土，你是叶。然后呢，我变成土。"','"你落了，烂了。"',
  '"我烂得慢。我一个月，你半个月。"','"为什么。"','"因为我不是纯的。你是黄葛，我是那根桩的。"']),

# 落在这儿
(['"你落在这儿多久了。"','"五天。"','"五天就成这个。"','"你十一月黄的。"',
  '"我十月黄的。"','"你比它早。"','"我是那根桩的。它也是。"','"它比根浅。"',
  '"什么叫浅。"','"我的根是它的两倍。"'],
 ['"你落在这儿多久了。"','"五天。"','"你十一月黄的。"','"我十月黄的。你比它早。"',
  '"我是那根桩的。它也是。"','"它比根浅。"','"什么叫浅。"','"我的根是它的两倍。"']),

# 硬着等开春
(['"那您就一直硬着。"','"我硬着的时候您等。"','"我等到开春。"','"开春您也软。"',
  '"那我们一块儿软。软了您挖。"','"我轻一点挖。"','"您挖了三十年。"',
  '"我挖出来的土都有用。"','"都有用。"'],
 ['"那您就一直硬着。我等到开春。"','"开春您也软。"','"那我们一块儿软。软了您挖。"',
  '"我轻一点挖。"','"您挖了三十年。"','"我挖出来的土都有用。"','"都有用。"']),
]

def key(lines):
    return re.sub(r'[^"]', '', '|'.join(lines))

# index all quote-only runs
i = 0
out = []
applied = 0
while i < len(blocks):
    b = blocks[i]
    if re.fullmatch(r'["“].{1,26}["”]?[。？]?', b.strip()) and i + 1 < len(blocks) and all(
            re.fullmatch(r'["“].{1,30}["”]?[。？]?', x.strip()) for x in blocks[i:i+12]):
        j = i
        while j < len(blocks) and re.fullmatch(r'["“].{1,26}["”]?[。？]?', blocks[j].strip()):
            j += 1
        run = [x.strip() for x in blocks[i:j]]
        k = key(run)
        hit = None
        for src, dst in R:
            if key(src) == k:
                hit = dst
                break
        if hit:
            out.extend(hit)
            applied += 1
            i = j
            continue
    out.append(b)
    i += 1

t = '\n\n'.join(out)
open(f, 'w', encoding='utf-8').write(t)
print('应用', applied, '段 | 现在', len(re.sub(r'\s', '', t)), '字符')