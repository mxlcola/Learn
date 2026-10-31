# -*- coding: utf-8 -*-
import os, re, sys

D = 'tiddlers'
KW = ['牙齿', '龋齿', '种牙', '牙周炎', '牙科', '口腔医学', '中医', '补牙', '根管', '种植']
out = []
for fn in os.listdir(D):
    if not fn.endswith('.tid') or fn.startswith('$'):
        continue
    raw = open(os.path.join(D, fn), 'rb').read().decode('utf-8')
    m = re.search(r'\r?\n\r?\n', raw)
    head, body = (raw[:m.start()], raw[m.end():]) if m else (raw, '')
    h = {}
    for ln in head.splitlines():
        if ':' in ln:
            k, v = ln.split(':', 1)
            h[k.strip()] = v.strip()
    tags = [t for t in h.get('tags', '').split() if t != '?']
    if any(k in tags for k in KW):
        out.append((h.get('title', ''), tags, body.strip(), len(body.strip())))

out.sort(key=lambda x: x[0])
print('牙齿域条目', len(out))
with open('scripts/_tooth_dump.txt', 'w', encoding='utf-8') as f:
    for t, tags, b, L in out:
        f.write('\n@@@@@ %s ||| tags=%s ||| %d字\n%s\n' % (t, ' '.join(tags), L, b))
print('已写 scripts/_tooth_dump.txt')
