# -*- coding: utf-8 -*-
"""输出 Anki 减肥问答卡的精简清单：按来源分组，只留问题 + 一句话结论。"""
import os
import re
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
ANKI = os.path.join(HERE, '_anki', 'col_copy.anki2')
OUT = os.path.join(HERE, '_anki', 'brief.txt')

# 来源归类：按标签优先级判断
SOURCE_RULES = [
    ('冯雪·科学减肥16讲', lambda ts: any(t.startswith('科学减肥法-') or '冯雪' in t for t in ts)),
    ('乐天瘦身法', lambda ts: any(t == '乐天瘦身法' or '记录减肥法' in t for t in ts)),
    ('超慢跑', lambda ts: any(t == '超慢跑' for t in ts)),
    ('生活化减脂（茴春）', lambda ts: any('生活化减脂' in t for t in ts)),
    ('瘦easy·马克思主义', lambda ts: any('瘦easy' in t for t in ts)),
    ('毛选两论', lambda ts: any('毛选' in t or '两论' in t for t in ts)),
]


def main():
    c = sqlite3.connect(ANKI)
    c.create_collation('unicase', lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
    rows = c.execute("""select n.tags, n.flds from notes n join cards cd on cd.nid = n.id
                        where cd.did = ? and n.mid = ? group by n.id""",
                     (1791983639885, 1763990896799)).fetchall()

    groups = {}
    for tags, flds in rows:
        ts = [t for t in tags.split() if t and t != '?']
        p = flds.split('\x1f')
        q = re.sub(r'<[^>]+>', ' ', p[0]).strip()
        a = re.sub(r'<[^>]+>', ' ', p[1]).strip() if len(p) > 1 else ''
        s = re.sub(r'<[^>]+>', ' ', p[2]).strip() if len(p) > 2 else ''
        src = '其他（未标注来源）'
        for name, rule in SOURCE_RULES:
            if rule(ts):
                src = name
                break
        groups.setdefault(src, []).append((q, s or a[:60], a))

    order = [n for n, _ in SOURCE_RULES] + ['其他（未标注来源）']
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('Anki「读书笔记::减肥」问答卡精简清单  共 %d 张\n' % sum(len(v) for v in groups.values()))
        for name in order:
            items = groups.get(name)
            if not items:
                continue
            f.write('\n\n########## %s : %d 张 ##########\n' % (name, len(items)))
            for i, (q, s, a) in enumerate(items, 1):
                f.write('%2d. %s\n     > %s\n' % (i, q, (s or '(无一句话)')[:70]))
    print('已写', OUT)
    for name in order:
        if groups.get(name):
            print('  %-24s %d' % (name, len(groups[name])))


if __name__ == '__main__':
    main()
