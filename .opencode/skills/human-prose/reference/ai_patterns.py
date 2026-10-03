#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 腔复发型扫描：模板总结句 + 万能情绪套语 + 批量替换疤

用法:
    python3 ai_patterns.py 正文/第一部
    python3 scars.py 正文/第一部        # 单独跑疤痕检测

⚠️ 已知误报（不要当判废线）:
    模板总结句的正则会命中**书里正在被讨论的模板句**、以及
    书灵"抄写"的文书（如旧报刊上的套话）。命中后必须回读判断，
    不能机械删除。
"""
import re
import glob
import os
import sys

# ---- 一、模板总结句 + 万能情绪套语（human-prose §6.1 / §6.2）
PATS = [
    ('模板总结句', r'这就是[^\n。]{0,10}——不只是'),
    ('模板总结句', r'[^。\n]{0,20}的力量——它不只是'),
    ('万能情绪套语', r'心里涌起一种'),
    ('万能情绪套语', r'眼睛里闪着光'),
    ('万能情绪套语', r'眼底(?:掠过|闪过)[^\n。]{0,10}(?:光|泪|笑意)'),
    ('万能情绪套语', r'心中(?:涌起|升起)一'),
    ('万能情绪套语', r'一股(?:暖流|暖意)[^\n。]{0,8}涌'),
    ('陈词滥调', r'那是.{0,12}的歌。'),
    ('陈词滥调', r'没有尽头'),
    ('陈词滥调', r'岁月(?:静好|如梭)'),
    ('陈词滥调', r'仿佛(?:时间|岁月)'),
    ('固定结尾', r'年年都来的风'),
    ('固定结尾', r'古老的摇篮曲'),
    ('固定结尾', r'不是一个人守护一个地方'),
    ('固定结尾', r'她不是一个人在战斗'),
    ('固定结尾', r'永不停歇'),
    ('固定结尾', r'灯火(?:一直|永远)(?:亮着|亮着不灭)'),
]

# ---- 二、批量替换留下的疤（human-prose §6.4）
# 必须正向断言 (?=看着)，否则「在她听不见」「念给她听的」全是误报
SCAR_POS = re.compile(r'(?:站在|坐在|跪在|在)[^，。！？—]{1,4}[她他](?=看着)')
SCAR_NEG = re.compile(r'(?:站在|坐在|跪在|在)[^，。！？—]{0,4}'
                      r'(?:听不|念给|看不|看得|看见了)')


def scan(paths):
    hit = {}
    for f in paths:
        t = open(f, encoding='utf-8').read()
        for label, pat in PATS:
            for m in re.finditer(pat, t):
                hit.setdefault(label, []).append(
                    (os.path.basename(f), t[max(0, m.start() - 20):m.end() + 12]
                     .replace('\n', ' ')))
    if not hit:
        print('✅ 无复发型命中')
        return
    for label, rows in hit.items():
        print(f'\n⚠ {label}  {len(rows)} 处')
        for fn, ctx in rows[:12]:
            print(f'   {fn[:26]:<28} …{ctx}…')
        if len(rows) > 12:
            print(f'   …另 {len(rows)-12} 处')


def scan_scars(paths):
    n = 0
    for f in paths:
        t = open(f, encoding='utf-8').read()
        for i, l in enumerate(t.split('\n'), 1):
            if SCAR_POS.search(l) and not SCAR_NEG.search(l):
                print(f'  {os.path.basename(f)}:{i}  {l.strip()[:70]}')
                n += 1
    print(f'\n替换疤 {n} 处' if n else '\n✅ 无替换疤')


def main():
    a = sys.argv[1:]
    paths = []
    for p in (a or ['正文']):
        paths += sorted(glob.glob(p + '/**/*.md', recursive=True)) \
            if os.path.isdir(p) else sorted(glob.glob(p))
    if not paths:
        print('未找到章节文件'); return
    print(f'扫描 {len(paths)} 章\n' + '=' * 60)
    scan(paths)
    if '--scars' in a:
        print('\n' + '=' * 60)
        scan_scars(paths)


if __name__ == '__main__':
    main()
