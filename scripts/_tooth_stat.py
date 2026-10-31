# -*- coding: utf-8 -*-
import os, re, collections

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
        rows.append(dict(fn=fn, title=h.get('title', ''), tags=tags, body=body.strip()))

print('牙齿域', len(rows))
c = collections.Counter()
for r in rows:
    b = r['body']
    has_sum = b.startswith('一句话概括')
    has_pt = '!! 要点' in b
    mrel = re.search(r'(?m)^关联[：:]\s*$', b)
    rel_oneline = bool(re.search(r'(?m)^关联[：:]\s*\S', b))
    links = re.findall(r'\[\[([^\]|]+)', b)
    c['缺一句话概括'] += 0 if has_sum else 1
    c['缺!! 要点'] += 0 if has_pt else 1
    c['关联独立成行(旧式)'] += 1 if mrel else 0
    c['关联单行'] += 1 if rel_oneline else 0
    c['无关联段'] += 1 if not re.search(r'(?m)^关联[：:]', b) else 0
    c['关联>5'] += 1 if len(links) > 5 else 0
    c['正文<80字'] += 1 if len(b) < 80 else 0
    c['正文>600字'] += 1 if len(b) > 600 else 0
    c['有原文摘录'] += 1 if '! 原文摘录' in b else 0
    c['有表格'] += 1 if re.search(r'(?m)^\|', b) else 0
for k, v in c.items():
    print(f'  {k:16s} {v}')

print('\n标签频次:', collections.Counter(t for r in rows for t in r['tags']).most_common(20))
print('\n=== 缺!! 要点的条目 ===')
for r in rows:
    if '!! 要点' not in r['body']:
        print(f'  [{r["title"]}] {len(r["body"])}字 {r["body"][:60]!r}')
