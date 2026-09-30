#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三部 补充扫描 v2：宽语境窗口，供人工核验"""
import glob, re, json

DIR = '/mnt/d/devProject/writer/novelist/旧书栖灵/正文/第三部'
MALE = ['林越', '周明远', '周先生', '方知远', '顾松年', '周维德', '林晓颂']
LUQI = ['陆栖', '陆老师', '陆馆长']
FEMO = ['苏晚', '顾念', '沈念', '阿棠']
VERBS = (r'(?:看了看|看着|望着|盯着|瞅着|端详着|打量着|看了|瞅了|望了|盯了|'
         r'递给|交给|推给|塞给|扔给|握住|握了|拉住|抓住|扶着|扶了|'
         r'拍了拍|拍着|碰到|摸了摸|摸着|陪着|守着|劝了|'
         r'想起|记得|想念|回应|回答|面对|朝向|对着|叫了|喊了|请了|'
         r'谢谢|照顾|留给|打量|端详|瞅|盯|望|递|交|推|'
         r'握|拉|抓|扶|拍|碰|摸|陪|守|劝|问|叫|喊|请|谢|照顾|想|记|'
         r'对|跟|向|给|帮|留|回应|回答|面对)')
TAGS = re.compile(r'(?<![他她])他(说|问|答|喊|道|开口|回答|念|讲|轻声|喃喃)')


def last_pos(t, ws):
    return max([t.rfind(w) for w in ws] + [-1])


def subj_is_luqi(para):
    """段落主语是否为陆栖：陆栖出现在首个句首人称位置，且其后无男性主语"""
    if not any(w in para for w in LUQI):
        return False
    m = re.search(r'[。！？]', para)
    first = para[:m.start()] if m else para
    lp = max(first.find(w) for w in LUQI)
    if lp < 0:
        return False
    for w in MALE:
        if first.find(w) > lp:
            return False
    return True


def run():
    A, B = [], []
    for path in sorted(glob.glob(DIR + '/*.md')):
        raw = open(path, encoding='utf-8').read().split('\n')
        paras = [p for p in raw if p.strip() and not p.lstrip().startswith('#')]
        fn = path.split('/')[-1]
        for i, p in enumerate(paras):
            if p.count('"') % 2 == 1:
                continue
            back = paras[max(0, i - 3):i]
            fwd = paras[i + 1:i + 3]
            ctx = ''.join(back) + p + ''.join(fwd)
            prev = back[-1] if back else ''
            # ---- A类 ----
            for m in re.finditer(VERBS + r'他(?!们|人|家|用|者|所)', p):
                s = m.start()
                if p[:s].count('"') % 2 == 1:
                    continue
                pre = p[:s]
                anchor = max(last_pos(pre, MALE), pre.rfind('他'))
                if anchor < 0 or last_pos(pre, LUQI) > anchor:
                    continue
                if any(x in pre[anchor:] for x in FEMO):
                    continue
                if not any(x in ctx for x in LUQI):
                    continue
                # 受事是"孩子/老人/家人"等明确他人 -> 排除
                A.append({'f': fn, 'i': i, 'para': p})
            # ---- B类 ----
            if subj_is_luqi(prev):
                for m in TAGS.finditer(p):
                    s = m.start()
                    if p[:s].count('"') % 2 == 1:
                        continue
                    post = p[s:s + 14]
                    if any(x in post for x in MALE + LUQI + FEMO):
                        continue
                    B.append({'f': fn, 'i': i, 'para': p})
    print('A:', len(A), ' B:', len(B))
    json.dump({'A': A, 'B': B}, open('/tmp/opencode/ab2.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


run()
