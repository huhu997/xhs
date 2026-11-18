#!/usr/bin/env node
// 方向① 增强版采集：延长 SPA 等待 + 单关键词容错 + null 保护（游客态即可搜到笔记）
import fs from "node:fs";
const CDP_PORT = process.env.CDP_PORT || 9222;
const CDP_HOST = process.env.CDP_HOST || "127.0.0.1";
const KWS = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function cdpJson(p, m = "GET") { const r = await fetch(`http://${CDP_HOST}:${CDP_PORT}${p}`, { method: m }); if (!r.ok) throw new Error(`CDP ${p} ${r.status}`); return r.json(); }
async function getTarget(url) { let t = (await cdpJson("/json/list")).find(t => t.type === "page" && t.url.includes("xiaohongshu.com")); if (!t) t = await cdpJson(`/json/new?${new URLSearchParams({ url })}`, "PUT").catch(() => cdpJson(`/json/new?${new URLSearchParams({ url })}`, "GET")); return t; }
class CDPSession {
  constructor(url) { this.ws = new WebSocket(url); this.id = 0; this.pending = new Map(); this.listeners = new Map(); this.ready = new Promise((res, rej) => { this.ws.addEventListener("open", () => res()); this.ws.addEventListener("error", e => rej(new Error("WS " + e.message))); }); this.ws.addEventListener("message", n => { const e = JSON.parse(n.data); if (e.id && this.pending.has(e.id)) { const { resolve, reject } = this.pending.get(e.id); this.pending.delete(e.id); e.error ? reject(new Error(e.error.message)) : resolve(e.result); } else if (e.method) { const l = this.listeners.get(e.method); l && l.forEach(f => f(e.params)); } }); }
  send(m, p = {}) { return new Promise((res, rej) => { const id = ++this.id; this.pending.set(id, { resolve: res, reject: rej }); this.ws.send(JSON.stringify({ id, method: m, params: p })); }); }
  on(m, f) { this.listeners.has(m) || this.listeners.set(m, []); this.listeners.get(m).push(f); }
  once(m) { return new Promise(res => { const f = x => { this.off(m, f); res(x); }; this.on(m, f); }); }
  off(m, f) { const l = this.listeners.get(m); if (l) { const i = l.indexOf(f); i >= 0 && l.splice(i, 1); } }
  close() { this.ws.close(); }
}
async function ev(s, expr) { const r = await s.send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value; }

(async () => {
  const all = [];
  for (const kw of KWS) {
    try {
      const url = `https://www.xiaohongshu.com/search_result?keyword=${encodeURIComponent(kw)}`;
      const t = await getTarget(url);
      const s = new CDPSession(t.webSocketDebuggerUrl); await s.ready;
      await s.send("Page.enable"); await s.send("Runtime.enable");
      const load = s.once("Page.loadEventFired");
      await s.send("Page.navigate", { url });
      await Promise.race([load, sleep(20000)]);
      await sleep(10000); // 等 SPA 渲染
      for (let i = 0; i < 12; i++) { await ev(s, `if(document.body){window.scrollTo(0, document.body.scrollHeight)}`); await sleep(2000); }
      await sleep(2000);
      const notes = await ev(s, `(()=>{ const items = Array.from(document.querySelectorAll('section.note-item')); const out=[]; for(const el of items){ const id=el.getAttribute('data-note-id'); if(!id) continue; const title=(el.querySelector('.title')?.innerText||'').trim(); const author=(el.querySelector('.author .name')?.innerText||'').trim(); const liked=(el.querySelector('.like-wrapper .count')?.innerText||'').trim(); const a=el.querySelector('a.cover')||el.querySelector('a.title'); const href=a?a.getAttribute('href'):''; const abs=href&&href.startsWith('/')?'https://www.xiaohongshu.com'+href:href; out.push({noteId:id,title,author,liked,tokenUrl:abs}); } return out; })()`);
      notes.forEach(n => all.push({ kw, ...n }));
      s.close();
      console.log(`[${kw}] 提取 ${notes.length} 条`);
    } catch (e) { console.log(`[${kw}] 失败: ${e.message}`); }
  }
  const seen = new Set(); const dedup = all.filter(n => { if (seen.has(n.noteId)) return false; seen.add(n.noteId); return true; });
  fs.writeFileSync("all_notes_cli.json", JSON.stringify(dedup, null, 2), "utf-8");
  console.log(`\n共 ${dedup.length} 条（去重）| 已存 all_notes_cli.json`);
})().catch(e => { console.error("[失败]", e.message); process.exit(1); });
