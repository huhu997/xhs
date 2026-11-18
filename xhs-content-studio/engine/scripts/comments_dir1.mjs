#!/usr/bin/env node
// 方向① 批量评论抓取：抓 Top 笔记评论（游客态首屏高赞即可），延长 SPA 等待
import fs from "node:fs";
const CDP_PORT = process.env.CDP_PORT || 9222;
const CDP_HOST = process.env.CDP_HOST || "127.0.0.1";
const TOP_N = Number(process.argv[2] || 16);
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
const EXTRACT = `(()=>{
   const pick=(el,sels)=>{ for(const s of sels){ const e=el.querySelector(s); if(e&&e.innerText&&e.innerText.trim()) return e.innerText.trim(); } return ''; };
   const items = Array.from(document.querySelectorAll('.parent-comment, .comment-item-sub'));
   const out = [];
   for(const it of items){
     const right = it.querySelector('.right') || it;
     const nickname = pick(right, ['.author .name', '.author', '.name']);
     const content = pick(right, ['.content', '.note-text']);
     const liked = pick(right, ['.like-wrapper .count', '.count']);
     const ip = pick(right, ['.location', '.author .location']);
     const isSub = it.classList.contains('comment-item-sub') || !!it.closest('.reply-container');
     if(!content) continue;
     out.push({ nickname, content, liked, ip, isSub });
   }
   return out;
})()`;
(async () => {
  const top = JSON.parse(fs.readFileSync("top30_for_comments.json", "utf-8")).slice(0, TOP_N);
  const all = [];
  for (const n of top) {
    try {
      const u = new URL(n.tokenUrl);
      const noteId = u.pathname.split('/').pop();
      const token = u.searchParams.get('xsec_token');
      const exploreUrl = `https://www.xiaohongshu.com/explore/${noteId}?xsec_token=${encodeURIComponent(token)}&xsec_source=pc_search`;
      const t = await getTarget(exploreUrl);
      const s = new CDPSession(t.webSocketDebuggerUrl); await s.ready;
      await s.send("Page.enable"); await s.send("Runtime.enable");
      const load = s.once("Page.loadEventFired");
      await s.send("Page.navigate", { url: exploreUrl });
      await Promise.race([load, sleep(20000)]);
      await sleep(8000);
      for (let i = 0; i < 15; i++) {
        await ev(s, `(()=>{ const el=document.querySelector('.note-scroller')||document.querySelector('.comments-container'); if(el&&el.scrollTo){try{el.scrollTo(0,el.scrollHeight)}catch(e){}} if(document.body) window.scrollTo(0,document.body.scrollHeight); return el?el.scrollTop:0; })()`);
        await sleep(1200);
      }
      const comments = await ev(s, EXTRACT);
      const seen = new Set(); const dedup = comments.filter(c => { const k = c.nickname + "||" + c.content; if (seen.has(k)) return false; seen.add(k); return true; });
      dedup.forEach(c => all.push({ fromNote: n.noteId, noteKw: n.kw, noteTitle: n.title, noteLiked: n.liked, ...c }));
      s.close();
      console.log(`[${n.kw}] ${n.like}赞 抓到 ${dedup.length} 条评论`);
    } catch (e) { console.log(`[${n.noteId}] 失败: ${e.message}`); }
  }
  fs.writeFileSync("comments_dir1.json", JSON.stringify(all, null, 2), "utf-8");
  console.log(`\n共抓评论 ${all.length} 条 | 已存 comments_dir1.json`);
})().catch(e => { console.error("[失败]", e.message); process.exit(1); });
