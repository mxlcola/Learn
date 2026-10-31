# -*- coding: utf-8 -*-
"""把重复的同步冲突副本移出 tiddlers，避免同名条目互相遮盖。

判定规则：文件名形如 `<原名>-冲突-<机器名><扩展名>`，且去掉冲突段后
tiddlers 里存在同名主文件。仅当两者内容完全相同时才归档，内容不同的
副本保留下来交人工确认，避免误删唯一版本。
"""
import os
import re
import shutil

D = 'tiddlers'
OUT = 'archive/conflicts'
os.makedirs(OUT, exist_ok=True)

CONFLICT_RE = re.compile(r'^(?P<base>.+?)-冲突-[^-]+(?P<ext>\.[^.]+)$')

moved, kept = [], []
for fn in os.listdir(D):
    m = CONFLICT_RE.match(fn)
    if not m:
        continue
    base = m.group('base') + m.group('ext')
    src = os.path.join(D, fn)
    dst_main = os.path.join(D, base)
    if not os.path.exists(dst_main):
        kept.append((fn, '无对应主文件'))
        continue
    if open(src, 'rb').read() == open(dst_main, 'rb').read():
        shutil.move(src, os.path.join(OUT, fn))
        moved.append(fn)
    else:
        kept.append((fn, '内容与主文件不同'))

print('已归档副本 %d -> %s' % (len(moved), OUT))
for f in moved:
    print('  -', f)
if kept:
    print('保留待人工确认 %d' % len(kept))
    for f, why in kept:
        print('  *', f, '|', why)
