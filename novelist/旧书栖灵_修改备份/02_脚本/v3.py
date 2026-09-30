#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《旧书栖灵》第三部 性别代词修正 —— 保守版 v3
陆栖是女性。凡「他」指代陆栖者，改为「她」。

核心：
  1) 引号内「他」不动（台词内容多指他人/精灵）
  2) 「他们/他人/其他/他用」不动
  3) 判定「他」是主语还是宾语
       - 宾语：其前有 主语(人名/代词) + 动词  =>「他」是动作的对象
       - 主语：位于小句句首，其后接动词
  4) 宾语位：若该小句主语是男性角色，且场景中「他」只能是陆栖 -> 改
  5) 主语位：若所指代的最近行为主体是陆栖 -> 改
  全部条件必须在同一段或相邻场景窗口内成立，否则跳过。
"""
import glob, os, re, sys, json

DIR = '/mnt/d/devProject/writer/novelist/旧书栖灵/正文/第三部'

LUQI = ['陆栖', '陆老师', '陆馆长']
MALE = ['林越', '周明远', '周先生', '方知远', '方小远', '顾松年', '周维德',
        '林晓颂', '周慎之', '周小明', '周晓', '沈明远', '苏明远', '陈志远',
        '明远', '林先生', '老林']
FEMALE = ['苏晚晴', '苏晚', '顾念秋', '顾念', '沈念', '阿棠', '雪团', '陈老师']
# 精灵等非人角色（周维德的灵，视为男性）
SPIRIT = ['精灵', '书灵', '那个灵', '灵站']

TA_NEXT_SKIP = set('们人家用者所')

# 出现在「他/她」之后 -> 说明该代词是主语（后接动词/副词）
SUBJ_FOLLOW = set('说问答喊道叫笑点摇转抬低伸拿递推拉坐站走停闭睁看听想做用把'
                  '想能会要不没从未没有立刻马又也就还才更最都把被让给对跟和与'
                  '在到从向朝为替已经依旧始终一直依然忽然突然然后于是接着轻轻'
                  '慢慢缓缓静静终于终于微微终于非常很太非常并曾正刚再并且'
                  '而但可却则就只仅还偏偏好好坏快慢长短高低大小多少深浅轻重')
# 出现在「他/她」之后 -> 说明该代词是宾语（后接名词/量词）
OBJ_FOLLOW_STR = ('的', '一', '眼', '手', '脸', '肩', '声', '心', '动作', '皮肤',
                  '歌', '故事', '身', '背', '前', '面', '边', '上', '里', '下',
                  '指', '目光', '表情', '姿态', '侧脸', '笔记', '乐谱', '书',
                  '信封', '竹笛', '相册', '名字', '照片', '电话', '门', '灯',
                  '茶', '水', '杯', '衣', '发', '字', '话', '屋', '窗', '门',
                  '表情', '反应', '回答', '眼睛', '目光', '手掌', '掌心')

LEAD_STRIP = re.compile(r'^[""\[\]【】（）()\s,，、。—\-…]*')


def spans(text, words):
    out = []
    for w in words:
        for m in re.finditer(re.escape(w), text):
            out.append((m.start(), m.end(), w))
    out.sort()
    res, last = [], -1
    for s, e, w in out:
        if s >= last:
            res.append((s, e, w))
            last = e
    return res


def in_quote(text, pos):
    return text[:pos].count('"') % 2 == 1


def clause_bounds(text, pos):
    """返回 (start, end) —— 以标点切分的小句"""
    seps = '。！？；\n'
    s = pos
    while s > 0 and text[s - 1] not in seps:
        s -= 1
    e = pos
    while e < len(text) and text[e] not in seps:
        e += 1
    return s, e


def classify(text, pos):
    """返回 'OBJ' / 'SUBJ' / 'UNK'"""
    nxt = text[pos + 1] if pos + 1 < len(text) else ''
    nxt2 = text[pos + 1:pos + 3]
    # 宾语信号：后接名词/量词
    for pre in OBJ_FOLLOW_STR:
        if nxt2.startswith(pre) and pre in ('的', '一', '眼', '手', '脸', '肩', '身'):
            return 'OBJ'
    if nxt2.startswith('的'):
        return 'OBJ'
    if nxt in '一' or nxt2.startswith('一下') or nxt2.startswith('一眼'):
        return 'OBJ'
    if nxt in '声心':
        return 'OBJ'
    # 主语信号：位于小句开头
    cs, ce = clause_bounds(text, pos)
    pre_txt = text[cs:pos]
    st = LEAD_STRIP.sub('', pre_txt)
    if not st:
        return 'SUBJ'
    # 前文只有连接词/副词 -> 仍是主语
    if re.fullmatch(r'(但|而|可|可是|不过|然后|于是|接着|这时|现在|后来|忽然|突然|'
                    r'又|再|也|还是|只是|因为|所以|如果|当|在|从|用|把|被|让|给|'
                    r'向|朝|对|跟|和|与|为|替|已经|依旧|始终|一直|依然|就|才|更|'
                    r'最|都|还|像|仿佛|好像|似乎|其实|当然|最后|最初)*', st):
        return 'SUBJ'
    return 'OBJ'


def scan(path):
    text = open(path, encoding='utf-8').read()
    paras = text.split('\n')
    props = []
    # 场景窗口：最近出现过的角色（滑动窗口，取最近 4 段）
    window = []

    def push(chars):
        for c in chars:
            if c in window:
                window.remove(c)
            window.append(c)

    for li, para in enumerate(paras):
        if not para.strip() or para.lstrip().startswith('#'):
            continue
        luqi_here = spans(para, LUQI)
        male_here = spans(para, MALE)
        fem_here = spans(para, FEMALE)
        spirit_here = spans(para, SPIRIT)

        present = set()
        for _, _, w in luqi_here:
            present.add('LUQI')
        for _, _, w in male_here:
            present.add('M:' + w)
        for _, _, w in fem_here:
            present.add('F:' + w)
        for _, _, w in spirit_here:
            present.add('S:' + w)
        push(present)

        if para.count('"') % 2 == 1:
            continue

        targets = []
        for m in re.finditer('他', para):
            p = m.start()
            if p + 1 < len(para) and para[p + 1] in TA_NEXT_SKIP:
                continue
            if in_quote(para, p):
                continue
            targets.append(p)

        for p in targets:
            kind = classify(para, p)
            cs, ce = clause_bounds(para, p)
            clause = para[cs:ce]
            # 小句主语
            male_in_clause = [(s, w) for s, e, w in male_here if cs <= s < p]
            luqi_in_clause = [(s, w) for s, e, w in luqi_here if cs <= s < p]
            fem_in_clause = [(s, w) for s, e, w in fem_here if cs <= s < p]
            last_male = male_in_clause[-1][0] if male_in_clause else -1
            last_luqi = luqi_in_clause[-1][0] if luqi_in_clause else -1
            last_fem = fem_in_clause[-1][0] if fem_in_clause else -1

            reason = None
            do = False
            if kind == 'OBJ':
                # 该他为动作对象。小句内若有男性主语 -> 对象应为在场的陆栖
                if last_male > last_luqi and last_male > last_fem:
                    # 场景窗口内：陆栖在，其他女性不在，无精灵独角
                    win_luqi = any(x == 'LUQI' for x in window)
                    win_fem = any(x.startswith('F:') for x in window)
                    win_spirit = any(x.startswith('S:') for x in window)
                    win_male = set(x for x in window if x.startswith('M:'))
                    if win_luqi and not win_fem and not win_spirit and len(win_male) == 1:
                        do = True
                        reason = 'OBJ:主语=%s,对象=陆栖' % male_in_clause[-1][1]
                    else:
                        reason = 'OBJ:场景不唯一(陆栖%s,其他女性%s,精灵%s,男性%s)' % (
                            win_luqi, win_fem, win_spirit, len(win_male))
                else:
                    reason = 'OBJ:小句主语非男性(%s)' % (
                        '陆栖' if last_luqi > -1 else ('其他女性' if last_fem > -1 else '无'))
            else:
                # 主语位：看最近行为主体
                if last_luqi > last_male and last_luqi > last_fem and luqi_in_clause:
                    do = True
                    reason = 'SUBJ:小句内最近主体=陆栖'
                elif luqi_in_clause and not male_in_clause and not fem_in_clause and not spirit_here:
                    do = True
                    reason = 'SUBJ:小句内仅陆栖'
                else:
                    reason = 'SUBJ:主体不确定'

            if do:
                props.append({'line': li, 'pos': p, 'reason': reason,
                              'ctx': para[max(0, p - 55):p + 30]})
    return paras, props


def main():
    allp = []
    for path in sorted(glob.glob(os.path.join(DIR, '*.md'))):
        paras, props = scan(path)
        if props:
            allp.append((os.path.basename(path), props))
    print('文件数', len(allp), '候选', sum(len(x[1]) for x in allp))
    json.dump([{'file': f, 'props': p} for f, p in allp],
              open('/tmp/opencode/v3.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


main()
