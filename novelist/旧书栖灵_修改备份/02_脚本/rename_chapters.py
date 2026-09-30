# -*- coding: utf-8 -*-
import os, sys

BASE = "/mnt/d/devProject/writer/novelist/旧书栖灵/正文"

# (part, num, old_filename_title, old_h1_title, new_title)
ENTRIES = [
    ("第二部", "003", "林越的第一个星期", "老街的黄昏", "林越的第一个星期"),
    ("第二部", "070", "晚风年年都来", "晚风年年都来", "桂花糖与故事集"),
    ("第三部", "045", "林越的参与", "林越的参与", "老城区记忆馆"),
    ("第三部", "059", "苏晚的参与", "苏晚的参与", "三本笔记"),
    ("第三部", "060", "周明远的配乐", "周明远的配乐", "被涂掉的名字"),
    ("第三部", "061", "划掉的那一行", "故事的完成", "划掉的那一行"),
    ("第四部", "004", "口袋里揣了六天", "林越的困惑", "口袋里揣了六天"),
    ("第四部", "005", "苏晚的成长", "苏晚的成长", "三块钱的煤球炉"),
    ("第四部", "013", "种子的发现", "种子的发现", "三粒旧种子"),
    ("第四部", "031", "林越的重新融入", "林越的重新融入", "五十四级台阶"),
    ("第四部", "057", "陆栖的成长", "陆栖的成长", "四千零一十一行"),
    ("第四部", "064", "精灵的祝福", "精灵的祝福", "我是那个夏天"),
    ("第四部", "065", "林越的承诺", "林越的承诺", "造册者不署名"),
    ("第四部", "066", "苏晚的未来", "苏晚的未来", "明年春天之前"),
    ("第四部", "070", "新的开始", "新的开始", "灯火暖人"),
    ("第六部", "006", "林晓颂的第一课", "新一代的学习", "林晓颂的第一课"),
    ("第六部", "012", "带不走的种子", "新一代的贡献", "带不走的种子"),
    ("第六部", "019", "回声的永恒", "回声的永恒", "掌纹里的微光"),
    ("第六部", "020", "写完最后一页", "永恒的完成", "写完最后一页"),
    ("第六部", "022", "把手艺交出去", "传承的完成", "把手艺交出去"),
    ("第六部", "023", "她自己的钥匙", "新一代的独立", "她自己的钥匙"),
    ("第六部", "024", "看着他们走远", "陆栖的满足", "看着他们走远"),
    ("第六部", "025", "老同事的下午茶", "林越的陪伴", "老同事的下午茶"),
    ("第六部", "038", "林越的礼物", "林越的礼物", "一枚常明"),
    ("第六部", "043", "永恒的守护", "永恒的守护", "断了一根枝"),
    ("第六部", "049", "灯下的第七个十年", "永恒的守望", "灯下的第七个十年"),
]

def fmt(num, title):
    return "第{}章-{}".format(num, title)

def fmt_h1(num, title):
    return "第{}章 {}".format(num, title)

def main():
    errors = []
    for part, num, old_file_title, old_h1_title, new_title in ENTRIES:
        old_path = os.path.join(BASE, part, fmt(num, old_file_title) + ".md")
        new_path = os.path.join(BASE, part, fmt(num, new_title) + ".md")

        # 1) rename file if needed (idempotent)
        old_exists = os.path.exists(old_path)
        new_exists = os.path.exists(new_path)
        if old_file_title != new_title:
            if new_exists and not old_exists:
                pass  # already renamed
            elif not new_exists and old_exists:
                os.rename(old_path, new_path)
                print("[RENAME] {} -> {}".format(fmt(num, old_file_title) + ".md", fmt(num, new_title) + ".md"))
            else:
                errors.append("[RENAME-CONFLICT] {}".format(new_path))
                continue
            path = new_path
        else:
            if not new_exists:
                errors.append("[MISS-FILE] {}".format(new_path))
                continue
            path = new_path

        # 2) sync H1 line (idempotent)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            errors.append("[EMPTY] {}".format(path))
            continue
        already = "# " + fmt_h1(num, new_title)
        if lines[0].rstrip("\r\n") == already:
            print("[H1-OK-ALREADY] {}".format(new_path))
            continue
        h1_old = "# " + fmt_h1(num, old_h1_title)
        got = lines[0].rstrip("\r\n")
        if got != h1_old:
            errors.append("[H1-MISMATCH] {}: got={!r} want={!r}".format(path, got, h1_old))
            continue
        lines[0] = already + "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("[H1] {} : {} -> {}".format(num, h1_old, "# " + fmt(num, new_title)))

    if errors:
        print("\n==== ERRORS ====")
        for e in errors:
            print(e)
        sys.exit(1)
    print("\nALL OK - {} entries processed".format(len(ENTRIES)))

if __name__ == "__main__":
    main()