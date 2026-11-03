# -*- coding: utf-8 -*-
"""把 Anki「读书笔记::减肥」的问答卡与 TiddlyWiki 减肥卡做交叉比对。

输出三类：
  A. 已有覆盖 —— Anki 问题在 Wiki 里能找到对应卡（相似度 ≥ COVER）
  B. 疑似相关 —— 有点关系但不确定，需要人工看
  C. Wiki 缺口 —— Wiki 里没有对应卡，是应该补的知识点
"""
import os
import re
import sqlite3
import unicodedata

ANKI = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_anki', 'col_copy.anki2')
TID = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tiddlers')
DID_WEIGHT = 1791983639885
MID_QA = 1763990896799

KW = {'减肥', '减脂', '饮食', '热量', '运动', '正念饮食', '乐天瘦身法', '科学减肥', '冯雪科学减肥法',
      '中国肥胖指南', '饥饿', '饱腹', '身体', '行为干预', '睡眠', '心理', '体重', '持久战', '反弹',
      '超慢跑', '三体目标', '体重观', '能量缺口', '肥胖', '瘦身'}

# 疑问句式，比较时去掉
QNOISE = re.compile(r'(是什么|为什么|怎么做|怎么|如何|哪些|有什么|多少|是否|吗|呢|？|\?)')
PUNCT = re.compile(r'[\s，,。.、；;：:！!？?“”"\'（）()《》【】\[\]—\-_~～…]')


def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = QNOISE.sub('', s)
    return PUNCT.sub('', s)


def bigrams(s):
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}


def sim(a, b):
    A, B = bigrams(norm(a)), bigrams(norm(b))
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def load_wiki():
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
            out.append(t)
    return out


def load_anki():
    c = sqlite3.connect(ANKI)
    c.create_collation('unicase', lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
    rows = c.execute("""select n.tags, n.flds from notes n join cards cd on cd.nid = n.id
                        where cd.did = ? and n.mid = ? group by n.id""",
                     (DID_WEIGHT, MID_QA)).fetchall()
    out = []
    for tags, flds in rows:
        p = flds.split('\x1f')
        q = re.sub(r'<[^>]+>', '', p[0]).strip()
        a = re.sub(r'<[^>]+>', '', p[1]).strip() if len(p) > 1 else ''
        s = re.sub(r'<[^>]+>', '', p[2]).strip() if len(p) > 2 else ''
        out.append(dict(q=q, a=a, s=s, tags=[t for t in tags.split() if t and t != '?']))
    return out


def main():
    wiki = load_wiki()
    anki = load_anki()
    RELATED = 0.28

    # Wiki 标题普遍很短（「进食速度」「七分饱」），直接看它是否出现在 Anki 正文里，
    # 比整句相似度可靠得多。过泛的词不作为命中依据。
    GENERIC = {'减肥', '减脂', '运动', '饮食', '体重', '身体', '心理', '热量', '肥胖',
               '瘦身', '饥饿', '饱腹', '睡眠', '反弹', '持久战'}
    cand = [w for w in wiki if 3 <= len(w) <= 10 and w not in GENERIC]

    covered, related, gaps = [], [], []
    for it in anki:
        text = it['q'] + '\n' + it['a'] + '\n' + it['s']
        hits = [w for w in cand if w in text]
        # 命中多个时取最长的那个，它最具体
        hit = max(hits, key=len) if hits else ''
        scored = sorted(((sim(it['q'], w), w) for w in wiki), reverse=True)
        best, btitle = scored[0] if scored else (0.0, '')
        if hit:
            covered.append((round(best, 2), hit, it))
        elif best >= RELATED:
            related.append((round(best, 2), btitle, it))
        else:
            gaps.append((round(best, 2), btitle, it))

    print('Anki 问答卡 %d 张 | Wiki 减肥卡 %d 张' % (len(anki), len(wiki)))
    print('已覆盖 %d | 疑似相关 %d | Wiki 缺口 %d' %
          (len(covered), len(related), len(gaps)))

    with open(os.path.join(os.path.dirname(ANKI), 'match_result.txt'), 'w', encoding='utf-8') as f:
        for name, items in (('C. Wiki 缺口（建议补卡）', gaps),
                            ('B. 疑似相关（需人工确认）', related)):
            f.write('\n\n================ %s : %d 条 ================\n' % (name, len(items)))
            for score, title, it in sorted(items, key=lambda x: -x[0]):
                f.write('\n--- sim=%.2f  最接近: %s\n' % (score, title or '(无)'))
                f.write('Q: %s\n' % it['q'])
                f.write('A: %s\n' % it['a'][:180])
                f.write('一句话: %s\n' % it['s'][:90])
                f.write('tags: %s\n' % ' '.join(it['tags']))
        f.write('\n\n================ A. 已覆盖 : %d 条 ================\n' % len(covered))
        for score, title, it in sorted(covered, key=lambda x: -x[0]):
            f.write('%.2f  [%s]  <-  %s\n' % (score, it['q'][:46], title))
    print('明细已写 scripts/_anki/match_result.txt')


if __name__ == '__main__':
    main()
