#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三部 补充扫描：两类漏网错误
  A类 宾语位「他」：男性主语 + 及物动词 + 他，而受事者只可能是陆栖
  B类 对话标签「他说/他问」：引语说话人只可能是陆栖
全部输出供人工逐条核验（不自动改）。
"""
import glob, re, json

DIR = '/mnt/d/devProject/writer/novelist/旧书栖灵/正文/第三部'
MALE = ['林越', '周明远', '周先生', '方知远', '顾松年', '周维德', '林晓颂']
LUQI = ['陆栖', '陆老师', '陆馆长']
FEMO = ['苏晚', '顾念', '沈念', '阿棠']
# 及物动词：后接人称宾语
VERBS = (r'(?:看了看|看着|望着|盯着|瞅着|端详着|打量着|看了|瞅了|望了|盯了|'
         r'递给|交给|推给|塞给|扔给|握住|握了|拉住|抓住|扶着|扶了|'
         r'拍了拍|拍着|拍了一下|碰到|摸了摸|摸着|陪着|陪着说|守着|劝了|'
         r'想起|记得|想念|回应|回答|面对|朝向|对着|看着|叫了|喊了|请了|'
         r'谢谢|照顾|留给|看着|盯着|瞅着|打量|端详|瞅|盯|望|递|交|推|'
         r'握|拉|抓|扶|拍|碰|摸|陪|守|劝|问|叫|喊|请|谢|照顾|想|记|'
         r'对|跟|向|给|帮|留|回应|回答|面对)')
TAGS = re.compile(r'(?<![他她])他(说|问|答|喊|道|开口|回答|念|讲|轻声|喃喃)')


def last_pos(text, words):
    best = -1
    for w in words:
        p = text.rfind(w)
        if p > best:
            best = p
    return best


def run():
    A, B = [], []
    for path in sorted(glob.glob(DIR + '/*.md')):
        paras = open(path, encoding='utf-8').read().split('\n')
        fn = path.split('/')[-1]
        for i, p in enumerate(paras):
            if not p.strip() or p.lstrip().startswith('#'):
                continue
            if p.count('"') % 2 == 1:
                continue
            prev = paras[i - 1] if i > 0 else ''
            nxt = paras[i + 1] if i + 1 < len(paras) else ''
            # ---------- A类 ----------
            for m in re.finditer(VERBS + r'他(?!们|人|家|用|者|所)', p):
                s = m.start()
                if p[:s].count('"') % 2 == 1:
                    continue
                pre = p[:s]
                mp = last_pos(pre, MALE)
                tp = pre.rfind('他')
                lp = last_pos(pre, LUQI)
                if mp < 0 and tp < 0:
                    continue
                anchor = max(mp, tp)
                if lp > anchor:
                    continue
                if any(x in pre[anchor:] for x in FEMO):
                    continue
                # 陆栖 必须在近处语境中
                ctx = prev + p + nxt
                if not any(x in ctx for x in LUQI):
                    continue
                # 排除：受事明显是第三人（他/她 先行词、家人、孩子等）
                A.append({'f': fn, 'i': i, 's': s, 'para': p})
            # ---------- B类 ----------
            for m in TAGS.finditer(p):
                s = m.start()
                if p[:s].count('"') % 2 == 1:
                    continue
                # 该段引语归属：段内是否有名字在引号后
                post = p[s:s + 12]
                if any(x in post for x in MALE + LUQI + FEMO):
                    continue
                # 说话人 = 上一段主语 / 段内最后具名者
                lp_prev = last_pos(prev, LUQI)
                mp_prev = last_pos(prev, MALE)
                fp_prev = last_pos(prev, FEMO)
                if lp_prev < 0:
                    continue
                if mp_prev > lp_prev or fp_prev > lp_prev:
                    continue
                B.append({'f': fn, 'i': i, 's': s, 'para': p})
    print('A类(宾语位他)候选:', len(A), ' B类(对话标签他说)候选:', len(B))
    json.dump({'A': A, 'B': B}, open('/tmp/opencode/ab.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


run()
