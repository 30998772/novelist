import re,sys
for p in sys.argv[1:]:
    t=open(p,encoding='utf-8').read()
    print(len(re.findall(r'[\u4e00-\u9fff]',t)), p)
