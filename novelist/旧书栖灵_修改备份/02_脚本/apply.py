#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三部：已人工核验确认的 陆栖→「他」 性别代词错误 定点修正"""
import os, sys

DIR = '/mnt/d/devProject/writer/novelist/旧书栖灵/正文/第三部'

FIXES = [
    # (文件, 原文, 改文, 说明)
    ('第008章-寻找演奏者.md',
     '陆栖站在旁边，打量着他们。他想起自己第一次走进文献馆的那天，顾松年对他说的话：',
     '陆栖站在旁边，打量着他们。她想起自己第一次走进文献馆的那天，顾松年对她说的话：',
     '陆栖回忆自己初到文献馆、顾松年对她说话'),
    ('第008章-寻找演奏者.md',
     '现在他懂了。不只是书比人经得住放，故事也是。',
     '现在她懂了。不只是书比人经得住放，故事也是。',
     '承接上句「你慢慢就会懂了」，指陆栖听懂'),
    ('第012章-精灵的感动.md',
     '陆栖没有打扰他。他无声地地走到自己的办公桌前坐下，开始整理其他的旧书。',
     '陆栖没有打扰他。她无声地地走到自己的办公桌前坐下，开始整理其他的旧书。',
     '「自己的办公桌」= 陆栖自己的办公桌；前半句「他」=周明远，保留'),
]

total = 0
touched = set()
for fn, old, new, why in FIXES:
    p = os.path.join(DIR, fn)
    s = open(p, encoding='utf-8').read()
    n = s.count(old)
    if n != 1:
        print('!! 跳过（匹配 %d 次）: %s | %s' % (n, fn, old[:30]))
        continue
    s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8').write(s)
    total += n
    touched.add(fn)
    print('OK  %s  <-  %s' % (why, old[:34]))
print('---')
print('替换处数:', total, ' 涉及文件数:', len(touched))
