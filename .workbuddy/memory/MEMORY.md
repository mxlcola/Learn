# Learn 项目长期备忘

## TiddlyWiki 知识库（tiddlywiki.info + tiddlers/，约 1064 条）

### 条目体例
- 三层结构固定：一句话概括（≤40字）→ 要点（2–4条）→ 末行「关联：」（按需，可为空）。
- **标题体例**：概念类条目用名词式（如《原子笔记》《永久笔记》）；原则/主张类条目用判断句式
  （如《常青笔记应面向概念》《纸笔记录优于App》）。2026-11-03 曾把常青笔记系列改成名词式，
  用户最终确认**按原判断句式标题**——两种体例并存，改标题前先问。
- 标题是主键：必须唯一稳定，差一个标点会被脚本归一化后互相覆盖；改标题前先查反链。
- 正文关系用内联双链表达，末行「关联：」只补漏，不设数量配额。

### 脚本（scripts/）
- `lint_cards.py [标签...]`：全库体检（缺概括/空条目/小标题过多/正文过长/碎片/悬空链接）。
- `extract_summary.py`：从正文首段提取现成概括（--dry-run 先预演）。
- `normalize_tooth.py`、`archive_conflicts.py`、`find_dup_titles.py` 等域脚本可复用其解析写法。
- 解析 .tid 头部要用 `re.match(r'(.*?)\r?\n\r?\n', raw, re.S)` 后取 **m.group(1)**，不能用 m.start()。

### 环境坑
- Nutstore 同步目录 IO 慢且不稳定：`python -c`、head、for 循环常被 SIGTERM；
  输出重定向到文件再读；大范围检索先把目标域合并成单个文本。
- 提交时 git 的 CRLF warning 可忽略。
- `scripts/_anki/` 在 .gitignore 里（Anki 数据库副本与读书摘录，个人数据不入库）。

### Anki 侧
- 库：`C:\Users\Te\AppData\Roaming\Anki2\账户 1\collection.anki2`（新 schema，查询需注册 unicase collation）。
- 牌组「读书笔记::减肥」379 条 = 272 问答卡 + 107 微信读书划线；与 Wiki 的分工：
  Anki 自测复述，Wiki 建框架理解；映射见 Wiki 卡《Anki减肥牌组与Wiki对照》。

### 遗留待办
- 全库缺一句话概括 269 条、空条目 147 条、小标题过多 65、正文过长 26、碎片 23。
