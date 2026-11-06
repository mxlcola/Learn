"""把指定的 .tid 卡片导出为 TiddlyWiki 可批量导入的 JSON 数组。

用法:
    python scripts/export_cards_json.py <输出.json> <标题1> <标题2> ...
    python scripts/export_cards_json.py <输出.json> --from-map <地图卡标题>

标题即 tiddlers/ 下的文件名（不含 .tid 后缀）。
--from-map 模式从索引卡表格行（以 | 开头）中提取所有双链标题并去重，
自动把地图卡本身排在第一位，适合按章节地图批量导出整本书。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TIDDLERS = ROOT / "tiddlers"


def parse_tid(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"(.*?)\r?\n\r?\n", raw, re.S)
    if not m:
        raise ValueError(f"无法解析 .tid 头部: {path}")
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    fields["text"] = raw[m.end():].strip("\r\n")
    return fields


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    out_path = Path(sys.argv[1])
    if sys.argv[2] == "--from-map":
        map_title = sys.argv[3]
        raw = (TIDDLERS / f"{map_title}.tid").read_text(encoding="utf-8")
        titles = [map_title]
        for line in raw.splitlines():
            if line.startswith("|"):
                for name in re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", line):
                    if name not in titles:
                        titles.append(name)
    else:
        titles = sys.argv[2:]
    cards = []
    for title in titles:
        path = TIDDLERS / f"{title}.tid"
        card = parse_tid(path)
        card["title"] = title
        cards.append(card)
    out_path.write_text(
        json.dumps(cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"exported {len(cards)} tiddlers -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
