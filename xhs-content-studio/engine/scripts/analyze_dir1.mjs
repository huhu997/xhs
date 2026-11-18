#!/usr/bin/env node
import fs from "node:fs";
const data = JSON.parse(fs.readFileSync("all_notes_cli.json", "utf-8"));
function parseLiked(s) {
  if (!s) return 0;
  s = String(s).replace(/[, ]/g, "");
  let m = s.match(/([\d.]+)\s*万/); if (m) return Math.round(parseFloat(m[1]) * 10000);
  m = s.match(/([\d.]+)\s*千/); if (m) return Math.round(parseFloat(m[1]) * 1000);
  return parseInt(s.replace(/\D/g, "")) || 0;
}
const rated = data.map(n => ({ ...n, like: parseLiked(n.liked) }));
// 按关键词分组
const byKw = {};
for (const n of rated) (byKw[n.kw] = byKw[n.kw] || []).push(n);
console.log("=== 各关键词竞争度（n / 平均赞 / 最高赞 / Top标题）===");
for (const kw of Object.keys(byKw)) {
  const arr = byKw[kw].slice().sort((a, b) => b.like - a.like);
  const avg = Math.round(arr.reduce((s, x) => s + x.like, 0) / arr.length);
  console.log(`【${kw}】 n=${arr.length} 平均赞=${avg} 最高赞=${arr[0].like} | Top: ${arr[0].title.slice(0, 28)}`);
}
// 赞数分档
const b = { "<1k": 0, "1k-3k": 0, "3k-8k": 0, ">8k": 0 };
for (const n of rated) {
  if (n.like < 1000) b["<1k"]++; else if (n.like < 3000) b["1k-3k"]++;
  else if (n.like < 8000) b["3k-8k"]++; else b[">8k"]++;
}
console.log("\n=== 全量赞数分档 ===");
console.log(JSON.stringify(b));
console.log(`总数=${rated.length} 总赞=${rated.reduce((s, x) => s + x.like, 0)}`);
// Top 30 高赞（用于评论挖掘）
const top = rated.slice().sort((a, b) => b.like - a.like).slice(0, 30);
console.log("\n=== Top30 高赞笔记（评论挖掘候选）===");
top.forEach((n, i) => console.log(`${i + 1}. [${n.kw}] ${n.like}赞 | ${n.title.slice(0, 38)} | ${n.tokenUrl}`));
// 导出 Top30 链接供评论脚本
fs.writeFileSync("top30_for_comments.json", JSON.stringify(top.map(n => ({ kw: n.kw, noteId: n.noteId, title: n.title, liked: n.liked, tokenUrl: n.tokenUrl })), null, 2));
console.log("\n已导出 top30_for_comments.json");
