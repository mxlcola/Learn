# -*- coding: utf-8 -*-
"""按常青笔记体例整理减肥 / 运动 / 饮食旧卡（2026-11-06）。

⚠️ 已废弃其段落化部分：用户 2026-11-06 明确要求「分点描述不能修改样式，可以精简内容」，
   365 张卡的分点样式已由 scripts/restore_bullet_style.py 恢复。
   **不要再运行 --apply**，否则会把 `!! 要点` / `*` / `#` 重新压成段落。
   本文件现仅作为 MAP / SOURCE 改名映射与解析写法的参考来源。

用法：
    python scripts/refine_evergreen_cards.py --dry-run   # 预演：输出转换样例与统计，不写文件
    python scripts/refine_evergreen_cards.py --apply     # 落地：写回并同步全库反链

做四件事：
  1. 28 张「《书》第N章-…」章节卡改为面向概念的新标题（概念名词式 / 判断句式并存），
     并补 source 字段保留出处。
  2. 标准模板卡正文由「一句话概括：+ !! 要点 / !! 怎么做 + 列表」压成纯段落式；
     导航卡保留小标题与表格，只去概括标签、统一关联行。
  3. 全库 1300+ 张 .tid 同步替换所有指向旧标题的双链（含 [[A|别名]]、地图表格）。
  4. 回退快照写到系统临时目录（项目内不留备份），输出校验报告。

原则：零信息丢失——不删事实、数据、双链、图片、表格；只去模板标签与列表符号。
"""
import pathlib, json, re, io, sys, tempfile

P = pathlib.Path(__file__).resolve().parent.parent
ROOT = P / 'tiddlers'
HDR = re.compile(r'(.*?)\r?\n\r?\n', re.S)
ASSOC = re.compile(r'^关联[：:]\s*(.*)$')

CORE = {'减肥', '饮食', '运动', '科学减肥', '正念饮食', '热量', '体重', '饱腹', '饥饿',
        '睡眠', '压力', '反弹', '行为干预', '生活方式', '身体', '健康', '乐天瘦身法',
        '放弃减肥我瘦了60斤', '超慢跑', '轻断食', '代餐', '心态', '生活化减脂', '减脂',
        '有氧运动', '力量训练'}
EXCLUDE = {'生活压力如何影响交易？'}          # 因「压力」标签误收的交易卡
NAV = re.compile(r'章节地图|索引|拆书|对应表|大纲|参考文献|发刊词|目录|对照|总结|16讲|全套')

# 旧标题 → 面向概念的新标题（概念名词式 / 判断句式，双体例并存）
MAP = {
    '《放弃减肥，我瘦了60斤》第1章-你被骗了': '减肥失败应归因于方案而非意志',
    '《放弃减肥，我瘦了60斤》第2章-开启你的最后一次减肥之旅': '减肥前先确认目标与健康边界',
    '《放弃减肥，我瘦了60斤》第3章-我相信你的决心但我更相信人性': '决心撑不起长期减肥系统',
    '《放弃减肥，我瘦了60斤》第4章-你需要300天': '减肥是数百天工程而非几周冲刺',
    '《放弃减肥，我瘦了60斤》第5章-持续减肥的策略': '持续减肥靠降低阻力而非提高耐受力',
    '《放弃减肥，我瘦了60斤》第6章-像刷牙一样去运动': '运动习惯靠低门槛与固定提示',
    '《放弃减肥，我瘦了60斤》第7章-别再跑步减肥了': '跑步不是减肥的默认答案',
    '《放弃减肥，我瘦了60斤》第8章-瘦子从来不算卡路里': '不算卡路里不等于否认能量平衡',
    '《放弃减肥，我瘦了60斤》第9章-总是吃多怎么办': '吃多不是人格失败',
    '《放弃减肥，我瘦了60斤》第10章-减肥减的是心': '不反弹靠切换生活模式',
    '《放弃减肥，我瘦了60斤》第11章-减肥的时候该吃什么': '长期禁止食物会把它变成补偿',
    '《放弃减肥，我瘦了60斤》第12章-饮食的断舍离': '吃不吃按当下是否还需要这一口决定',
    '《放弃减肥，我瘦了60斤》第13章-记录减肥法': '记录减肥法按阶段建立身体反馈',
    '《放弃减肥，我瘦了60斤》第14章-都会好的': '减肥是无限游戏，中断后还能回来',
    '《正念饮食》第一章-认识正念饮食': '正念饮食重建人与食物的关系',
    '《正念饮食》第二章-培养正念习惯': '正念习惯落在自动进食的瞬间',
    '《正念饮食》第三章-真正的饥饿感': '进食原因不止生理饥饿',
    '《正念饮食》第四章-你为什么不满足': '满足感由三种身体信号构成',
    '《正念饮食》第五章-培养外在智慧': '外在智慧只做参考，不当食物警察',
    '《正念饮食》第六章-认识你的饮食模式': '记录用变化而非完美衡量进展',
    '《正念饮食》第七章-改变你的饮食模式': '暂停能力靠呼吸与静坐练出来',
    '《正念饮食》第八章-你是真的饿了还是想吃': '吃前给饥饿打分',
    '《正念饮食》第九章-唤醒你的内在美食家': '用内在美食家替代食物警察',
    '《正念饮食》第十章-开心享受但不一定要吃完': '把享受和清盘分开',
    '《正念饮食》第十一章-告别热量焦虑': '热量应帮助选择而非统治饮食',
    '《正念饮食》第十二章-选择真正想吃的': '正念选择要进入真实食物场景',
    '《正念饮食》第十三章-告别压力型进食': '安抚自己的路径不该只有食物',
    '《正念饮食》第十四章-享受新的食物关系': '用关系变化衡量正念饮食成效',
}
SOURCE = {}
for _k in MAP:
    if _k.startswith('《放弃减肥'):
        _ch = _k.split('第', 1)[1].split('章', 1)[0]
        SOURCE[_k] = '《放弃减肥，我瘦了60斤》第%s章' % _ch
    else:
        _ch = _k.split('《正念饮食》', 1)[1].split('-', 1)[0]
        SOURCE[_k] = '《正念饮食》%s' % _ch

PUNCT = '。！？；.!?;：:，,、）)】」』…'


def parse(f):
    raw = f.read_text(encoding='utf-8', errors='replace')
    m = HDR.match(raw)
    head = m.group(1) if m else ''
    body = raw[m.end():] if m else ''
    d = {}
    for line in head.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            d[k.strip()] = v.strip()
    nl = '\r\n' if '\r\n' in raw else '\n'
    return d, body, raw, head, nl


def join_items(items):
    buf = []
    for s in items:
        s = s.strip()
        if not s:
            continue
        if s[-1] not in PUNCT:
            s += '。'
        buf.append(s)
    return ''.join(buf)


def to_prose(body):
    """模板卡 → 纯段落式：去概括标签与 !! 小标题，列表项并成自然段，表格/图片原样。"""
    lines = body.replace('\r\n', '\n').split('\n')
    blocks = []          # (kind, text)  kind: prose | table | img
    cur_items = []
    summary = None
    assoc = None

    def flush():
        nonlocal cur_items
        if cur_items:
            t = join_items(cur_items)
            if t:
                blocks.append(('prose', t))
            cur_items = []

    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            flush(); i += 1; continue
        m = ASSOC.match(s)
        if m:
            flush(); assoc = s; i += 1; continue
        if s.startswith('一句话概括：') or s.startswith('一句话概括:'):
            flush()
            summary = re.split(r'[：:]', s, maxsplit=1)[1].strip()
            i += 1; continue
        if re.match(r'^!{1,6}\s', s) or re.match(r'^!{1,6}\S', s):
            flush(); i += 1; continue
        if s.startswith('|'):
            flush()
            tbl = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tbl.append(lines[i].strip()); i += 1
            blocks.append(('table', '\n'.join(tbl)))
            continue
        if s.startswith('[img['):
            flush(); blocks.append(('img', s)); i += 1; continue
        lm = re.match(r'^([*#]+)\s*(.*)$', s)
        if lm:
            cur_items.append(lm.group(2)); i += 1; continue
        flush(); blocks.append(('prose', s)); i += 1
    flush()

    out = []
    if summary:
        out.append(summary)
    for kind, text in blocks:
        out.append(text)
    res = '\n\n'.join(out)
    if assoc:
        res += '\n\n' + assoc
    return res


def light_nav(body):
    """导航卡：保留小标题/表格/列表，只去「一句话概括：」标签、把关联行收为末行。"""
    lines = body.replace('\r\n', '\n').split('\n')
    assoc = None
    out = []
    for s in lines:
        t = s.strip()
        if ASSOC.match(t):
            assoc = t
            continue
        if t.startswith('一句话概括：') or t.startswith('一句话概括:'):
            out.append(re.split(r'[：:]', t, maxsplit=1)[1].strip())
            continue
        out.append(s)
    while out and not out[-1].strip():
        out.pop()
    res = '\n'.join(out)
    if assoc:
        res += '\n\n' + assoc
    return res


def build_header(head, newtitle, extra_source=None, nl='\n'):
    lines = head.replace('\r\n', '\n').split('\n')
    out, has_title, has_source = [], False, False
    for ln in lines:
        if re.match(r'^title\s*:', ln):
            out.append('title: ' + newtitle); has_title = True
        elif re.match(r'^source\s*:', ln):
            out.append(ln); has_source = True
        else:
            out.append(ln)
    if not has_title:
        out.append('title: ' + newtitle)
    if extra_source and not has_source:
        out.append('source: ' + extra_source)
    return nl.join(out)


def main():
    apply = '--apply' in sys.argv
    out = io.StringIO()

    j = json.loads((P / '《我们为什么吃（太多）》卡片-批量导入.json').read_text(encoding='utf-8'))
    today = {t.get('title', '') for t in j}

    parsed = {}
    for f in ROOT.glob('*.tid'):
        d, b, raw, head, nl = parse(f)
        title = d.get('title', '') or f.stem
        parsed[f.name] = dict(f=f, d=d, b=b, raw=raw, head=head, nl=nl, title=title)

    targets = []
    for fname, v in parsed.items():
        if v['title'] in today or v['title'] in EXCLUDE:
            continue
        tags = set(x[0] or x[1] for x in re.findall(r'\[\[([^\]]+)\]\]|(\S+)', v['d'].get('tags', '')))
        if tags & CORE:
            targets.append(fname)
    print('命中待整理: %d 张' % len(targets), file=out)

    # 回退快照（系统临时目录，项目内不留备份）
    if apply:
        snapdir = pathlib.Path(tempfile.gettempdir()) / 'evergreen_refine_20261106'
        snapdir.mkdir(parents=True, exist_ok=True)
        (snapdir / 'all_tiddlers_before.json').write_text(
            json.dumps({k: v['raw'] for k, v in parsed.items()}, ensure_ascii=False), encoding='utf-8')
        (snapdir / 'targets.json').write_text(
            json.dumps(sorted(targets), ensure_ascii=False), encoding='utf-8')
        print('回退快照: %s' % snapdir, file=out)

    # 逐张生成新内容
    built = {}       # fname -> (newraw, newtitle)
    stats = {'prose': 0, 'nav': 0, 'skip': 0}
    samples = []
    for fname in targets:
        v = parsed[fname]
        old_title, b, head, nl = v['title'], v['b'], v['head'], v['nl']
        new_title = MAP.get(old_title)
        is_nav = bool(NAV.search(old_title))
        if not b.lstrip().startswith('一句话概括：'):
            newbody = light_nav(b)
            stats['skip'] += 1
        elif is_nav:
            newbody = light_nav(b)
            stats['nav'] += 1
        else:
            newbody = to_prose(b)
            stats['prose'] += 1
            if len(samples) < 5:
                samples.append((old_title, new_title or old_title, b.strip(), newbody.strip()))

        newhead = build_header(head, new_title or old_title, SOURCE.get(old_title), nl)
        newraw = newhead + nl + nl + newbody.replace('\n', nl) + nl
        built[fname] = (newraw, new_title or old_title)

    print('转换统计: %s' % stats, file=out)

    # 全库反链替换（所有 .tid，含今日 108 张新卡与非命中卡）
    # 两类引用：(a) [[旧标题]] / [[旧标题|别名]]；(b) 头部字段值恰好等于旧标题（如 list:）
    link_changes = field_changes = 0
    final = {}
    for fname, v in parsed.items():
        text = built[fname][0] if fname in built else v['raw']
        for old, new in MAP.items():
            pat = r'\[\[' + re.escape(old) + r'(\|[^\]]*)?\]\]'
            text, n = re.subn(pat, lambda m: '[[' + new + (m.group(1) or '') + ']]', text)
            link_changes += n
        # 头部字段：仅处理第一个空行之前的行（无正文时整文件即头部），值整段精确匹配
        mm = re.search(r'\r?\n\r?\n', text)
        headpart = text[:mm.start()] if mm else text.rstrip('\r\n')
        tailpart = text[mm.end():] if mm else None
        hlines = headpart.split('\n')
        head_touched = False
        for idx, ln in enumerate(hlines):
            if ':' in ln:
                key, val = ln.split(':', 1)
                v2 = val.strip().rstrip('\r')
                if v2 in MAP:
                    hlines[idx] = key + ': ' + MAP[v2] + ('\r' if val.endswith('\r') else '')
                    field_changes += 1
                    head_touched = True
        if head_touched:
            newhead = '\n'.join(hlines)
            if mm:
                text = newhead + ('\r\n\r\n' if '\r\n' in mm.group(0) else '\n\n') + tailpart
            else:
                text = newhead + ('\r\n' if '\r\n' in v['raw'] else '\n')
        final[fname] = text
    print('反链替换次数: %d；头部字段同步: %d' % (link_changes, field_changes), file=out)

    # 改名映射：旧文件名 -> 新文件名
    renames = {fname: built[fname][1] + '.tid' for fname in built
               if built[fname][1] != parsed[fname]['title']}
    # 落盘清单：内容有变化的所有文件（含仅因反链变化者）
    changed = {f: t for f, t in final.items() if t != parsed[f]['raw']}
    print('改名文件: %d；内容有变化待写: %d' % (len(renames), len(changed)), file=out)

    for old, new, before, after in samples:
        print('\n' + '=' * 70, file=out)
        print('标题: %s%s' % (old, ('  →  ' + new) if new != old else ''), file=out)
        print('--- 原文 ---\n%s' % before[:800], file=out)
        print('--- 新文 ---\n%s' % after[:800], file=out)

    if apply:
        for fname, text in changed.items():
            target_name = renames.get(fname, fname)
            (ROOT / target_name).write_text(text, encoding='utf-8', newline='')
        for fname, newname in renames.items():
            oldf = ROOT / fname
            if oldf.exists() and newname != fname:
                oldf.unlink()
        print('\n已写入 %d 个文件，删除旧名文件 %d 个' % (len(changed), len(renames)), file=out)
    else:
        print('\n[DRY-RUN] 未写入任何文件', file=out)

    (P / '_refine_report.txt').write_text(out.getvalue(), encoding='utf-8')
    print(out.getvalue()[-1200:])


if __name__ == '__main__':
    main()
