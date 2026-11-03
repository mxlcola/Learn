# -*- coding: utf-8 -*-
"""把 Wiki 减肥相关卡片合并成一个文本，便于快速检索核对。"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TID = os.path.join(HERE, '..', 'tiddlers')
OUT = os.path.join(HERE, '_anki', 'wiki_weight_all.txt')

KW = {'减肥', '减脂', '饮食', '热量', '运动', '正念饮食', '乐天瘦身法', '科学减肥', '冯雪科学减肥法',
      '中国肥胖指南', '饥饿', '饱腹', '身体', '行为干预', '睡眠', '心理', '体重', '持久战', '反弹',
      '超慢跑', '三体目标', '体重观', '能量缺口', '肥胖', '瘦身'}

n = 0
with open(OUT, 'w', encoding='utf-8') as f:
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
        gm = re.search(r'(?m)^tags:[^\n]*$', h)
        tags = [x for x in gm.group(0)[5:].split() if x != '?'] if gm else []
        if not (set(tags) & KW):
            continue
        n += 1
        f.write('\n===== %s =====\n%s\n' % (t, body.strip()))
print('合并 %d 张 -> %s' % (n, OUT))
