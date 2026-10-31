# -*- coding: utf-8 -*-
"""知识卡片体检：按《条目编写规范》逐条检查，输出可执行的问题清单。

用法：
    python scripts/lint_cards.py              # 全库体检
    python scripts/lint_cards.py 牙齿 龋齿     # 只看带这些标签的条目
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
TIDDLER_DIR = os.path.join(os.path.dirname(HERE), 'tiddlers')

SUMMARY_MAX = 40      # 一句话概括字数上限
BODY_WARN = 800       # 正文过长，提示拆分
REL_WARN = 5          # 关联条数预警（不是硬限制）
LINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')
REL_RE = re.compile(r'(?m)^关联[：:]([^\n]*)')
HEADING_RE = re.compile(r'(?m)^!![^!]')


def load():
    items = []
    for fn in os.listdir(TIDDLER_DIR):
        if not fn.endswith('.tid') or fn.startswith('$'):
            continue
        path = os.path.join(TIDDLER_DIR, fn)
        raw = open(path, 'rb').read().decode('utf-8')
        m = re.match(r'(.*?)\r?\n\r?\n', raw, re.S)
        head, body = (m.group(1), raw[m.end():]) if m else (raw, '')
        h = head.replace('\r\n', '\n')
        tm = re.search(r'(?m)^title:[ \t]*([^\n]*)$', h)
        gm = re.search(r'(?m)^tags:[^\n]*$', h)
        items.append(dict(
            title=(tm.group(1).strip() if tm else fn[:-4]),
            tags=[t for t in (gm.group(0)[5:].split() if gm else []) if t != '?'],
            body=body.strip().replace('\r\n', '\n'),
            file=fn,
        ))
    return items


def check(items, only=None):
    titles = {it['title'] for it in items}
    dup = {k for k, v in Counter(it['title'] for it in items).items() if v > 1}
    issues = []

    def add(it, kind, detail):
        issues.append((kind, it['title'], detail))

    for it in items:
        if only and not (set(it['tags']) & set(only)):
            continue
        t, b = it['title'], it['body']
        L = len(b)

        if L == 0:
            add(it, '空条目', '正文为空，待补内容或删除')
            continue
        if L < 20:
            add(it, '碎片', '正文仅 %d 字，多半是没写完的一句' % L)
            continue

        first = b.split('\n')[0].strip()
        if not first.startswith('一句话概括'):
            add(it, '缺一句话概括', '首行不是结论句')
        else:
            s = first.split('：', 1)[-1].strip()
            if len(s) > SUMMARY_MAX:
                add(it, '概括过长', '%d 字，超过 %d' % (len(s), SUMMARY_MAX))
            if s and (s == t or s.startswith(t) and len(s) <= len(t) + 8):
                add(it, '概括重复标题', '概括只是把标题改写一遍')

        rels = REL_RE.findall(b)
        for r in rels:
            n = len(LINK_RE.findall(r))
            if n > REL_WARN:
                add(it, '关联偏多', '%d 条，检查是否与正文内联链接重复' % n)
        if len(rels) > 1:
            add(it, '关联重复', '出现 %d 处 关联 段' % len(rels))

        heads = len(HEADING_RE.findall(b))
        if heads > 2:
            add(it, '小标题过多', '%d 个二级标题，考虑拆分' % heads)
        if L > BODY_WARN:
            add(it, '正文过长', '%d 字，考虑拆成多张卡' % L)

        for l in LINK_RE.findall(b):
            if l not in titles:
                add(it, '悬空链接', '指向不存在的条目 [[%s]]' % l)

        if t in dup:
            add(it, '标题重复', '有同名条目，TiddlyWiki 会互相遮盖')

    return issues


def main():
    only = sys.argv[1:] or None
    items = load()
    issues = check(items, only)
    stat = Counter(k for k, _, _ in issues)

    print('条目总数 %d\n' % len(items))
    print('问题分布：')
    for k, v in stat.most_common():
        print('  %-12s %d' % (k, v))

    print('\n明细：')
    for kind in ['标题重复', '空条目', '悬空链接', '关联重复', '概括重复标题',
                 '概括过长', '关联偏多', '小标题过多', '正文过长', '碎片', '缺一句话概括']:
        group = [i for i in issues if i[0] == kind]
        if not group:
            continue
        print('\n[%s] %d 条' % (kind, len(group)))
        for _, title, detail in group[:15]:
            print('  %-30s %s' % (title[:30], detail))
        if len(group) > 15:
            print('  … 其余 %d 条' % (len(group) - 15))


if __name__ == '__main__':
    main()
