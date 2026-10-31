# -*- coding: utf-8 -*-
"""找出没打牙齿标签、但正文大量指向牙齿域条目的「漏网卡」。"""
import os
import re
from collections import Counter

D = 'tiddlers'
TOOTH_TAGS = {'牙齿', '龋齿', '种牙', '牙周炎', '牙科', '口腔医学', '中医', '根管', '种植',
              '牙髓炎', '骨粉', '上颌窦提升', '根管治疗'}
LINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')

items = {}
for fn in os.listdir(D):
    if not fn.endswith('.tid') or fn.startswith('$'):
        continue
    raw = open(os.path.join(D, fn), 'rb').read().decode('utf-8')
    m = re.search(r'\r?\n\r?\n', raw)
    head, body = (raw[:m.start()], raw[m.end():]) if m else (raw, '')
    h = head.replace('\r\n', '\n')
    tm = re.search(r'(?m)^title:[ \t]*([^\n]*)$', h)
    gm = re.search(r'(?m)^tags:[^\n]*$', h)
    title = tm.group(1).strip() if tm else fn[:-4]
    items[title] = dict(
        tags=[t for t in (gm.group(0)[5:].split() if gm else []) if t != '?'],
        body=body.replace('\r\n', '\n'),
    )

tooth = {t for t, v in items.items() if set(v['tags']) & TOOTH_TAGS}
rows = []
for t, v in items.items():
    if t in tooth:
        continue
    links = [l for l in LINK_RE.findall(v['body']) if l in tooth]
    if len(links) >= 2:
        rows.append((len(links), t, len(v['body']), links))

rows.sort(reverse=True)
print('未打牙齿标签但强关联牙齿域的条目：', len(rows))
for n, t, L, links in rows:
    print('%-3d %-24s %4d字  %s' % (n, t, L, '、'.join(links[:6])))
