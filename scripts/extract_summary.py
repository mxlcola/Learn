# -*- coding: utf-8 -*-
"""把正文首段里现成的定义/结论句提取为「一句话概括：」。

适用条件（全部满足才动）：
1. 正文还没有 一句话概括
2. 首段不是标题、图片、列表、引用
3. 首段是完整一句（以 。！？ 结尾），且句中不含换行
4. 长度在 14–40 字之间
5. 首段后面还有正文（否则整段搬走会让卡片变空）

提取后该句从正文移除，避免与概括重复。
"""
import os
import re
import sys

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tiddlers')
SUMMARY_RE = re.compile(r'^一句话概括[：:]')
HEAD_RE = re.compile(r'^\s*!{1,3}\s')
JUNK_RE = re.compile(r'^\s*(\[img|#|\*|>|\||https?://)')
SENT_END = '。！？'
# 以指代词开头的句子是承接上文的，单独摘出来不成概括
PRONOUN_START = ('这', '那', '其', '它', '他', '她', '此', '该', '上述', '其中', '另外', '还有', '同时')


def parse(raw):
    m = re.match(r'(.*?)\r?\n\r?\n', raw, re.S)
    if not m:
        return raw, ''
    # 必须用 group(1)：m.start() 是 group 0 的起始，恒为 0
    return m.group(1), raw[m.end():]


def first_para(body):
    """取第一段非空文本，返回 (段落文本, 剩余正文)。"""
    lines = body.replace('\r\n', '\n').split('\n')
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    end = start
    while end < len(lines) and lines[end].strip():
        end += 1
    para = '\n'.join(lines[start:end]).strip()
    rest = '\n'.join(lines[end:]).strip('\n')
    return para, rest


def main(dry=False):
    done, skipped = [], []
    for fn in sorted(os.listdir(D)):
        if not fn.endswith('.tid') or fn.startswith('$'):
            continue
        p = os.path.join(D, fn)
        raw = open(p, 'rb').read().decode('utf-8')
        head, body = parse(raw)
        b = body.replace('\r\n', '\n').strip()
        if not b or SUMMARY_RE.match(b):
            continue
        para, rest = first_para(b)
        if not rest.strip():
            skipped.append((fn[:-4], '首段之后没有正文，搬走会变空'))
            continue
        if HEAD_RE.match(para) or JUNK_RE.match(para):
            skipped.append((fn[:-4], '首段是标题/图片/列表，不提取'))
            continue
        if '\n' in para:
            skipped.append((fn[:-4], '首段是多行'))
            continue
        if para[-1] not in SENT_END:
            skipped.append((fn[:-4], '首段不是完整句'))
            continue
        # 只取到第一个句号，避免把一整段搬上去
        cut = min([i for i, ch in enumerate(para) if ch in SENT_END] or [len(para)])
        sent = para[:cut + 1]
        L = len(sent)
        if not (14 <= L <= 40):
            skipped.append((fn[:-4], '首句 %d 字，需人工' % L))
            continue
        if sent.startswith(PRONOUN_START):
            skipped.append((fn[:-4], '首句以指代词开头，是承接上文'))
            continue
        nl = '\r\n' if '\r\n' in raw else '\n'
        # 先把三段统一成 \n 再拼接，最后只做一次换行符转换，
        # 否则 \r\n 里的 \n 会被二次替换成 \r\r\n
        head_u = head.replace('\r\n', '\n').replace('\r', '\n')
        rest_u = rest.replace('\r\n', '\n').replace('\r', '\n')
        out_u = head_u + '\n\n' + ('一句话概括：' + sent + '\n\n' + rest_u).rstrip('\n') + '\n'
        out = out_u.replace('\n', nl)
        if out == raw:
            continue
        done.append((fn[:-4], L))
        if dry and len(done) == 1:
            print('[预演样例] %s' % fn)
            print('   out 前160字节: %r' % out[:160])
            print('   原 raw 前80字节: %r' % raw[:80])
        if not dry:
            open(p, 'wb').write(out.encode('utf-8'))

    print('%s提取 %d 张' % ('[预演] ' if dry else '', len(done)))
    for t, L in done:
        print('   %-34s %d字' % (t[:34], L))
    if skipped:
        print('\n需人工处理 %d 张，原因分布：' % len(skipped))
        import collections
        c = collections.Counter('、'.join(w.split('，')[1:]) if '，' in w else w for _, w in skipped)
        for k, v in c.most_common(6):
            print('   %-24s %d' % (k, v))


if __name__ == '__main__':
    main('--dry-run' in sys.argv)
