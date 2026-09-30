#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《旧书栖灵》第三部 性别代词修正
主角陆栖为女性 -> 「他」应作「她」
保守策略：宁可漏改，不可错改
"""
import glob, os, re, sys, json

DIR = '/mnt/d/devProject/writer/novelist/旧书栖灵/正文/第三部'

LUQI = ['陆栖', '陆老师', '陆馆长']
MALE = ['林越', '周明远', '周先生', '方知远', '方小远', '顾松年', '周维德',
        '林晓颂', '周慎之', '周小明', '周晓', '沈明远', '苏明远', '陈志远']
FEMALE_OTHER = ['苏晚晴', '苏晚', '顾念秋', '顾念', '沈念']

# 男性代词后不可接的字（复数/其他用法）
TA_SKIP_NEXT = set('们��老家用者所')

SPEECH = re.compile(r'(说|问|答|喊|道|开口|回答|念|讲)')


def is_luqi(t):
    return any(t in x for x in LUQI)


class Char:
    __slots__ = ('name', 'gender')

    def __init__(self, name, gender):
        self.name, self.gender = name, gender

    def __repr__(self):
        return '%s(%s)' % (self.name, self.gender)


def find_names(text):
    """返回 [(pos, Char)] 按位置排序，长名优先"""
    out = []
    for n in LUQI:
        for m in re.finditer(re.escape(n), text):
            out.append((m.start(), Char(n, 'F')))
    for n in FEMALE_OTHER:
        for m in re.finditer(re.escape(n), text):
            out.append((m.start(), Char(n, 'F')))
    for n in MALE:
        for m in re.finditer(re.escape(n), text):
            out.append((m.start(), Char(n, 'M')))
    out.sort(key=lambda x: x[0])
    # 去重叠（保留长的/先出现的）
    res = []
    last_end = -1
    for pos, c in out:
        if pos >= last_end:
            res.append((pos, c))
            last_end = pos + len(c.name)
    return res


def para_segments(para):
    """把段落切成句子片段: [(start, end, in_quote)]"""
    segs = []
    inq = False
    start = 0
    for i, ch in enumerate(para):
        if ch == '"':
            if not inq:
                segs.append((start, i, False))
                inq = True
            else:
                segs.append((i, i + 1, False))
                inq = False
            start = i + 1
        elif ch in '。！？' and not inq:
            segs.append((start, i + 1, False))
            start = i + 1
    if start < len(para):
        segs.append((start, len(para), inq))
    return [s for s in segs if s[1] > s[0]]


SUBJ_LEAD = re.compile(r'^[\s""''（）()【】\[\]，、。—\-…\w]*$')


def process(path, apply=False):
    src = open(path, encoding='utf-8').read()
    paras = src.split('\n')
    changes = []
    skipped = []
    # 全局状态
    actor = None          # 当前最可能的「他/她」指代
    last_named = None     # 最近提到的角色
    others = []           # 本场景出现过的其他角色

    for pi, para in enumerate(paras):
        if not para.strip() or para.lstrip().startswith('#'):
            continue
        names = find_names(para)
        # 记录本段出现的角色
        for _, c in names:
            if c not in others:
                others.append(c)
        para_has_luqi = any(c.gender == 'F' and is_luqi(c.name) for _, c in names)
        other_females = [c for c in others if c.gender == 'F' and not is_luqi(c.name)]
        male_present = [c for c in others if c.gender == 'M']

        # 定位所有非引号内的「他」
        targets = []  # (pos, is_first_in_sentence, seg_start)
        for (ss, se, inq) in para_segments(para):
            if inq:
                continue
            for m in re.finditer('他', para[ss:se]):
                p = m.start() + ss
                nxt = para[p + 1] if p + 1 < len(para) else ''
                if nxt in TA_SKIP_NEXT:
                    continue
                targets.append(p)

        # 说话人推断：先按顺序扫描「说话事件」
        # 模式1: 名字 + 说/问…  + 引号  -> 该名字说话
        # 模式2: 引号 紧跟 名字        -> 该名字说话
        speaker_events = []  # (pos_after, Char)
        for m in re.finditer(r'([^"]{0,25}?)"([^"]{0,200}?)"', para):
            pass
        # 简化：遍历引号对，判断说话人
        quote_spans = [(m.start(), m.end()) for m in re.finditer(r'"[^"]*"', para)]
        for qs, qe in quote_spans:
            pre = para[max(0, qs - 30):qs]
            post = para[qe:qe + 30]
            pre_names = find_names(pre)
            post_names = find_names(post[:12])
            spk = None
            # 引号紧跟名字
            if post_names and (qe - (qe + post_names[0][0])) <= 1:
                spk = post_names[0][1]
            else:
                # 名字 + 说话动词 + 引号
                cand = [c for p, c in pre_names if re.search(r'(说|问|答|喊|道|开口|回答|念|讲)[^"]{0,12}$', pre[p:])]
                if cand:
                    spk = cand[-1]
                elif pre_names and not re.search(r'[。！？]', pre[pre_names[-1][0] + len(pre_names[-1][1].name):]):
                    spk = pre_names[-1][1]
            if spk:
                speaker_events.append((qe, spk))

        # 生成 事件序列: 名字提及 / 说话人 / 他(目标)
        events = []
        for p, c in names:
            events.append((p, 'name', c))
        for p, c in speaker_events:
            events.append((p, 'speak', c))
        for p in targets:
            events.append((p, 'ta', None))
        events.sort(key=lambda x: x[0])

        # 段落内他位置的上下文
        for (p, kind, c) in events:
            if kind == 'name':
                last_named = c
                if c.gender == 'M':
                    pass
                else:
                    pass
                actor = c
            elif kind == 'speak':
                actor = c
            else:
                # 判断 SUBJECT / OBJECT
                seg_start = 0
                for (ss, se, inq) in para_segments(para):
                    if ss <= p < se:
                        seg_start = ss
                        break
                sent = para[seg_start:p]
                prev_names = [(pp, cc) for pp, cc in names if seg_start <= pp < p]
                prev_ta = [q for q in targets if seg_start <= q < p]
                # 句首（去除引导标点后以他开头）=> 潜在主语
                stripped = re.sub(r'^[""''\[\]【】（）()\s,，、。—\-…]*', '', sent)
                stripped2 = re.sub(r'^(但|而|可|可是|不过|然后|于是|接着|这时|这时侯|现在|后来|忽然|突然|接着|又|再|也|还是|只是|因为|所以|如果|当|在|从|到|用|把|被|让|给|向|朝|对|跟|和|与|为|替|在|随着|就在|已经|依旧|始终|一直|依然|忽然|就|才|更|最|都|还|只是|像|仿佛|好像|似乎)*', '', stripped)
                is_subject = stripped2.startswith('他') and not prev_names and not prev_ta
                if not is_subject and not prev_names and not prev_ta:
                    is_subject = True   # 句首主语
                # 判定
                do_change = False
                reason = ''
                if is_subject:
                    if actor is not None and is_luqi(actor.name) and actor.gender == 'F':
                        # 段落内不能出现其它男性角色名在「他」之后（避免误判）
                        after = para[p:]
                        after_male = [n for n in MALE if n in after]
                        # 紧跟引号标签的「他说」不算
                        if not after_male:
                            do_change = True
                            reason = 'SUBJECT-actor=陆栖'
                    else:
                        reason = 'SUBJECT-actor=%s' % (actor,)
                else:
                    subj = prev_names[-1][1] if prev_names else None
                    if subj is not None and is_luqi(subj.name):
                        reason = 'OBJECT-subj=陆栖(不改)'
                    elif subj is not None and subj.gender == 'M':
                        if para_has_luqi and not other_females:
                            do_change = True
                            reason = 'OBJECT-subj=男性->对象应为陆栖'
                        else:
                            reason = 'OBJECT-subj=%s 场景含其它角色' % subj.name
                    else:
                        reason = 'OBJECT-无明确主语'
                if do_change:
                    changes.append({'para': pi, 'pos': p, 'reason': reason,
                                    'ctx': para[max(0, p - 45):p + 25]})
                    if apply:
                        actor = Char('陆栖', 'F')
                else:
                    skipped.append({'para': pi, 'pos': p, 'reason': reason,
                                    'ctx': para[max(0, p - 45):p + 25]})
    return src, changes, skipped, paras


def main():
    apply = '--apply' in sys.argv
    total_files = 0
    total_changes = 0
    all_report = []
    for path in sorted(glob.glob(os.path.join(DIR, '*.md'))):
        src, changes, skipped, paras = process(path, apply=apply)
        if changes:
            total_files += 1
            total_changes += len(changes)
            all_report.append((os.path.basename(path), changes, skipped))
        if apply and changes:
            # 重新生成
            new = src
            for ch in sorted(changes, key=lambda x: -x['pos']):
                pi = ch['para']
                pass
            # 逐段重跑
            paras = src.split('\n')
            newparas = list(paras)
            bypara = {}
            for ch in changes:
                bypara.setdefault(ch['para'], []).append(ch)
            for pi, lst in bypara.items():
                line = newparas[pi]
                for ch in sorted(lst, key=lambda x: -x['pos']):
                    line = line[:ch['pos']] + '她' + line[ch['pos'] + 1:]
                newparas[pi] = line
            open(path, 'w', encoding='utf-8').write('\n'.join(newparas))
    print('FILES_CHANGED', total_files)
    print('CHANGES', total_changes)
    with open('/tmp/opencode/report.json', 'w', encoding='utf-8') as f:
        json.dump([{'file': a, 'changes': b, 'skipped': c} for a, b, c in all_report],
                  f, ensure_ascii=False, indent=1)


main()
