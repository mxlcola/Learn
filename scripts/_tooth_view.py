# -*- coding: utf-8 -*-
import os, re

D = 'tiddlers'
KW = ['牙齿', '龋齿', '种牙', '牙周炎', '牙科', '口腔医学', '中医', '补牙', '根管', '种植']
rows = []
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
        rows.append((h.get('title', ''), tags, body.strip()))

rows.sort(key=lambda x: x[0])
lines = []
for t, tags, b in rows:
    # 去掉 关联 段与图片，只留正文信息
    core = re.split(r'(?m)^关联[：:]', b)[0]
    core = re.sub(r'\[img\[[^\]]*\]\]', '', core)
    core = re.sub(r'\s+', ' ', core).strip()
    links = re.findall(r'\[\[([^\]|]+)', b)
    lines.append('%s | %s | %d字 | %d链\n  %s' % (t, ' '.join(tags), len(b), len(links), core[:220]))

with open('scripts/_tooth_view.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('写出', len(lines), '条')
