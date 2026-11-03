# -*- coding: utf-8 -*-
"""用 Wiki 卡片全文与 Anki 问答卡做匹配，判断知识点是否已被覆盖。

标题匹配会漏掉「同义不同名」的情况（如 Anki 问「饱腹度为什么是相对概念」，
Wiki 卡叫《饱腹度记录》）。这里改用正文全文比对，召回更高。
"""
import os
import re
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
ANKI = os.path.join(HERE, '_anki', 'col_copy.anki2')
TID = os.path.join(HERE, '..', 'tiddlers')
OUT = os.path.join(HERE, '_anki', 'full_match.txt')

KW = {'减肥', '减脂', '饮食', '热量', '运动', '正念饮食', '乐天瘦身法', '科学减肥', '冯雪科学减肥法',
      '中国肥胖指南', '饥饿', '饱腹', '身体', '行为干预', '睡眠', '心理', '体重', '持久战', '反弹',
      '超慢跑', '三体目标', '体重观', '能量缺口', '肥胖', '瘦身'}
PUNCT = re.compile(r'[\s，,。.、；;：:！!？?“”"\'（）()《》【】\[\]—\-_~～…|]')


def norm(s):
    return PUNCT.sub('', s)


def bigrams(s):
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}


def load_wiki():
    out = []
    for fn in os.listdir(TID):
        if not fn.endswith('.tid') or fn.startswith('$'):
            continue
        raw = open(os.path.join(TID, fn), 'rb').read().decode('utf-8')
        m = re.match(r'(.*?)\r?\n\r?\n', raw, re.S)
        head = m.group(1) if m else raw
        body = raw[m.end():] if m else ''
        h = head.replace('\r\n', '\n')
        tm = re.search(r'(?m)^title:[ \t]*([^\n]*)$', h)
        t = tm.group(1).strip() if tm else fn[:-4]
        gm = re.search(r'(?m)^tags:[^\n]*$', h)
        tags = [x for x in gm.group(0)[5:].split() if x != '?'] if gm else []
        if not (set(tags) & KW):
            continue
        # 去掉关联行，只比正文
        b = re.sub(r'(?m)^关联[：:].*$', '', body)
        out.append((t, bigrams(norm(b)), len(body)))
    return out


def main():
    c = sqlite3.connect(ANKI)
    c.create_collation('unicase', lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
    rows = c.execute("""select n.tags, n.flds from notes n join cards cd on cd.nid = n.id
                        where cd.did = ? and n.mid = ? group by n.id""",
                     (1791983639885, 1763990896799)).fetchall()
    wiki = load_wiki()

    res = []
    for tags, flds in rows:
        p = flds.split('\x1f')
        q = re.sub(r'<[^>]+>', '', p[0]).strip()
        a = re.sub(r'<[^>]+>', '', p[1]).strip() if len(p) > 1 else ''
        s = re.sub(r'<[^>]+>', '', p[2]).strip() if len(p) > 2 else ''
        A = bigrams(norm(q + a))
        best, btitle = 0.0, ''
        for t, W, _ in wiki:
            if not A or not W:
                continue
            j = len(A & W) / len(A)
            if j > best:
                best, btitle = j, t
        ts = [x for x in tags.split() if x and x != '?']
        res.append((best, btitle, q, a, s, ts))

    res.sort()
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('Anki 问答卡 %d 张 vs Wiki %d 张\n' % (len(res), len(wiki)))
        low = [r for r in res if r[0] < 0.45]
        f.write('覆盖率(Anki 答案二元组被某张 Wiki 卡正文包含的比例) < 0.45 的有 %d 张\n\n' % len(low))
        for best, btitle, q, a, s, ts in res:
            f.write('\n--- %.2f  %s\n' % (best, btitle))
            f.write('Q: %s\n' % q)
            f.write('A: %s\n' % a[:200])
            f.write('tags: %s\n' % ' '.join(ts))
    print('已写', OUT)
    print('覆盖率分布:')
    for lo, hi in ((0, .3), (.3, .45), (.45, .6), (.6, .8), (.8, 1.01)):
        print('  %.2f-%.2f : %d' % (lo, hi, sum(1 for r in res if lo <= r[0] < hi)))


if __name__ == '__main__':
    main()
