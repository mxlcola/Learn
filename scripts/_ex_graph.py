# -*- coding: utf-8 -*-
"""运动域 93 张卡的链接关系：找孤岛、找枢纽候选、找已有索引卡。"""
import os, re, collections
D = 'tiddlers'
KW_TITLE = ['运动', '超慢跑', '跑步', '慢跑', '快走', '步数', '走路', '散步', '锻炼', '训练',
            '肌肉', '力量', '有氧', '无氧', '拉伸', '心率', '代谢', '消耗', '活动量',
            'FatMax', '二区', '指压板', '爬楼', '站姿', '久坐', 'NEAT', '体脂', '基础代谢',
            '燃脂', '供能', '强度', '疲劳', '恢复', '热身', '膝盖', '关节', '呼吸', '乳酸']
cards = {}
for fn in os.listdir(D):
    if not fn.endswith('.tid') or fn.startswith('$'):
        continue
    raw = open(os.path.join(D, fn), 'rb').read().decode('utf-8')
    m = re.match(r'(.*?)\r?\n\r?\n', raw, re.S)
    head = m.group(1) if m else raw
    body = (raw[m.end():] if m else '').strip()
    h = head.replace('\r\n', '\n')
    tm = re.search(r'(?m)^title:[ \t]*([^\n]*)$', h)
    t = tm.group(1).strip() if tm else fn[:-4]
    gm = re.search(r'(?m)^tags:[^\n]*$', h)
    tags = [x for x in gm.group(0)[5:].split() if x != '?'] if gm else []
    cards[t] = dict(fn=fn, body=body, tags=tags)

LINK = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')
scope = [t for t, v in cards.items()
         if any(k in t for k in KW_TITLE) or ('运动' in v['tags'] or '超慢跑' in v['tags'])]
scope = set(scope)

indeg = collections.Counter()
outdeg = collections.Counter()
for t, v in cards.items():
    ls = [l for l in LINK.findall(v['body']) if l in cards]
    outdeg[t] = len(ls)
    for l in ls:
        indeg[l] += 1

print('=== 是否有运动域索引/地图卡 ===')
for t in sorted(cards):
    if re.search(r'(运动|超慢跑).*(地图|索引|总纲|导航|清单|对应表|章节)', t) or \
       re.search(r'(地图|索引|总纲|导航).*(运动|超慢跑)', t):
        print('  ', t)

print('\n=== 孤岛（在运动域内无任何入链，且自身出链 <=2） ===')
isolated = []
for t in sorted(scope):
    if indeg[t] == 0:
        isolated.append((t, outdeg[t], len(cards[t]['body'])))
for t, o, L in isolated:
    print('  %-38s 出链%d  %d字' % (t[:38], o, L))
print('孤岛数', len(isolated), '/', len(scope))

print('\n=== 入链最多（自然枢纽 Top12）===')
for t, n in indeg.most_common(12):
    if t in scope:
        print('  %-38s %d' % (t[:38], n))

print('\n=== 高度疑似重复（标题成对）===')
print('  运动后涨秤 / 运动后涨秤怎么办')
print('  运动30分钟迷思 / 运动黄金时长 / 超慢跑黄金时长 / 慢跑40分钟')
print('  燃脂心率 / 超慢跑燃脂心率 / 谈话测试')
print('  后燃效应 / 运动后过量氧耗')
print('  抗阻训练 / 重训')
