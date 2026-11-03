# -*- coding: utf-8 -*-
"""按关键词提取 Anki 卡的完整内容，用于补写 Wiki 卡片。"""
import os
import re
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
ANKI = os.path.join(HERE, '_anki', 'col_copy.anki2')
OUT = os.path.join(HERE, '_anki', 'picked.txt')

KEYS = ['种花', '搬砖', '拳头', '指压板', '八分饱', '纸笔', 'FatMax', '二区',
        '午睡', '抗抑郁', '静息心率', '热量密度', '颜色区', '最好吃', '十五天']

c = sqlite3.connect(ANKI)
c.create_collation('unicase', lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
rows = c.execute("""select n.tags, n.flds from notes n join cards cd on cd.nid = n.id
                    where cd.did = ? group by n.id""", (1791983639885,)).fetchall()

picked = []
for tags, flds in rows:
    p = flds.split('\x1f')
    allf = [re.sub(r'<[^>]+>', ' ', x).strip() for x in p]
    txt = '\n'.join(allf)
    hit = [k for k in KEYS if k in txt]
    if hit:
        picked.append((hit, allf))

with open(OUT, 'w', encoding='utf-8') as f:
    for hit, allf in picked:
        f.write('\n########## 命中: %s\n' % '、'.join(hit))
        for i, x in enumerate(allf):
            if x:
                f.write('  [%d] %s\n' % (i, x))
print('命中 %d 条 -> %s' % (len(picked), OUT))
