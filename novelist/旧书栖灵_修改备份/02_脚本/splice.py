import re, glob

# splice corruption: two sentence fragments glued with no punctuation,
# often a pronoun + verb + a noun phrase, e.g.
#   "她没有立刻下去。她又她看着那扇门那几盏灯"
PAT = [
 (r'她没有立刻[^。]{0,8}。她(?:又)?她', 'A'),
 (r'(?:她|他)看了(?:着)?那扇门那', 'B'),
 (r'声音就静静地响起(?:了|来)[，。]?', 'C'),
 (r'在[^。]{0,10}。(?:那|那那)个', 'D'),
 (r'[，。][^。]{0,6}(?:她|他)(?:又)?(?:她|他)', 'E'),
 (r'，(?=[^，。「\"]{2,8}[，。])', 'F'),
]

for f in sorted(glob.glob('正文/*/*.md')):
    t = open(f, encoding='utf-8').read()
    for pat, tag in PAT[:5]:
        for m in re.finditer(pat, t):
            s = t[max(0, m.start()-40):m.end()+40].replace('\n', ' ')
            print('%-4s %-20s | %s' % (tag, f.split('/')[-1][:18], s))
