# -*- coding: utf-8 -*-
import sqlite3, re, collections
c = sqlite3.connect('scripts/_anki/col_copy.anki2')
c.create_collation('unicase', lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
rows = c.execute("""select n.flds from notes n join cards cd on cd.nid=n.id
                    where cd.did=? and n.mid=? group by n.id""",
                 (1791983639885, 1763990896799)).fetchall()
def s(x):
    x = re.sub(r'<br\s*/?>', ' ', x); x = re.sub(r'<[^>]+>', '', x)
    return x.replace('&nbsp;', ' ').strip()
empty = 0; lens = []; samples = []
for (f,) in rows:
    p = f.split('\x1f')
    cite = s(p[2]) if len(p) > 2 else ''
    if not cite: empty += 1
    else:
        lens.append(len(cite))
        if len(samples) < 8: samples.append(cite)
print('问答卡 %d，引用字段为空 %d' % (len(rows), empty))
if lens:
    import statistics as st
    print('引用长度 中位 %d 均值 %.1f' % (st.median(lens), sum(lens)/len(lens)))
    print('样例:')
    for x in samples: print('   ', x[:90])
