# -*- coding: utf-8 -*-
"""检查一组候选知识点在 Wiki 全文中是否已有覆盖。"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TID = os.path.join(HERE, '..', 'tiddlers')

CANDIDATES = [
    '八分饱', '8分饱', '纸笔记录', '指压板', '腰臀比', '腰围',
    '热量密度', '拳头法', 'FatMax', '二区', 'Zone 2',
    '体脂秤', '静息心率', '番茄钟', '味觉满足', '咀嚼',
    '剩余一口', '每天剩一口', '最好吃的份量', '十五天', '15天',
    '种花', '搬砖', '多小测', '少考试', '长线思维',
    '回笼觉', '午睡', '补觉', '抗抑郁',
    '教条主义', '同一性', '斗争性', '量变质变', '实事求是',
]

docs = []
for fn in os.listdir(TID):
    if not fn.endswith('.tid') or fn.startswith('$'):
        continue
    raw = open(os.path.join(TID, fn), 'rb').read().decode('utf-8')
    m = re.match(r'(.*?)\r?\n\r?\n', raw, re.S)
    head = m.group(1) if m else raw
    body = raw[m.end():] if m else ''
    h = head.replace('\r\n', '\n')
    tm = re.search(r'(?m)^title:[ \t]*([^\n]*)$', h)
    t = tm.group(1).strip() if tm else fn[:-4]
    docs.append((t, head + '\n' + body))

print('%-14s %5s  %s' % ('关键词', '命中', '出现的卡片（前3）'))
print('-' * 78)
for kw in CANDIDATES:
    hits = [t for t, txt in docs if kw in txt]
    mark = '✓' if hits else '✗ 缺口'
    print('%-14s %5d  %s %s' % (kw, len(hits), mark, '、'.join(hits[:3])))
