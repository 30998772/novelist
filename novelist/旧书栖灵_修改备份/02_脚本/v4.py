#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4：穷尽式共指消解。列出所有「他」 antecedent == 陆栖 的候选。
包含泛指名词作为 antecedent，避免把别人的「他」误记到陆栖头上。
"""
import glob, os, re, sys, json

DIR = '/mnt/d/devProject/writer/novelist/旧书栖灵/正文/第三部'

LUQI = ['陆栖', '陆老师', '陆馆长']
MALE = ['林越', '周明远', '周先生', '方知远', '方小远', '顾松年', '周维德',
        '林晓颂', '周慎之', '周小明', '周晓', '沈明远', '苏明远', '陈志远',
        '明远', '老林']
FEM = ['苏晚晴', '苏晚', '顾念秋', '顾念', '沈念', '阿棠', '雪团', '陈老师']
# 泛指：按出现顺序优先匹配长的
GENERIC_M = ['那个身影', '身影', '那个灵', '精灵', '书灵', '灵', '男人', '男孩',
             '老先生', '老人', '孩子', '父亲', '爸爸', '儿子', '外婆', '爷爷',
             '老伴', '同学', '同事', '朋友', '陌生人', '客人', '读者', '读者们',
             '指挥家', '作曲家', '植物学家', '盲人', '乐手', '乐手们', '刘叔',
             '小陈', '王阿姨', '陈守仁', '陈国华', '李文渊', '王雪莹', '顾松年',
             '大家', '人们', '别人', '所有人', '人们']
GENERIC_F = ['女人', '女孩', '女孩儿', '母亲', '妈妈', '女儿', '外婆', '奶奶',
             '老太太', '女士', '姑娘', '苏']
TA_NEXT_SKIP = set('们人家用者所')

ALL_WORDS = LUQI + MALE + FEM + GENERIC_M + GENERIC_F


def find_all(text):
    """返回按位置排序的 (start, end, kind, word)"""
    out = []
    for w in LUQI:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), m.end(), 'LUQI', w))
    for w in FEM:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), m.end(), 'F', w))
    for w in MALE:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), m.end(), 'M', w))
    for w in GENERIC_M:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), m.end(), 'M', w))
    for w in GENERIC_F:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), m.end(), 'F', w))
    out.sort()
    res, last = [], -1
    for s, e, k, w in out:
        if s >= last:
            res.append((s, e, k, w))
            last = e
    return res


def main():
    hits = []
    stats = {'LUQI': 0, 'M': 0, 'F': 0, 'NONE': 0, 'skip': 0}
    for path in sorted(glob.glob(os.path.join(DIR, '*.md'))):
        lines = open(path, encoding='utf-8').read().split('\n')
        # 文档级 antecedent 栈
        doc_ante = None          # 最近的男性 antecedent
        para_ante = None         # 段内最近 antecedent
        for li, para in enumerate(lines):
            if not para.strip() or para.lstrip().startswith('#'):
                continue
            events = find_all(para)
            tas = []
            for m in re.finditer('他', para):
                p = m.start()
                if p + 1 < len(para) and para[p + 1] in TA_NEXT_SKIP:
                    continue
                if para[:p].count('"') % 2 == 1:
                    continue
                tas.append(p)
            # 合并事件流
            stream = [(s, 'ref', k, w) for s, e, k, w in events]
            stream += [(p, 'ta', None, None) for p in tas]
            stream.sort(key=lambda x: x[0])
            for (s, typ, k, w) in stream:
                if typ == 'ref':
                    if k in ('M', 'LUQI'):
                        para_ante = w if k == 'M' else '陆栖'
                        doc_ante = w if k == 'M' else '陆栖'
                    else:
                        para_ante = 'F:' + w
                        doc_ante = None   # 女性不作为「他」的 antecedent
                else:
                    if para_ante is None:
                        para_ante = doc_ante
                    a = para_ante
                    if a is None:
                        stats['NONE'] += 1
                    elif a.startswith('F:'):
                        stats['F'] += 1
                    elif a == '陆栖':
                        stats['LUQI'] += 1
                        hits.append({'file': os.path.basename(path), 'line': li,
                                     'pos': s, 'para': para})
                    else:
                        stats['M'] += 1
                    # 该「他」成为最近 antecedent
                    para_ante = '他'
                    doc_ante = '他'
    print(stats)
    print('陆栖候选数:', len(hits))
    json.dump(hits, open('/tmp/opencode/v4.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


main()
