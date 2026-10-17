from pathlib import Path
import subprocess,re

keys=('减肥','减脂','体重','饮食','运动','GLP','医学减')
skip=('《','冯雪','300天','章节地图','章节索引','概念索引','练习索引','对应表')

def read_head(path):
    try:
        return subprocess.check_output(['git','show','HEAD:'+path.as_posix()],stderr=subprocess.DEVNULL).decode('utf-8-sig','ignore')
    except Exception:
        return ''

def link_titles(text):
    result=[]
    for item in re.findall(r'\[\[([^\]]+)\]\]',text):
        title=item.split('|',1)[0].strip()
        if title and title not in result:
            result.append(title)
    return result

def source_units(body):
    units=[]
    for line in body.splitlines():
        line=line.strip()
        if not line or line.startswith('!!') or line.startswith('一句话概括：'):
            continue
        if line.startswith(('关联：','实践中可结合','来源：','来源 ')):
            continue
        line=re.sub(r'^\s*[#*]\s*','',line)
        line=re.sub(r'^\s*\|.*\|\s*$','',line)
        line=re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]',r'\1',line)
        line=re.sub(r'\s+',' ',line).strip()
        if line:
            units.append(line)
    return units

def split_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[。！？!?])',text) if s.strip()]

changed=0
for path in Path('tiddlers').glob('*.tid'):
    if not any(word in path.name for word in keys) or any(word in path.name for word in skip):
        continue
    current=path.read_text(encoding='utf-8-sig')
    original=read_head(path)
    old_parts=re.split(r'\r?\n\s*\r?\n',original,maxsplit=1)
    cur_parts=re.split(r'\r?\n\s*\r?\n',current,maxsplit=1)
    if len(old_parts)<2 or len(cur_parts)<2:
        continue
    old_body=old_parts[1]
    header=cur_parts[0]
    summary_match=re.search(r'^一句话概括：(.+)$',cur_parts[1],re.M)
    summary=summary_match.group(1).strip() if summary_match else ''
    units=source_units(old_body)
    # Drop a source sentence that merely repeats the original summary.
    original_summary=re.search(r'^一句话概括：(.+)$',old_body,re.M)
    if original_summary:
        duplicate=original_summary.group(1).strip()
        units=[u for u in units if u!=duplicate]
    selected=[]
    for unit in units:
        for sentence in split_sentences(unit):
            if sentence and sentence not in selected:
                selected.append(sentence)
            if len(selected)>=4:
                break
        if len(selected)>=4:
            break
    if not selected:
        selected=[summary or f'本条说明“{path.stem}”的核心原则。']
    core=''.join(selected)
    links=[x for x in link_titles(old_body) if x not in path.stem and f'[[{x}]]' not in core][:10]
    if links:
        core += ' 可结合'+'、'.join(f'[[{x}]]' for x in links)+'理解。'
    explanation=''.join(split_sentences(core)[:3])
    if len(split_sentences(explanation))<2:
        explanation += f'应用时结合个人情况和持续反馈调整。'
    if not summary:
        summary=selected[0]
    new=header+f'\n\n一句话概括：{summary}\n\n!! 核心知识\n{core}\n\n!! 简明解释\n{explanation}\n'
    path.write_text(new,encoding='utf-8')
    changed+=1
print(f'repaired {changed}')
