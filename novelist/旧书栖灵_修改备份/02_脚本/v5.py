#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v5：共指消解 + 主宾位判定。
  - 段内/文档级维护 cur（最近人物）与 other（场景中另一人物）
  - 宾语位「他」-> antecedent = other（主语是别人）
  - 主语位「他」-> antecedent = cur
输出 antecedent==陆栖 的全部候选，供人工核验。
"""
import glob, os, re, json

DIR = '/mnt/d/devProject/writer/novelist/旧书栖灵/正文/第三部'
LUQI = ['陆栖', '陆老师', '陆馆长']
MALE = ['林越', '周明远', '周先生', '方知远', '方小远', '顾松年', '周维德',
        '林晓颂', '周慎之', '周小明', '周晓', '沈明远', '苏明远', '陈志远',
        '明远', '老林']
FEM = ['苏晚晴', '苏晚', '顾念秋', '顾念', '沈念', '阿棠', '雪团']
GEN_M = ['那个身影', '身影', '那个灵', '精灵', '书灵', '男人', '男孩', '老先生',
         '老人', '孩子', '父亲', '爸爸', '儿子', '外婆', '爷爷', '老伴',
         '指挥家', '作曲家', '植物学家', '盲人', '刘叔', '小陈', '王阿姨',
         '陈守仁', '陈国华', '李文渊', '王雪莹', '同学', '同事', '朋友',
         '陌生人', '客人', '乐手', '大家', '人们', '别人', '所有人']
GEN_F = ['女人', '女孩', '母亲', '妈妈', '女儿', '奶奶', '老太太', '女士', '姑娘']
TA_NEXT_SKIP = set('们人家用者所')

# 「他」后接 -> 主语；「他」后接名词/量词 -> 宾语
OBJ_NEXT = ('的', '一', '眼', '手', '脸', '肩', '声', '心', '身', '背', '前',
            '面', '边', '上', '里', '下', '指', '眼', '头', '次', '首', '件',
            '本', '张', '块', '条', '个', '只', '把', '支', '份', '种', '位',
            '名字', '话', '字', '书', '信', '门', '灯', '茶', '水', '杯',
            '乐谱', '笔记', '照片', '信纸', '纸', '谱', '曲子', '旋律')
LEAD_ONLY = re.compile(r'^(但|而|可|可是|不过|然后|于是|接着|这时|这时候|现在|'
                        r'后来|忽然|突然|又|再|也|还是|只是|因为|所以|如果|当|'
                        r'在|从|用|把|被|让|给|向|朝|对|跟|和|与|为|替|已经|'
                        r'依旧|始终|一直|依然|就|才|更|最|都|还|像|仿佛|好像|'
                        r'似乎|其实|当然|最后|最初|最|另|另一次|一次)*')


def refs(text):
    out = []
    for w in LUQI:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), 'LUQI', w))
    for w in FEM:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), 'F', w))
    for w in MALE:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), 'M', w))
    for w in GEN_M:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), 'M', w))
    for w in GEN_F:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), 'F', w))
    out.sort()
    res, last = [], -1
    for s, k, w in out:
        if s >= last:
            res.append((s, k, w))
            last = s + len(w)
    return res


def is_object(para, p):
    nxt = para[p + 1:p + 3]
    if nxt.startswith('的'):
        return True
    if nxt[:1] and nxt[0] in '一':
        # 他一眼 / 他一下 / 他一个 —— 宾语；但「他一」也可能是主语后接数量
        return True
    for o in OBJ_NEXT:
        if nxt.startswith(o) and o not in ('把', '上', '下', '里', '个', '只', '前', '面'):
            return True
    # 位于小句首 -> 主语
    i = p
    while i > 0 and para[i - 1] not in '。！？；\n':
        i -= 1
    pre = para[i:p]
    st = re.sub(r'^[""\[\]【】（）()\s,，、。—\-…]*', '', pre)
    if not st or LEAD_ONLY.fullmatch(st):
        return False
    return False


def main():
    hits = []
    stats = {'LUQI': 0, 'M': 0, 'F': 0, 'NONE': 0}
    for path in sorted(glob.glob(os.path.join(DIR, '*.md'))):
        lines = open(path, encoding='utf-8').read().split('\n')
        cur = other = None
        for li, para in enumerate(lines):
            if not para.strip() or para.lstrip().startswith('#'):
                continue
            R = refs(para)
            T = []
            for m in re.finditer('他', para):
                p = m.start()
                if p + 1 < len(para) and para[p + 1] in TA_NEXT_SKIP:
                    continue
                if para[:p].count('"') % 2 == 1:
                    continue
                T.append(p)
            stream = [(s, 'R', k, w) for s, k, w in R] + [(p, 'T', None, None) for p in T]
            stream.sort(key=lambda x: x[0])
            for (s, typ, k, w) in stream:
                if typ == 'R':
                    if k == 'LUQI':
                        cur = '陆栖'
                    elif k == 'M':
                        if cur == '陆栖':
                            other = w
                        cur = 'M:' + w
                    else:
                        cur = 'F:' + w
                else:
                    if is_object(para, s):
                        a = other
                    else:
                        a = cur
                    if a is None:
                        stats['NONE'] += 1
                    elif a == '陆栖':
                        stats['LUQI'] += 1
                        hits.append({'file': os.path.basename(path), 'line': li,
                                     'pos': s, 'para': para})
                    elif a.startswith('F:'):
                        stats['F'] += 1
                    else:
                        stats['M'] += 1
                    cur = '他'
    print(stats, '陆栖候选:', len(hits))
    json.dump(hits, open('/tmp/opencode/v5.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


main()
