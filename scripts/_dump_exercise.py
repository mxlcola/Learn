# -*- coding: utf-8 -*-
"""导出减肥域中与「运动/身体活动」相关的条目，并做结构体检。"""
import os, re, statistics as st

D = 'tiddlers'
# 明确属于运动/身体活动域的关键词（标题或标签命中即纳入）
KW_TITLE = ['运动', '超慢跑', '跑步', '慢跑', '快走', '步数', '走路', '散步', '锻炼', '训练',
            '肌肉', '力量', '有氧', '无氧', '拉伸', '心率', '代谢', '消耗', '活动量',
            'FatMax', '二区', '指压板', '爬楼', '站姿', '久坐', 'NEAT', '体脂', '基础代谢',
            '燃脂', '供能', '强度', '疲劳', '恢复', '热身', '膝盖', '关节', '呼吸', '乳酸']
KW_TAG = {'运动', '超慢跑', '减脂', '减肥', '热量', '身体', '行为干预', '三体目标', '体重',
          '能量缺口', '科学减肥', '冯雪科学减肥法', '乐天瘦身法', '中国肥胖指南', '正念饮食'}

rows = []
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
    hit_title = any(k in t for k in KW_TITLE)
    hit_tag = bool(set(tags) & {'运动', '超慢跑'})
    if not (hit_title or hit_tag):
        continue
    rows.append(dict(fn=fn, t=t, tags=tags, body=body, L=len(body),
                     why=('标题' if hit_title else '') + ('标签' if hit_tag else '')))

rows.sort(key=lambda r: r['t'])
print('运动相关条目 %d' % len(rows))

def defects(r):
    b = r['body']
    d = []
    if r['L'] < 20: d.append('碎片/空')
    if not b.startswith('一句话概括'): d.append('无概括')
    sm = re.search(r'一句话概括[：:]([^\n]+)', b)
    if sm and len(sm.group(1).strip()) > 40: d.append('概括过长')
    n_head = len(re.findall(r'(?m)^!{1,3}\s', b))
    if n_head > 2: d.append('小标题%d' % n_head)
    if r['L'] > 800: d.append('正文超长')
    if not r['tags']: d.append('无标签')
    if re.search(r'(?m)^关联[：:]\s*$', b): d.append('空关联行')
    return d

LINK = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')
titles = set()
for fn in os.listdir(D):
    if fn.endswith('.tid') and not fn.startswith('$'):
        raw = open(os.path.join(D, fn), 'rb').read().decode('utf-8')
        mm = re.match(r'(.*?)\r?\n\r?\n', raw, re.S)
        hh = (mm.group(1) if mm else raw).replace('\r\n', '\n')
        tt = re.search(r'(?m)^title:[ \t]*([^\n]*)$', hh)
        titles.add(tt.group(1).strip() if tt else fn[:-4])

for r in rows:
    d = defects(r)
    br = [l for l in LINK.findall(r['body']) if l not in titles]
    if br: d.append('断链:' + '、'.join(br[:3]))
    r['d'] = d

with open('scripts/_anki/exercise_dump.txt', 'w', encoding='utf-8') as f:
    for r in rows:
        f.write('\n@@@@@ %s | %d字 | tags=%s | 命中=%s | 缺陷=%s\n'
                % (r['t'], r['L'], ' '.join(r['tags']), r['why'], '、'.join(r['d']) or 'OK'))
        f.write(r['body'] + '\n')

print('有缺陷 %d / %d' % (sum(1 for r in rows if r['d']), len(rows)))
import collections
c = collections.Counter(x.split(':')[0] for r in rows for x in r['d'])
print('缺陷分布', dict(c))
print('\n=== 标题清单 ===')
for r in rows:
    flag = '  << ' + '、'.join(r['d']) if r['d'] else ''
    print('  %4d  %-40s %s%s' % (r['L'], r['t'][:40], r['why'], flag))
