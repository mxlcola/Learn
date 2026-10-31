# -*- coding: utf-8 -*-
"""找出「归一化后标题相同」的重复条目。

只差引号、空格、全半角标点、书名号等的两个标题，在 Wiki 里看起来是两张卡，
实际是同一概念的重复，且会让按标题匹配的处理脚本互相覆盖。
"""
import os
import re
import collections

D = 'tiddlers'


def norm_key(s):
    """忽略引号、空白、常见标点的标题归一。"""
    s = re.sub(r'["“”\'’‘]', '', s)
    s = re.sub(r'[《》〈〉\[\]【】（）()《》]', '', s)
    s = re.sub(r'[，,。.、；;：:！!？?—\-_~～]', '', s)
    return re.sub(r'\s+', '', s)


def body_of(raw):
    m = re.match(r'.*?\r?\n\r?\n', raw, re.S)
    return raw[m.end():].strip() if m else ''


groups = collections.defaultdict(list)
for fn in os.listdir(D):
    if not fn.endswith('.tid') or fn.startswith('$'):
        continue
    raw = open(os.path.join(D, fn), 'rb').read().decode('utf-8')
    m = re.match(r'(.*?)\r?\n\r?\n', raw, re.S)
    head = m.group(1) if m else raw
    h = head.replace('\r\n', '\n')
    tm = re.search(r'(?m)^title:[ \t]*([^\n]*)$', h)
    title = tm.group(1).strip() if tm else fn[:-4]
    groups[norm_key(title)].append((fn, title, len(body_of(raw))))

dups = {k: v for k, v in groups.items() if len(v) > 1}
print('归一化后重复的标题组 %d 个，涉及 %d 个文件' % (len(dups), sum(len(v) for v in dups.values())))
for k, v in sorted(dups.items(), key=lambda x: -len(x[1])):
    v = sorted(v, key=lambda x: -x[2])
    print('\n[%s]' % k)
    for fn, title, L in v:
        flag = '  <- 空' if L == 0 else ''
        print('   %-6d %s%s' % (L, title, flag))
