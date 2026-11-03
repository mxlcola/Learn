# -*- coding: utf-8 -*-
"""按主题给 Anki 减肥问答卡分组，并检查每组在 Wiki 里的覆盖情况。"""
import os
import re
import sqlite3
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ANKI = os.path.join(HERE, '_anki', 'col_copy.anki2')
TID = os.path.join(HERE, '..', 'tiddlers')

GEN = {'减肥', '运动', '饮食理念', '心态', '实操', '热量', '医学', '饱腹度',
       '记录法', '生活化减脂', '体重观', '三体目标', '科学减肥法'}
KW = {'减肥', '减脂', '饮食', '热量', '运动', '正念饮食', '乐天瘦身法', '科学减肥', '冯雪科学减肥法',
      '中国肥胖指南', '饥饿', '饱腹', '身体', '行为干预', '睡眠', '心理', '体重', '持久战', '反弹',
      '超慢跑', '三体目标', '体重观', '能量缺口', '肥胖', '瘦身'}


def wiki_titles():
    out = []
    for fn in os.listdir(TID):
        if not fn.endswith('.tid') or fn.startswith('$'):
            continue
        raw = open(os.path.join(TID, fn), 'rb').read().decode('utf-8')
        m = re.match(r'(.*?)\r?\n\r?\n', raw, re.S)
        head = m.group(1) if m else raw
        h = head.replace('\r\n', '\n')
        tm = re.search(r'(?m)^title:[ \t]*([^\n]*)$', h)
        t = tm.group(1).strip() if tm else fn[:-4]
        gm = re.search(r'(?m)^tags:[^\n]*$', h)
        tags = [x for x in gm.group(0)[5:].split() if x != '?'] if gm else []
        if set(tags) & KW:
            out.append((t, set(tags)))
    return out


def main():
    c = sqlite3.connect(ANKI)
    c.create_collation('unicase', lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
    rows = c.execute("""select n.tags, n.flds from notes n join cards cd on cd.nid = n.id
                        where cd.did = ? and n.mid = ? group by n.id""",
                     (1791983639885, 1763990896799)).fetchall()

    wt = wiki_titles()
    GENERIC = {'减肥', '减脂', '运动', '饮食', '体重', '身体', '心理', '热量', '肥胖',
               '瘦身', '饥饿', '饱腹', '睡眠', '反弹', '持久战'}
    cand = [w for w, _ in wt if 3 <= len(w) <= 10 and w not in GENERIC]

    groups = collections.defaultdict(list)
    for tags, flds in rows:
        ts = [t for t in tags.split() if t and t != '?']
        p = flds.split('\x1f')
        q = re.sub(r'<[^>]+>', '', p[0]).strip()
        a = re.sub(r'<[^>]+>', '', p[1]).strip() if len(p) > 1 else ''
        s = re.sub(r'<[^>]+>', '', p[2]).strip() if len(p) > 2 else ''
        main = [t for t in ts if t not in GEN and not t.startswith('科学减肥法-')]
        if not main:
            main = [t for t in ts if t.startswith('科学减肥法-')] or ['(未分组)']
        text = q + '\n' + a + '\n' + s
        hits = [w for w in cand if w in text]
        groups[main[0]].append(dict(q=q, a=a, s=s, tags=ts, hit=hits))

    print('Anki 问答卡 %d 张，分成 %d 组\n' % (sum(len(v) for v in groups.values()), len(groups)))
    print('%-40s %4s %6s %6s' % ('主题组', '张数', '有命中', '无命中'))
    print('-' * 62)
    for k, v in sorted(groups.items(), key=lambda x: -len(x[1])):
        h = sum(1 for x in v if x['hit'])
        print('%-40s %4d %6d %6d' % (k[:40], len(v), h, len(v) - h))


if __name__ == '__main__':
    main()
