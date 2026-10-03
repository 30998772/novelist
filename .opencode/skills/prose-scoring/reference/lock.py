#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定稿锁校验。

用法：
    python3 lock.py --lock     # 对当前定稿范围生成/刷新哈希清单
    python3 lock.py            # 校验：范围内文件是否与清单一致

范围由 LOCK_SCOPE 决定（正文/第一部 + 章节大纲/第一部）。
修订前跑一次校验，返回非 0 即表示定稿已被改动。
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
BOOK = 'novelist/他们说我是来替他挡灾的'
MANIFEST = os.path.join(ROOT, BOOK, '_定稿锁.json')

# 已定稿、后续不允许改动的范围
LOCK_SCOPE = [
    '正文/第一部',          # 第一部正文 36 章（_ 前缀文件不计，那是说明与总账）
    '章节大纲/第一部',      # 只固定第一部的章节大纲
    '章节大纲/总纲.md',    # 全书总纲：内含第一部定案，改动会波及第一部
]


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def collect():
    out = {}
    for scope in LOCK_SCOPE:
        base = os.path.join(ROOT, BOOK, scope)
        if os.path.isfile(base):
            txt = re.sub(r'<!--.*?-->', '', open(base, encoding='utf-8').read(), flags=re.S)
            rel = os.path.relpath(base, ROOT).replace(chr(92), '/')
            out[rel] = hashlib.sha256(txt.encode()).hexdigest()
            continue
        for dirpath, _dirs, files in os.walk(base):
            for fn in sorted(files):
                if not fn.endswith('.md'):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
                out[rel.replace('\\', '/')] = digest(os.path.join(dirpath, fn))
    return out


def norm(sha):
    """忽略章末 <!-- 修订 --> 注释块——它是修订史，不算正文改动。"""
    h = hashlib.sha256()
    h.update(sha.encode())
    return h.hexdigest()


def collect_relaxed():
    out = {}
    for scope in LOCK_SCOPE:
        base = os.path.join(ROOT, BOOK, scope)
        for dirpath, _dirs, files in os.walk(base):
            for fn in sorted(files):
                if not fn.endswith('.md') or fn.startswith('_'):
                    continue
                # 说明性目录不进锁：归档说明、评分历史等
                rel_dir = os.path.relpath(dirpath, base).replace('\\', '/')
                if rel_dir != '.' and any(
                        k in rel_dir for k in ('评分历史', '过程稿', '归档')):
                    continue
                p = os.path.join(dirpath, fn)
                t = open(p, encoding='utf-8').read()
                t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
                rel = os.path.relpath(p, ROOT).replace('\\', '/')
                out[rel] = hashlib.sha256(t.encode()).hexdigest()
    return out


def main():
    if not os.path.isdir(ROOT):
        print('找不到仓库根：%s' % ROOT)
        return 2
    cur = collect_relaxed()
    if '--lock' in sys.argv:
        json.dump(cur, open(MANIFEST, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1, sort_keys=True)
        print('已锁定 %d 个文件 -> _定稿锁.json' % len(cur))
        return 0
    if not os.path.exists(MANIFEST):
        print('未找到定稿锁清单，请先跑 lock.py --lock')
        return 2
    old = json.load(open(MANIFEST, encoding='utf-8'))
    added = sorted(set(cur) - set(old))
    removed = sorted(set(old) - set(cur))
    changed = sorted(k for k in set(cur) & set(old) if cur[k] != old[k])
    if not (added or removed or changed):
        print('定稿锁校验通过：%d 个文件全部未改动' % len(cur))
        return 0
    print('!! 定稿锁校验失败 —— 以下文件在锁定后被改动：')
    for k in changed:
        print('   改  %s' % k)
    for k in added:
        print('   增  %s' % k)
    for k in removed:
        print('   删  %s' % k)
    print('第一部正文与第一部章节大纲已定稿，不允许再改。')
    print('确需改动请先跑 `python3 lock.py --lock` 重新锁定并说明理由。')
    return 1


if __name__ == '__main__':
    sys.exit(main())
