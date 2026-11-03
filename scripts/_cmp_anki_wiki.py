# -*- coding: utf-8 -*-
"""对比 Anki 减肥牌组与 Wiki 卡片的结构性指标，用于规范差异分析。"""
import sqlite3, os, re, statistics as st

ANKI = 'scripts/_anki/col_copy.anki2'
D = 'tiddlers'

# ---------- Anki 侧 ----------
c = sqlite3.connect(ANKI)
c.create_collation('unicase', lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
DID = 1791983639885
QA = 1763990896799
rows = c.execute("""select n.mid, n.flds from notes n join cards cd on cd.nid=n.id
                    where cd.did=? group by n.id""", (DID,)).fetchall()
fmap = {}
for mid, name in c.execute("select id,name from notetypes"):
    fmap[mid] = [r[0] for r in c.execute("select name from fields where ntid=? order by ord", (mid,))]

def strip_tags(s):
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    return s.replace('&nbsp;', ' ').strip()

qa = []          # (q, a, one, src)
hl = 0
for mid, flds in rows:
    parts = flds.split('\x1f')
    names = fmap.get(mid, [])
    d = dict(zip(names, parts))
    if mid == QA:
        q = strip_tags(d.get('问题', ''))
        a = strip_tags(d.get('答案', ''))
        one = strip_tags(d.get('一句话', ''))
        src = strip_tags(d.get('来源', ''))
        qa.append((q, a, one, src))
    else:
        hl += 1

print('=' * 60)
print('【Anki 侧】')
print('笔记总数 %d：问答卡 %d，原文划线 %d' % (len(rows), len(qa), hl))
print('字段：%s' % ' / '.join(fmap.get(QA, [])))
ql = [len(q) for q, _, _, _ in qa if q]
al = [len(a) for _, a, _, _ in qa if a]
ol = [len(o) for _, _, o, _ in qa if o]
print('问题字数  中位 %d  均值 %.1f  最长 %d' % (st.median(ql), sum(ql)/len(ql), max(ql)))
print('答案字数  中位 %d  均值 %.1f  最长 %d' % (st.median(al), sum(al)/len(al), max(al)))
if ol:
    print('一句话字数 中位 %d  均值 %.1f  (有该字段 %d/%d)' % (st.median(ol), sum(ol)/len(ol), len(ol), len(qa)))
print('有来源字段 %d/%d' % (sum(1 for _, _, _, s in qa if s), len(qa)))
print('问句以问号结尾 %d/%d' % (sum(1 for q, _, _, _ in qa if q.rstrip().endswith(('？', '?'))), len(qa)))
# 答案里含多要点（分号/序号/多句）
multi = sum(1 for _, a, _, _ in qa if a.count('。') >= 2 or re.search(r'[;；]|[①②③1-9][、.．]', a))
print('答案含 3 句以上或多要点  %d/%d (%.0f%%)' % (multi, len(qa), multi*100.0/len(qa)))

# ---------- Wiki 侧 ----------
KW = {'减肥', '减脂', '饮食', '热量', '运动', '正念饮食', '乐天瘦身法', '科学减肥', '冯雪科学减肥法',
      '中国肥胖指南', '饥饿', '饱腹', '身体', '行为干预', '睡眠', '心理', '体重', '持久战', '反弹',
      '超慢跑', '三体目标', '体重观', '能量缺口', '肥胖', '瘦身'}
wiki = []
for fn in os.listdir(D):
    if not fn.endswith('.tid') or fn.startswith('$'):
        continue
    raw = open(os.path.join(D, fn), 'rb').read().decode('utf-8')
    m = re.match(r'(.*?)\r?\n\r?\n', raw, re.S)
    head = m.group(1) if m else raw
    body = (raw[m.end():] if m else '').strip()
    h = head.replace('\r\n', '\n')
    tm = re.search(r'(?m)^title:[ \t]*([^\n]*)$', h)
    t = tm.group(1).strip() if tm else fn[:-4]
    gm = re.search(r'(?m)^tags:[^\n]*$', h)
    tags = [x for x in gm.group(0)[5:].split() if x != '?'] if gm else []
    if set(tags) & KW:
        wiki.append((t, body))

print()
print('=' * 60)
print('【Wiki 侧】')
print('减肥域卡片 %d' % len(wiki))
bl = [len(b) for _, b in wiki if b]
print('正文字数  中位 %d  均值 %.1f  最长 %d' % (st.median(bl), sum(bl)/len(bl), max(bl)))
n_head = [b.count('\n!') + (1 if b.startswith('!') else 0) for _, b in wiki]
print('小标题数  中位 %d  均值 %.1f  最多 %d' % (st.median(n_head), sum(n_head)/len(n_head), max(n_head)))
sm = [len(re.search(r'一句话概括[：:]([^\n]+)', b).group(1).strip())
      for _, b in wiki if re.search(r'一句话概括[：:]([^\n]+)', b)]
print('概括字数  中位 %d  均值 %.1f  (有概括 %d/%d)' % (st.median(sm), sum(sm)/len(sm), len(sm), len(wiki)))
LINK = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')
lk = [len(LINK.findall(b)) for _, b in wiki]
print('双链数    中位 %d  均值 %.1f  最多 %d' % (st.median(lk), sum(lk)/len(lk), max(lk)))
print('正文含列表 %d/%d' % (sum(1 for _, b in wiki if re.search(r'(?m)^\*|^\d+\.', b)), len(wiki)))

print()
print('=' * 60)
print('【交叉】两者字数对比（Anki 答案 vs Wiki 正文）')
print('Anki 答案中位 %d 字 / Wiki 正文中位 %d 字 → 比值 %.1f 倍'
      % (st.median(al), st.median(bl), st.median(bl)*1.0/st.median(al)))
