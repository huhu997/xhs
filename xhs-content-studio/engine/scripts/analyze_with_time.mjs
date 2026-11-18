#!/usr/bin/env node
// 分析（数据源 = 本次带发布时间的 all_notes_with_time.json，300条自洽）
// 输出：新老分桶对比 + 近30天新爆选题信号 + 各关键词竞争度
import fs from "node:fs";
const data = JSON.parse(fs.readFileSync("all_notes_with_time.json", "utf-8"));
const TODAY = new Date(); TODAY.setHours(0, 0, 0, 0);

function parseLiked(s) {
  if (!s) return 0;
  s = String(s).replace(/[, ]/g, "");
  let m = s.match(/([\d.]+)\s*万/); if (m) return Math.round(parseFloat(m[1]) * 10000);
  m = s.match(/([\d.]+)\s*千/); if (m) return Math.round(parseFloat(m[1]) * 1000);
  return parseInt(s.replace(/\D/g, "")) || 0;
}
function parsePubTime(raw) {
  if (!raw) return null;
  raw = String(raw).trim();
  let m = raw.match(/(\d+)\s*天前/); if (m) { const d = new Date(TODAY); d.setDate(d.getDate() - Number(m[1])); return d; }
  m = raw.match(/(\d+)\s*小时前/); if (m) { const d = new Date(TODAY); d.setHours(d.getHours() - Number(m[1])); return d; }
  m = raw.match(/(\d+)\s*分钟前/); if (m) return new Date(TODAY);
  m = raw.match(/昨天|前天/); if (m) { const d = new Date(TODAY); d.setDate(d.getDate() - (m[0] === '昨天' ? 1 : 2)); return d; }
  m = raw.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/); if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  m = raw.match(/^(\d{1,2})-(\d{1,2})$/); if (m) { const mo = Number(m[1]), da = Number(m[2]); let y = TODAY.getFullYear(); const cand = new Date(y, mo - 1, da); if (cand > TODAY) y--; return new Date(y, mo - 1, da); }
  return null;
}

const rated = data.map(n => {
  const date = parsePubTime(n.pubTime);
  const daysAgo = date ? Math.round((TODAY - date) / 86400000) : null;
  return { ...n, like: parseLiked(n.liked), pubDate: date ? date.toISOString().slice(0, 10) : null, daysAgo };
});
const noTime = rated.filter(n => n.daysAgo === null).length;

function bucket(d) { if (d === null) return "未知"; if (d <= 7) return "近7天"; if (d <= 30) return "近30天(8-30)"; if (d <= 180) return "近半年(31-180)"; if (d <= 365) return "半年-1年"; return "1年以上"; }
const order = ["近7天", "近30天(8-30)", "近半年(31-180)", "半年-1年", "1年以上", "未知"];
const stat = {}; order.forEach(b => stat[b] = { n: 0, sum: 0, bomb: 0 });
rated.forEach(n => { const b = bucket(n.daysAgo); stat[b].n++; stat[b].sum += n.like; if (n.like >= 3000) stat[b].bomb++; });

console.log("今天", TODAY.toISOString().slice(0, 10), "| 总笔记", rated.length, "| 无时间(空值)", noTime);
console.log("\n=== 新老分桶（发布时间维度）===");
console.log("分桶                 n    均赞   爆款>3k  爆款率");
order.forEach(b => { const s = stat[b]; const avg = s.n ? s.sum / s.n : 0; const rate = s.n ? (s.bomb / s.n * 100).toFixed(1) + "%" : "-"; console.log(b.padEnd(18), String(s.n).padStart(4), String(Math.round(avg)).padStart(6), String(s.bomb).padStart(6), "  ", rate); });

const recent = rated.filter(n => n.daysAgo !== null && n.daysAgo <= 30);
const recentAvg = recent.length ? Math.round(recent.reduce((s, x) => s + x.like, 0) / recent.length) : 0;
console.log(`\n=== 近30天新发: ${recent.length}条 | 近30天均赞 ${recentAvg} ===`);
const rb = recent.filter(n => n.like >= 1000).sort((a, b) => b.like - a.like).slice(0, 20);
console.log("近30天千赞+ Top20（当下最热选题信号）:");
rb.forEach((n, i) => console.log(`${String(i + 1).padStart(2)}. [${n.kw}] ${String(n.like).padStart(6)} | ${n.daysAgo}天前(${n.pubTime}) | ${n.title.slice(0, 36)}`));

console.log("\n=== 各关键词竞争度（本次带时间数据统一口径）===");
const kws = {}; rated.forEach(n => (kws[n.kw] = kws[n.kw] || []).push(n));
console.log("关键词               n   均赞   最高赞  爆款>3k  近30天数  半年以上");
Object.keys(kws).forEach(kw => {
  const a = kws[kw];
  const avg = Math.round(a.reduce((s, x) => s + x.like, 0) / a.length);
  const max = Math.max(...a.map(x => x.like));
  const bomb = a.filter(x => x.like >= 3000).length;
  const rec = a.filter(x => x.daysAgo !== null && x.daysAgo <= 30).length;
  const old = a.filter(x => x.daysAgo !== null && x.daysAgo > 180).length;
  console.log(kw.padEnd(16), String(a.length).padStart(3), String(avg).padStart(6), String(max).padStart(7), String(bomb).padStart(5), String(rec).padStart(8), String(old).padStart(7));
});

fs.writeFileSync("notes_with_time_analyzed.json", JSON.stringify(rated, null, 2), "utf-8");
console.log("\n已存 notes_with_time_analyzed.json");
