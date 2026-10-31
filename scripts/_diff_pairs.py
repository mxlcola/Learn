# -*- coding: utf-8 -*-
"""对比 -冲突- 副本与主文件，确认副本没有独有内容。"""
import os, re, difflib

D = 'tiddlers'
pairs = []
for fn in os.listdir(D):
    if '冲突' in fn and fn.endswith('.tid') and not fn.startswith('$'):
        main = fn.replace('-冲突-老乐_Win11', '').replace('-冲突-老乐_Win10', '')
        if os.path.exists(os.path.join(D, main)):
            pairs.append((fn, main))
        else:
            print('!! 找不到主文件:', fn)


def body(p):
    raw = open(os.path.join(D, p), 'rb').read().decode('utf-8')
    m = re.search(r'\r?\n\r?\n', raw)
    return (raw[m.end():] if m else '').replace('\r\n', '\n').strip()


for dup, main in sorted(pairs):
    a, b = body(main), body(dup)
    same = a.replace(' ', '') == b.replace(' ', '')
    print(f'{"相同" if same else "不同"} | 主{len(a):4d} 副{len(b):4d} | {main}')
    if not same:
        for ln in list(difflib.unified_diff(a.split('\n'), b.split('\n'), lineterm='', n=0))[2:12]:
            print('     ', ln)
print('\n共', len(pairs), '对')
