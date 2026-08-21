import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const dir = path.join(root, 'tiddlers');
const relevantTags = /减肥|减脂|运动|饮食|正念饮食|热量|体重|超慢跑|腹型肥胖|内脏脂肪/;
const linkRe = /\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g;

const manual = new Map(Object.entries({
  '正念饮食': ['正常饮食逻辑', '正念饮食觉知训练', '饮食安全感'],
  '正常饮食逻辑': ['饮食安全感', '正念饮食', '吃多了过了就过了'],
  '减肥和运动的关系': ['减肥中的能量平衡', '运动单独减重效果有限', '减脂运动组合'],
  '减肥中的能量平衡': ['能量缺口', '吸收端减脂策略', '消耗端减脂策略'],
  '消耗端减脂策略': ['减肥中的能量平衡', '减脂运动组合', '非运动消耗'],
  '吸收端减脂策略': ['减肥中的能量平衡', '调整饮食结构', '正常饮食逻辑'],
  '减脂运动组合': ['减肥和运动的关系', '低强度有氧运动', '抗阻训练'],
  '乐天瘦身法': ['乐天记录减肥法', '减肥阻力最小化', '不跑步、不节食、不坚持'],
  '减肥的底层逻辑，原来在《毛选》两论里': ['减肥中的能量平衡', '减脂的主要矛盾', '个性化减脂实践'],
  '个性化减脂实践': ['减肥中的实事求是', '身体说明书', '减肥中的自我商量'],
  '体重波动应对能力': ['七日平均体重', '称重心态', '体重记录注意事项'],
  '减肥中的可持续性': ['减肥阻力最小化', '微目标', '减肥持久战'],
  '减脂不反弹': ['体重反弹', '胖瘦生活模式', '减肥中的可持续性'],
  '减肥是一种生活方式': ['生活化减脂', '胖瘦生活模式', '减肥中的可持续性'],
  '减肥完整方案': ['减肥系统', '减肥中的能量平衡', '减脂运动组合'],
  '系统性减肥框架': ['减肥系统', '减肥中的能量平衡', '生活化减脂'],
  '热量表减肥迷思': ['食物能量觉知', '卡路里奴隶', '正常饮食逻辑'],
  '减肥记录': ['乐天记录减肥法', '饱腹度记录', '体重记录注意事项'],
  '称重心态': ['体重波动应对能力', '七日平均体重', '减肥中的自我接纳'],
  '生活方式干预减肥': ['生活化减脂', '减肥同伴行动', '压力和睡眠减肥'],
}));

function field(text, name) {
  const match = text.match(new RegExp(`^${name}: (.*)$`, 'm'));
  return match ? match[1].trim() : '';
}

function firstDistinctLinks(tail, max = 3) {
  const result = [];
  const seen = new Set();
  linkRe.lastIndex = 0;
  for (let match; (match = linkRe.exec(tail));) {
    const link = match[1].trim();
    if (!seen.has(link)) {
      seen.add(link);
      result.push(link);
    }
    if (result.length >= max) break;
  }
  return result;
}

function writeSafe(file, content) {
  try {
    fs.writeFileSync(file, content, 'utf8');
    return;
  } catch (error) {
    const bak = `${file}.bak`;
    if (fs.existsSync(bak)) throw new Error(`Backup already exists: ${bak}`);
    fs.renameSync(file, bak);
    try {
      fs.writeFileSync(file, content, 'utf8');
      fs.unlinkSync(bak);
    } catch (writeError) {
      if (!fs.existsSync(file) && fs.existsSync(bak)) fs.renameSync(bak, file);
      throw writeError;
    }
  }
}

const changed = [];

for (const name of fs.readdirSync(dir)) {
  if (!name.endsWith('.tid')) continue;
  const file = path.join(dir, name);
  const text = fs.readFileSync(file, 'utf8');
  const tags = field(text, 'tags');
  if (!relevantTags.test(tags)) continue;

  const title = field(text, 'title');
  const idx = text.lastIndexOf('关联：');
  if (idx < 0) continue;

  const tail = text.slice(idx);
  const before = [...tail.matchAll(linkRe)].length;
  if (before <= 3) continue;

  const chosen = manual.get(title) ?? firstDistinctLinks(tail, 3);
  const body = text.slice(0, idx).trimEnd();
  const newTail = `关联：\n${chosen.map((item) => `[[${item}]]`).join('\n')}\n`;
  const next = `${body}\n\n${newTail}`;

  if (next !== text) {
    writeSafe(file, next);
    changed.push({ title, file: name, before, after: chosen.length });
  }
}

changed.sort((a, b) => b.before - a.before || a.file.localeCompare(b.file, 'zh-Hans-CN'));
for (const row of changed) {
  console.log(`${row.before}->${row.after}\t${row.file}\t${row.title}`);
}
console.log(`Changed count: ${changed.length}`);
