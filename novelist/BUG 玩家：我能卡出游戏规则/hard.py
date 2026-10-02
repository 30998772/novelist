#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""20 项硬规则。每项都有可复现的数值阈值。全部通过才算合规 100。"""
def hard(r):
    c = r['chars']
    H = [
      ('字数',      3400 <= c <= 3800),
      ('禁用词',    not r['ban7'] and not r['ban_guide'] and not r['forbid']),
      ('加粗',      r['bold'] == 0),
      ('半角逗号',  r['halfcomma'] == 0),
      ('标题同步',  r['title_sync']),
      ('修改残留',  r['edit_residue'] == 0),
      ('唯一句≥.80', r['uniq'] >= 0.80),
      ('叙述段均60-180', 60 <= r['pavg_narr_c'] <= 180),
      ('段长≤200',  r['para_max'] <= 200),
      ('引语≥40',   r['dlg_count'] >= 40),
      ('对白比.25-.45', 0.25 <= r['dlg_line_ratio'] <= 0.45),
      ('长句2-4',   2 <= r['long45'] <= 4),
      ('长句≤80字', r['long80'] == 0),
      ('破折≤2',    r['dash'] <= 2),
      ('无焊接',    not r['weld']),
      ('无疤痕',    not r['scar']),
      ('陆寻不蹲',  not r['dun_ctx']),
      ('明喻≤6', r['simile'] <= 6),
      ('无解释型比喻', r['simile_explain'] == 0),
      ('无解释型排比', r['tri_list'] == 0),
    ]
    return H

def report(rs, lo=1, hi=12):
    for r in rs[lo-1:hi]:
        H = hard(r)
        bad = [n for n, ok in H if not ok]
        pct = round(sum(1 for _, ok in H if ok) / len(H) * 100)
        print(f"{r['file'][-22:]}  {r['chars']:5}  {pct:3}  {'OK' if not bad else 'NG: '+', '.join(bad)}")
