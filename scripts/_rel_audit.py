# -*- coding: utf-8 -*-
import os, re

D = 'tiddlers'
LINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')
rows = []
for fn in os.listdir(D):
    if not fn.endswith('.tid') or fn.startswith('$'):
        continue
    raw = open(os.path.join(D, fn), 'rb').read().decode('utf-8')
    m = re.search(r'\r?\n\r?\n', raw)
    head, body = (raw[:m.start()], raw[m.end():]) if m else (raw, '')
    tm = re.search(r'(?m)^title:[ \t]*([^\n]*)$', head.replace('\r\n', '\n'))
    title = tm.group(1).strip() if tm else fn[:-4]
    rel = re.search(r'(?m)^关联[：:]([^\n]*)$', body.replace('\r\n', '\n'))
    if not rel:
        rows.append((0, title, ''))
        continue
    links = LINK_RE.findall(rel.group(1))
    rows.append((len(links), title, '、'.join(links)))

rows.sort(reverse=True)
many = [r for r in rows if r[0] >= 5]
print('有 关联 行的条目：', sum(1 for r in rows if r[0] > 0))
print('无 关联 行：', sum(1 for r in rows if r[0] == 0))
print('关联 >=5 的：', len(many))
print()
for n, t, l in many:
    print('%d | %s | %s' % (n, t, l[:90]))
