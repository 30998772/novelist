#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《旧书栖灵》第三部 性别代词修正 —— 严格保守版
主角陆栖为女性，「他」->「她」。宁可漏改，不可错改。

判定（全部限制在同一段落内完成）：
 必要条件 A：段落内出现 陆栖/陆老师/陆馆长，且出现在该「他」之前
 必要条件 B：段内不出现任何男性配角名（顾松年/方知远/周明远/林越/周维德…）
 必要条件 C：段内不出现 精灵/灵/男/姑娘/先生 等他者标志
 必要条件 D：该「他」为无先行词的主语位置（句首/分句首），其前最近的具名角色是陆栖
 加强条件 E：段内含陆栖特征标志，或该「他」与陆栖同句
"""
import glob, os, re, sys, json

DIR = '/mnt/d/devProject/writer/novelist/旧书栖灵/正文/第三部'

LUQI = ['陆栖', '陆老师', '陆馆长']
MALE = ['林越', '周明远', '周先生', '方知远', '方小远', '顾松年', '周维德',
        '林晓颂', '周慎之', '周小明', '周晓', '沈明远', '苏明远', '陈志远',
        '周维徳', '明远']
OTHER_ALERT = ['精灵', '书灵', '纸屑灵', '阿棠', '雪团', '陈守仁', '陈老师',
               '姑娘', '男人', '男生', '先生', '女士', '孩子', '男孩', '女孩',
               '别人', '大家', '人们', '所有人', '两人', '两人', '两人',
               '路人', '父亲', '妈妈', '外婆', '外公', '奶奶', '爷爷', '儿子',
               '女儿', '爸爸', '老伴', '大夫', '护士', '姑娘']
MARKERS = ['文献馆', '守馆', '守夜', '值班手记', '巡馆', '锁大门', '锁馆门',
           '晒书台', '木楼梯', '老槐树', '天井', '二楼', '纸角信物', '工牌',
           '补书', '修书', '穿针', '编目', '登记簿', '泡茶', '换灯', '点灯',
           '巡楼', '闭馆', '守这栋楼', '留灯', '守馆人', '馆长', '南枝',
           '登记本', '阅览室', '书架', '旧书', '书脊', '古籍', '书页']

TA_SKIP_NEXT = set('们人家用者所')

# 主语位置的引导词
LEAD = re.compile(
    r'^[""''\[\]【】（）()\s,，、。—\-…]*'
    r'(但|而|可是|不过|然后|于是|接着|这时|这时候|现在|后来|忽然|突然|又|再|也|'
    r'还是|只是|因为|所以|如果|当|在|从|到|用|把|被|让|给|向|朝|对|跟|和|与|'
    r'为|替|随着|已经|依旧|始终|一直|依然|就|才|更|最|都|还|像|仿佛|好像|'
    r'似乎|其实|当然|果然|于是|最后|最初|第二天|那天|这年|那年|如今|如今)*')


def find_spans(text, words):
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


def is_luqi(w):
    return w in LUQI


def scan_file(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    props = []
    reasons = []
    for li, para in enumerate(lines):
        if not para.strip() or para.lstrip().startswith('#'):
            continue
        luqi = find_spans(para, LUQI)
        males = find_spans(para, MALE)
        alerts = find_spans(para, OTHER_ALERT)
        if not luqi:
            continue
        # 所有非引号内的「他」
        spans = find_spans(para, ['他'])
        for (s, e, w) in spans:
            if e < len(para) and para[e] in TA_SKIP_NEXT:
                reasons.append((li, s, '复数/他用(他们等)'))
                continue
            # 是否在引号内
            before = para[:s].count('"')
            if before % 2 == 1:
                reasons.append((li, s, '引号内(人物台词内容)'))
                continue
            # 条件 B/C
            if males:
                reasons.append((li, s, '段内有男性配角名 %s' % males[0][2]))
                continue
            if alerts:
                reasons.append((li, s, '段内有他者标志 %s' % alerts[0][2]))
                continue
            # 条件 A：陆栖须在该「他」之前
            luqi_before = [x for x in luqi if x[1] <= s]
            if not luqi_before:
                reasons.append((li, s, '陆栖出现在「他」之后'))
                continue
            # 条件 D：无先行词的主语位置
            seg = para.rfind('。', 0, s)
            seg = max(seg, para.rfind('！', 0, s), para.rfind('？', 0, s),
                      para.rfind('"', 0, s))
            sent = para[seg + 1:s]
            # 同句内「他」之前是否有其它角色/代词先行
            anchor = [x for x in luqi + find_spans(para[seg + 1:s], ['他', '她', '他们'])
                      if True]
            if re.search(r'[他她]', sent):
                reasons.append((li, s, '同句前文已有代词先行'))
                continue
            st = LEAD.sub('', sent)
            if not st.startswith('他'):
                reasons.append((li, s, '非主语位置(前有动词/名词)'))
                continue
            # 条件 E：同句 或 特征标志
            same_sentence = bool(re.search(r'陆栖|陆老师|陆馆长', sent))
            has_marker = any(m in para for m in MARKERS)
            if not (same_sentence or has_marker):
                reasons.append((li, s, '无特征标志且非同句'))
                continue
            props.append({'line': li, 'pos': s,
                          'ctx': para[max(0, s - 50):s + 30],
                          'para': para})
    return lines, props, reasons


def main():
    dry = '--dry' in sys.argv
    allprops = []
    nfiles = 0
    for path in sorted(glob.glob(os.path.join(DIR, '*.md'))):
        lines, props, reasons = scan_file(path)
        if props:
            nfiles += 1
            allprops.append((os.path.basename(path), props))
    print('候选文件数:', nfiles, ' 候选替换处:', sum(len(p) for _, p in allprops))
    json.dump([{'file': f, 'props': [{'line': x['line'], 'pos': x['pos'],
                                      'ctx': x['ctx'], 'para': x['para']}
                                     for x in ps]}
               for f, ps in allprops],
              open('/tmp/opencode/strict.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


main()
