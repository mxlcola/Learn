# -*- coding: utf-8 -*-
"""第一阶段：减肥卡片规则化清理。

只做可判定的机械改动，不重写语义：
  R1 补全空的 type 字段
  R2 标签归并（复用 simplify_cards.TAG_MAP）
  R3 关联段统一为单行「关联：[[A]]、[[B]]」
  R4 删除与「核心知识」重复的「简明解释」节
  R5 摘掉「可进一步参考/参见…」尾巴句，链接并入关联段

用法：
  python scripts/normalize_cards.py --dry-run   预览
  python scripts/normalize_cards.py             写入
"""
import os
import re
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
TIDDLER_DIR = os.path.join(os.path.dirname(HERE), 'tiddlers')

spec = importlib.util.spec_from_file_location('sc', os.path.join(HERE, 'simplify_cards.py'))
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

TAG_MAP = sc.TAG_MAP
DROP_TAGS = sc.DROP_TAGS

ALREADY_DONE = set(sc.CARDS) | {'减肥也要多吃肉', '减肥中的自我商量', '减肥中的正向激励'}

KEYWORDS = ['减肥', '瘦身', '减脂', '体重', '热量', '基础代谢', '肥胖',
            '正念饮食', '断食', '卡路里', '节食', '运动', '饮食结构', '暴食', '胰岛素']
SKIP_NAME = ['牙', '口腔', '龋', '骨粉', '种牙', '穿搭', '男装', '尺码', '身材参考', '股票']

LINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')
# 句末的“可进一步参考…”尾巴：贪婪吃到句号，强制整句匹配
TAIL_PAT = r'(?:可进一步参考|可参见|详见|参见|可结合|也可参考|可参考)[^。\n]*。'
TAIL_RE = re.compile(r'(?:([。，；])\s*)?' + TAIL_PAT)
TAIL_END_RE = re.compile(r'(?:([。，；])\s*)?' + r'(?:可进一步参考|可参见|详见|参见|可结合|也可参考|可参考)[^。\n]*$')
# 关联小节标题
REL_HEAD_RE = re.compile(r'^!!+\s*(关联|相关|相关条目|参见)\s*$')
REL_LINE_RE = re.compile(r'^(关联|相关|相关条目)\s*[:：]\s*(.*)$')
BARE_LINK_RE = re.compile(r'^\[\[[^\]]+\]\](、\[\[[^\]]+\]\])*[。.]?$')
# 简明解释里的操作性表述
OPS_RE = re.compile(r'例如|比如|可以先|建议|入门|若|避免|注意|做法|步骤|先从|再用|每次')


def parse(raw):
    nl = '\r\n' if '\r\n' in raw else '\n'
    m = re.search(r'\r?\n\r?\n', raw)
    if not m:
        return nl, raw, ''
    return nl, raw[:m.start()], raw[m.end():]


def han(s):
    return re.sub(r'[^\u4e00-\u9fa5]', '', s)


def similarity(a, b):
    A, B = set(han(a)), set(han(b))
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def normalize_tags(head, nl):
    lines = head.splitlines()
    out = []
    for ln in lines:
        if ln.startswith('tags:'):
            tokens = ln[5:].strip().split()
            prefix = [t for t in tokens if t == '?']
            rest = []
            for t in tokens:
                if t == '?':
                    continue
                if t in DROP_TAGS:
                    continue
                t2 = TAG_MAP.get(t, t)
                if t2 not in rest:
                    rest.append(t2)
            ln = 'tags: ' + ' '.join(prefix + rest)
        elif ln.startswith('type:') and not ln[5:].strip():
            ln = 'type: text/vnd.tiddlywiki'
        out.append(ln)
    return nl.join(out)


def split_sections(body, nl):
    """切成 [(heading, text)]，heading 为空表示开头无标题部分。"""
    parts = re.split(r'\r?\n(?=!!+ )', body)
    secs = []
    for p in parts:
        m = re.match(r'^(!!+ )(.+?)\r?\n', p)
        if m:
            secs.append((m.group(2).strip(), p[m.end():]))
        else:
            secs.append(('', p))
    return secs


def drop_redundant_explain(secs, notes):
    """R4: 「简明解释」只有在既无独有链接、又无操作性表述、且高度重复时才删。"""
    core = next((t for h, t in secs if h in ('核心知识', '要点')), None)
    out = []
    for h, t in secs:
        if h != '简明解释' or not core:
            out.append((h, t))
            continue
        sim = similarity(core, t)
        new_links = set(LINK_RE.findall(t)) - set(LINK_RE.findall(core))
        has_ops = bool(OPS_RE.search(t))
        if new_links or has_ops:
            notes.append(f'简明解释→怎么做(重合{sim:.2f})')
            out.append(('怎么做', t))
            continue
        if sim > 0.45:
            notes.append(f'删除简明解释(重合{sim:.2f})')
            continue
        notes.append(f'保留简明解释(重合{sim:.2f})')
        out.append((h, t))
    return out


def strip_tail_sentences(text, sink, notes):
    """R5: 摘掉「可进一步参考…」整句，链接收集到 sink，保留句末句号。"""
    def repl(m):
        seg = m.group(0)
        links = LINK_RE.findall(seg)
        if not links:
            return seg
        sink.extend(links)
        notes.append('摘除参考尾巴')
        lead = m.group(1)
        return '。' if lead == '。' else ''
    text = TAIL_RE.sub(repl, text)
    text = TAIL_END_RE.sub(repl, text)
    return text


def normalize_relation(body, extra_links, nl, notes):
    """R3: 关联段合并为单行。"""
    lines = body.rstrip().splitlines()
    tail_links = []

    # 情况 C：末尾是 !! 关联 小节
    idx = None
    for i in range(len(lines) - 1, -1, -1):
        if REL_HEAD_RE.match(lines[i].strip()):
            if all(not l.strip().startswith('!!') for l in lines[i + 1:]):
                idx = i
            break
    if idx is not None:
        tail_links = LINK_RE.findall('\n'.join(lines[idx + 1:]))
        lines = lines[:idx]
    else:
        # 情况 A/B：末尾若干行是「关联：…」或裸链接
        block = []
        while lines:
            s = lines[-1].strip()
            if not s:
                lines.pop()
                continue
            if REL_LINE_RE.match(s) or BARE_LINK_RE.match(s):
                block.insert(0, lines.pop())
            else:
                break
        if block:
            tail_links = LINK_RE.findall('\n'.join(block))
            notes.append('合并关联段')
    body = nl.join(lines).rstrip()

    all_links = []
    for L in tail_links + extra_links:
        if L not in all_links:
            all_links.append(L)
    if not all_links:
        return body
    rel = '关联：' + '、'.join(f'[[{L}]]' for L in all_links)
    return body + nl + nl + rel


def rebuild(secs, nl):
    chunks = []
    for h, t in secs:
        t = t.strip('\r\n')
        if not t:
            continue
        chunks.append((f'!! {h}' + nl + t) if h else t)
    return (nl + nl).join(chunks)


def process(title, meta, body, nl, dry):
    notes = []
    secs = split_sections(body, nl)
    secs = drop_redundant_explain(secs, notes)
    extra = []
    new_secs = []
    for h, t in secs:
        t2 = strip_tail_sentences(t, extra, notes)
        new_secs.append((h, t2))
    body_out = rebuild(new_secs, nl)
    body_out = normalize_relation(body_out, extra, nl, notes)
    return body_out, notes


def main(dry):
    rows = []
    for fn in sorted(os.listdir(TIDDLER_DIR)):
        if not fn.endswith('.tid'):
            continue
        title = fn[:-4]
        if title in ALREADY_DONE or any(s in fn for s in SKIP_NAME):
            continue
        path = os.path.join(TIDDLER_DIR, fn)
        raw = open(path, 'rb').read().decode('utf-8')
        nl, head, body = parse(raw)
        meta = {}
        for l in head.splitlines():
            if ':' in l:
                k, v = l.split(':', 1)
                meta[k.strip()] = v.strip()
        if not any(k in (meta.get('tags', '') + title + body) for k in KEYWORDS):
            continue

        new_head = normalize_tags(head, nl)
        new_body, notes = process(title, meta, body, nl, dry)
        out = new_head + nl + nl + new_body.rstrip() + nl
        if out != raw:
            rows.append((title, len(body), len(new_body), notes, out, path))

    print(f'{"[预演] " if dry else ""}待写入 {len(rows)} 张')
    b = sum(r[1] for r in rows)
    a = sum(r[2] for r in rows)
    if b:
        print(f'正文合计 {b} -> {a} 字，压缩 {100 * (1 - a / b):.0f}%')
    import collections
    c = collections.Counter()
    for r in rows:
        for n in r[3]:
            c[re.sub(r'\(.*\)', '', n)] += 1
    print('改动类型:', dict(c))

    if dry:
        for r in rows[:3]:
            print('\n' + '=' * 30, r[0], r[3])
            print(r[4])
        return
    for r in rows:
        open(r[5], 'wb').write(r[4].encode('utf-8'))


if __name__ == '__main__':
    main('--dry-run' in sys.argv)
