# -*- coding: utf-8 -*-
"""修正牙齿域里指向不存在条目的链接。"""
import os
import re

D = 'tiddlers'

# (文件名, 原文, 替换)
FIXES = [
    ('[[上颌]]', '[[上颌窦]]'),
    ('[[根管后的牙，为什么变_脆_了？]]', '[[根管后的牙，为什么变"脆"了？]]'),
    ('[[牙骨质]]', '[[牙根]]'),
    ('[[牙龈]]', '[[牙龈退缩]]'),
    ('[[牙周膜]]', '牙周膜'),
]

n = 0
for fn in os.listdir(D):
    if not fn.endswith('.tid') or fn.startswith('$'):
        continue
    path = os.path.join(D, fn)
    raw = open(path, 'rb').read().decode('utf-8')
    new = raw
    for a, b in FIXES:
        if a in new:
            new = new.replace(a, b)
    if new != raw:
        open(path, 'wb').write(new.encode('utf-8'))
        print('修正', fn)
        n += 1
print('共修正', n, '个文件')
