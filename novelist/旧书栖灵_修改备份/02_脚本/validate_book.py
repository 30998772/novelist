# -*- coding: utf-8 -*-
"""Validate 旧书栖灵 after chapter renames:
1) no duplicate chapter titles across 正文
2) every 正文 file H1 title equals its filename title (known exceptions reported)
3) 逐章卡片 headings match 正文 chapter title for the same part+number
"""
import os
import re
import glob
import sys

BASE = "/mnt/d/devProject/writer/novelist/旧书栖灵"

# kept chapters where filename title != H1 title (expected)
KNOWN_EXCEPTIONS = {
    ("第三部", 54),  # 苏晚的册子 / 苏晚的参与
    ("第三部", 55),  # 共鸣不是单向的 / 周明远的配乐
}

file_re = re.compile(r"^第(\d+)章-(.+)\.md$")
h1_re = re.compile(r"^# 第(\d+)章 (.+?)\s*$")
card_re = re.compile(r"^### 第(\d+)章?[:： ]+(.+?)\s*$")


def chapter_files():
    out = []
    for part in sorted(os.listdir(os.path.join(BASE, "正文"))):
        pdir = os.path.join(BASE, "正文", part)
        if not os.path.isdir(pdir):
            continue
        for fn in sorted(os.listdir(pdir)):
            m = file_re.match(fn)
            if not m:
                continue
            num = int(m.group(1))
            title = m.group(2)
            path = os.path.join(pdir, fn)
            with open(path, "r", encoding="utf-8") as f:
                first = f.readline()
            hm = h1_re.match(first.rstrip("\r\n"))
            h1_title = hm.group(2) if hm else None
            out.append((part, num, title, h1_title, path))
    return out


def main():
    errors = []
    warns = []
    files = chapter_files()

    # 1) duplicate titles across whole book
    seen = {}
    for part, num, title, _, path in files:
        seen.setdefault(title, []).append("{} 第{}章".format(part, num))
    for title, locs in sorted(seen.items()):
        if len(locs) > 1:
            errors.append("DUPLICATE title {!r}: {}".format(title, ", ".join(locs)))

    # 2) H1 vs filename
    for part, num, ftitle, h1title, path in files:
        if h1title is None:
            errors.append("NO-H1 {}: first line not a valid H1".format(path))
            continue
        if ftitle != h1title:
            if (part, num) in KNOWN_EXCEPTIONS:
                warns.append("KNOWN-EXCEPTION {} {}: file={!r} h1={!r}".format(part, num, ftitle, h1title))
            else:
                errors.append("H1-VS-FILE {} 第{}章: file={!r} h1={!r}".format(part, num, ftitle, h1title))

    # 3) cards vs 正文
    by_part = {}
    for part, num, title, _, _ in files:
        by_part.setdefault(part, {})[num] = title
    for cardfile in sorted(glob.glob(os.path.join(BASE, "章节大纲", "*", "逐章卡片.md"))):
        part = os.path.basename(os.path.dirname(cardfile))
        with open(cardfile, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                m = card_re.match(line.rstrip("\r\n"))
                if not m:
                    continue
                num = int(m.group(1))
                ctitle = m.group(2).strip()
                body = by_part.get(part, {})
                if num in body:
                    if body[num] != ctitle:
                        errors.append("CARD-MISMATCH {} {} line {}: card={!r} file={!r}".format(
                            part, num, lineno, ctitle, body[num]))
                else:
                    warns.append("CARD-ORPHAN {} line {}: card chapter {} {!r} has no 正文 file".format(
                        part, lineno, num, ctitle))

    print("checked {} chapter files".format(len(files)))
    for w in warns:
        print("WARN:", w)
    if errors:
        print("==== ERRORS ({} ) ====".format(len(errors)))
        for e in errors:
            print(e)
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()