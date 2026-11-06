# -*- coding: utf-8 -*-
"""恢复减肥域旧卡的分点样式，并做温和精简（2026-11-06 第二轮）。

背景：上一轮 refine_evergreen_cards.py 把 365 张卡的「!! 要点 / * 列表 /
!! 怎么做 / # 列表」压成了纯段落式。用户确认「分点描述不能修改样式，可以精简内容」，
故本脚本从改前快照恢复原分点结构，只精简文字，不动任何结构符号。

保留上一轮成果：
  - 28 张改名卡的新标题与 source 字段（取当前文件头部）
  - 6 张卡 8 处「本章/本书/书中/作者」语境词修正
  - 全库反链同步（恢复文本里残留的 2 处旧标题双链再替换一次）
  - 关联行末行纯文本格式（快照里本来就是末行）

用法：
    python scripts/restore_bullet_style.py --dry-run
    python scripts/restore_bullet_style.py --apply
"""
import pathlib, json, re, tempfile, io, sys, ast, collections

P = pathlib.Path(__file__).resolve().parent.parent
ROOT = P / 'tiddlers'
HDR = re.compile(r'(.*?)\r?\n\r?\n', re.S)
ASSOC_LINE = re.compile(r'^关联[：:]')
NAV = re.compile(r'章节地图|索引|拆书|对应表|大纲|参考文献|发刊词|目录|对照|总结|16讲|全套')
SNAPDIR = pathlib.Path(tempfile.gettempdir()) / 'evergreen_refine_20261106'

# 复用上一轮的改名映射
_src = (P / 'scripts' / 'refine_evergreen_cards.py').read_text(encoding='utf-8')
for node in ast.parse(_src).body:
    if isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == 'MAP' for t in node.targets):
        MAP = ast.literal_eval(node.value)

# 标题映射：旧文件名 -> 当前文件名
CUR_NAME = {k + '.tid': v + '.tid' for k, v in MAP.items()}

# —— 语境词修正（上一轮手工改过，恢复快照后需重新应用）——
# (快照文件名, 原文片段, 新文片段)
CONTEXT_FIX = [
    ('《放弃减肥，我瘦了60斤》第2章-开启你的最后一次减肥之旅.tid',
     '本书不承诺腹肌、速成和完美身材', '这套思路不承诺腹肌、速成和完美身材'),
    ('《放弃减肥，我瘦了60斤》第7章-别再跑步减肥了.tid',
     '本章并非否定跑步', '这不是否定跑步'),
    ('《正念饮食》第一章-认识正念饮食.tid',
     '作者用售卖机、甜点和披萨的个人经历说明', '售卖机、甜点和披萨这类日常场景说明'),
    ('《正念饮食》第一章-认识正念饮食.tid',
     '是本章的情绪底色', '是这条路径的情绪底色'),
    ('《正念饮食》第三章-真正的饥饿感.tid',
     '本章不是要消灭渴望', '重点不是消灭渴望'),
    ('《正念饮食》第五章-培养外在智慧.tid',
     '书中更偏向“多吃一点/少吃一点”的可调表达', '更合用的是“多吃一点/少吃一点”这类可调表达'),
    ('《正念饮食》第十章-开心享受但不一定要吃完.tid',
     '练习 18 在本书中更强调察觉持续进食冲动', '练习 18 更强调察觉持续进食冲动'),
    ('《正念饮食》第十章-开心享受但不一定要吃完.tid',
     '本章把“剩下”从浪费和失败', '把“剩下”从浪费和失败'),
]
FIX_BY_FILE = collections.defaultdict(list)
for f, a, b in CONTEXT_FIX:
    FIX_BY_FILE[f].append((a, b))

# —— 温和精简规则：只删虚词/套话/冗长修饰，不碰事实、数据、专名、双链 ——
# 每条 (名称, 正则, 替换)
# 只保留「零语义损失、零可读性损失」的替换。
# 已剔除：非常/极其/十分（实义程度副词，删了弱化表述）、相当（同前）、
#         对多数人来说/而言（删后句法生硬）、插入「其实」（表转折，删了损语气）。
# 库内 [[十分饱心得]] 等双链另有 PROTECT 占位保护，任何规则都不会触及其内部文字。
LEAN_RULES = [
    ('句首套话', r'^'
     r'(?:其实|事实上|实际上|说实话|坦白说|说到底|归根结底|总的来说|总体而言|'
     r'一般来说|一般来讲|在大多数情况下|从某种意义上说|某种意义上|'
     r'严格来说|客观来说|众所周知|毫无疑问|显而易见|需要注意的是|值得注意的是|'
     r'需要指出的是|换言之|换句话说|也就是说|由此可见|不难看出|可以看出|'
     r'简单来说|简而言之)[，,]\s*', ''),
    ('的时候→时', r'的时候', '时'),
    ('冗余限定语', r'在一定程度上|某种程度上', ''),
]

# 双链 / 图片等不可触碰的片段：精简前先占位保护
PROTECT = re.compile(r'\[\[[^\]]*\]\]|\[img\[[^\]]*\]\]')

# 不参与精简的行：表格、图片、关联行、小标题、概括标签行
def leannable(line):
    s = line.strip()
    if not s: return False
    if ASSOC_LINE.match(s): return False
    if s.startswith('|') or s.startswith('[img['): return False
    if re.match(r'^!{1,6}\s', s): return False
    if s.startswith('一句话概括'): return False
    return True


def parse(raw):
    m = HDR.match(raw)
    head = m.group(1) if m else ''
    body = raw[m.end():] if m else ''
    return head, body


def title_of(head):
    for ln in head.splitlines():
        if ln.startswith('title:'):
            return ln[6:].strip()
    return ''


def lean_body(body, detail, fname):
    """逐行温和精简，返回 (新 body, 命中数)。双链/图片片段占位保护，绝不被改写。"""
    lines = body.replace('\r\n', '\n').split('\n')
    out, n = [], 0
    for ln in lines:
        if not leannable(ln):
            out.append(ln); continue
        # 保护 [[...]] / [img[...]]，占位符不会被任何规则命中
        saved = []

        def stash(m):
            saved.append(m.group(0))
            return '\x01%d\x01' % (len(saved) - 1)

        cur = PROTECT.sub(stash, ln)
        for name, pat, rep in LEAN_RULES:
            if name == '句首套话':
                # 去掉列表符号后再判句首，命中则删套话、保留列表符号
                m0 = re.match(r'^(\s*[*#]+\s*)(.*)$', cur)
                prefix, text = (m0.group(1), m0.group(2)) if m0 else ('', cur)
                newtext, c = re.subn(pat, rep, text, count=1)
                if c:
                    cur = prefix + newtext
                    n += c; detail[name] += c
                    detail['_lines'].append((fname, name, text[:60]))
            else:
                cur, c = re.subn(pat, rep, cur)
                if c:
                    n += c; detail[name] += c
                    detail['_lines'].append((fname, name, re.findall(pat, PROTECT.sub('', ln))[:3]))
        if saved:
            cur = re.sub(r'\x01(\d+)\x01', lambda m: saved[int(m.group(1))], cur)
        out.append(cur)
    return '\n'.join(out), n


def main():
    apply = '--apply' in sys.argv
    out = io.StringIO()
    before_all = json.loads((SNAPDIR / 'all_tiddlers_before.json').read_text(encoding='utf-8'))
    targets = json.loads((SNAPDIR / 'targets.json').read_text(encoding='utf-8'))

    # 本轮目标：快照里以「一句话概括」开头且非导航卡的 365 张
    goal = []
    for f in targets:
        h, b = parse(before_all.get(f, ''))
        t = title_of(h)
        if NAV.search(t) or not b.lstrip().startswith('一句话概括'):
            continue
        goal.append(f)
    print('本轮恢复目标（分点卡）: %d 张' % len(goal), file=out)

    detail = collections.Counter()
    detail['_lines'] = []
    stats = collections.Counter()
    samples = []
    writes = {}
    missing = []

    for f in goal:
        old_head, old_body = parse(before_all[f])
        cur_name = CUR_NAME.get(f, f)
        cur_path = ROOT / cur_name
        if not cur_path.exists():
            missing.append(cur_name); continue
        cur_raw = cur_path.read_text(encoding='utf-8', errors='replace')
        cur_head, cur_body = parse(cur_raw)
        nl = '\r\n' if '\r\n' in cur_raw else '\n'

        body = old_body.replace('\r\n', '\n')

        # 1) 重新应用上一轮语境词修正
        for a, b in FIX_BY_FILE.get(f, []):
            if a in body:
                body = body.replace(a, b, 1)
                stats['语境词修正'] += 1
            else:
                stats['语境词修正_未命中'] += 1

        # 2) 小标题里的「本章」去掉绑定来源措辞（!! 层级与列表符号不变）
        #    注：「一句话概括：」标签属于原样式，完整保留，不动
        body, c = re.subn(r'^(!!\s*)本章增量', r'\1增量', body, flags=re.M)
        stats['小标题去本章'] += c

        # 3) 恢复文本里残留的旧标题双链 → 新标题
        for old, new in MAP.items():
            pat = r'\[\[' + re.escape(old) + r'(\|[^\]]*)?\]\]'
            body, c = re.subn(pat, lambda m: '[[' + new + (m.group(1) or '') + ']]', body)
            stats['旧标题双链同步'] += c

        # 4) 温和精简
        body, n = lean_body(body, detail, f)
        stats['精简命中'] += n

        # 5) 仅当关联行不在末行时才归一（快照里本来就在末行，保留原间距）
        body = body.rstrip('\n')
        lines = body.split('\n')
        idx = [i for i, x in enumerate(lines) if ASSOC_LINE.match(x.strip())]
        if idx and idx[-1] != len(lines) - 1:
            assoc = lines[idx[-1]].strip()
            drop = set(idx)
            lines = [x for i, x in enumerate(lines) if i not in drop]
            while lines and not lines[-1].strip():
                lines.pop()
            lines += ['', assoc]
            body = '\n'.join(lines)
            stats['关联行归一'] += 1

        # 头部沿用当前文件（含新标题与 source 字段）
        newraw = cur_head + nl + nl + body.replace('\n', nl) + nl
        writes[cur_name] = newraw

        if len(samples) < 4:
            samples.append((cur_name, cur_body.strip(), body.strip()))

    print('待写文件: %d；找不到当前文件: %d' % (len(writes), len(missing)), file=out)
    if missing:
        for x in missing[:10]: print('  MISSING ' + x, file=out)

    print('\n== 处理统计 ==', file=out)
    for k, v in stats.most_common(): print('%5d  %s' % (v, k), file=out)
    print('\n== 精简规则命中 ==', file=out)
    for name, _, _ in LEAN_RULES:
        print('%5d  %s' % (detail.get(name, 0), name), file=out)
    print('\n== 精简明细（前 40 条） ==', file=out)
    for fname, name, hit in detail['_lines'][:40]:
        print('  [%s] %s → %s' % (name, fname[:34], str(hit)[:80]), file=out)

    for fname, before, after in samples:
        print('\n' + '=' * 66, file=out)
        print('文件: ' + fname, file=out)
        print('--- 当前（段落式）---\n' + before[:700], file=out)
        print('--- 恢复后（分点式 + 精简）---\n' + after[:700], file=out)

    if apply:
        for name, text in writes.items():
            (ROOT / name).write_text(text, encoding='utf-8', newline='')
        print('\n[APPLY] 已写入 %d 个文件' % len(writes), file=out)
        (SNAPDIR / 'restore_written.json').write_text(
            json.dumps(sorted(writes), ensure_ascii=False), encoding='utf-8')
    else:
        print('\n[DRY-RUN] 未写入任何文件', file=out)

    (P / '_restore_report.txt').write_text(out.getvalue(), encoding='utf-8')
    print('done')


if __name__ == '__main__':
    main()
