# -*- coding: utf-8 -*-
"""牙齿域规范化结果复核。"""
import os
import re

D = 'tiddlers'
TOOTH_TAGS = {'牙齿', '龋齿', '种牙', '牙周炎', '牙科', '口腔医学', '中医', '根管',
              '牙髓炎', '骨粉', '上颌窦提升', '根管治疗'}
LINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')

total = ok_sum = ok_rel = 0
no_sum, rel_dist = [], {}
for fn in os.listdir(D):
    if not fn.endswith('.tid') or fn.startswith('$'):
        continue
    raw = open(os.path.join(D, fn), 'rb').read().decode('utf-8')
    m = re.search(r'\r?\n\r?\n', raw)
    head, body = (raw[:m.start()], raw[m.end():]) if m else (raw, '')
    h = head.replace('\r\n', '\n')
    gm = re.search(r'(?m)^tags:[^\n]*$', h)
    tags = [t for t in (gm.group(0)[5:].split() if gm else []) if t != '?']
    if not (set(tags) & TOOTH_TAGS):
        continue
    total += 1
    b = body.replace('\r\n', '\n').strip()
    first = b.split('\n')[0]
    if first.startswith('一句话概括'):
        ok_sum += 1
    else:
        no_sum.append((h.split('title:')[-1].strip()[:20], len(b)))
    rel = re.search(r'(?m)^关联[：:]([^\n]*)$', b)
    n = len(LINK_RE.findall(rel.group(1))) if rel else 0
    rel_dist[n] = rel_dist.get(n, 0) + 1

print('牙齿域条目', total)
print('有概括', ok_sum, '| 无概括', len(no_sum), no_sum[:8])
print('关联条数分布', dict(sorted(rel_dist.items())))
