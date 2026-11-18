#!/usr/bin/env node
// 方向① 补采发布时间：在 collect_tokens_v2 基础上，额外提取 note-item 的 .time 字段
// 只输出 noteId->pubTime 映射（pubtime_map.json）+ 完整带时间笔记（all_notes_with_time.json）
// 不破坏原 all_notes_cli.json 的赞数，后续合并回原数据
import fs from "node:fs";
for (const k of ["HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy","NO_PROXY"]) delete process.env[k];
const CDP_PORT = process.env.CDP_PORT || 9222;
const CDP_HOST = process.env.CDP_HOST || "127.0.0.1";
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
  const base = JSON.parse(fs.readFileSync("all_notes_cli.json", "utf-8"));
  const KWS = [...new Set(base.map(n => n.kw))];
  console.log("[采集] 去重关键词数:", KWS.length, "|", KWS.join(" / "));
  const map = {};      // noteId -> pubTime
  const fresh = [];    // 完整带时间笔记
  for (const kw of KWS) {
    try {
      const url = `https://www.xiaohongshu.com/search_result?keyword=${encodeURIComponent(kw)}`;
      const t = await getTarget(url);
      const s = new CDPSession(t.webSocketDebuggerUrl); await s.ready;
      await s.send("Page.enable"); await s.send("Runtime.enable");
      const load = s.once("Page.loadEventFired");
      await s.send("Page.navigate", { url });
      await Promise.race([load, sleep(20000)]);
      await sleep(10000);
      for (let i = 0; i < 12; i++) { await ev(s, `if(document.body)window.scrollTo(0,document.body.scrollHeight)`); await sleep(2000); }
      const notes = await ev(s, `(()=>{ const items=Array.from(document.querySelectorAll('section.note-item')); const out=[]; for(const el of items){ const id=el.getAttribute('data-note-id'); if(!id) continue; const title=(el.querySelector('.title')?.innerText||'').trim(); const author=(el.querySelector('.author .name')?.innerText||'').trim(); const liked=(el.querySelector('.like-wrapper .count')?.innerText||'').trim(); const pubTime=(el.querySelector('.time')?.innerText||'').trim(); const a=el.querySelector('a.cover')||el.querySelector('a.title'); const href=a?a.getAttribute('href'):''; const abs=href&&href.startsWith('/')?'https://www.xiaohongshu.com'+href:href; out.push({noteId:id,title,author,liked,pubTime,tokenUrl:abs}); } return out; })()`);
      for (const n of notes) { if (!map[n.noteId]) { map[n.noteId] = n.pubTime; fresh.push({ kw, ...n }); } }
      s.close();
      console.log(`[${kw}] 提取 ${notes.length} 条 | 累计 ${Object.keys(map).length}`);
    } catch (e) { console.log(`[${kw}] 失败: ${e.message}`); }
  }
  fs.writeFileSync("pubtime_map.json", JSON.stringify(map, null, 2), "utf-8");
  fs.writeFileSync("all_notes_with_time.json", JSON.stringify(fresh, null, 2), "utf-8");
  console.log(`\n共抓到 ${Object.keys(map).length} 个 noteId 发布时间 | 已存 pubtime_map.json / all_notes_with_time.json`);
})().catch(e => { console.error("[失败]", e.message); process.exit(1); });
