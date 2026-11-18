#!/usr/bin/env node
// 探针：探测搜索列表页 note-item 是否含时间，以及详情页时间字段格式，决定补采方案
import fs from "node:fs";
for (const k of ["HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy","NO_PROXY"]) delete process.env[k];
const CDP_PORT = 9222, CDP_HOST = "127.0.0.1";
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
  const data = JSON.parse(fs.readFileSync("all_notes_cli.json", "utf-8"));
  const kw = data[0].kw;
  console.log("[探针] 用关键词:", kw, "| 样本笔记数:", data.length);

  // 1) 列表页探测
  const url = `https://www.xiaohongshu.com/search_result?keyword=${encodeURIComponent(kw)}`;
  const t = await getTarget(url);
  const s = new CDPSession(t.webSocketDebuggerUrl); await s.ready;
  await s.send("Page.enable"); await s.send("Runtime.enable");
  const load = s.once("Page.loadEventFired");
  await s.send("Page.navigate", { url });
  await Promise.race([load, sleep(20000)]);
  await sleep(10000);
  for (let i = 0; i < 8; i++) { await ev(s, `if(document.body)window.scrollTo(0,document.body.scrollHeight)`); await sleep(2000); }
  const listInfo = await ev(s, `(()=>{
    const item=document.querySelector('section.note-item');
    if(!item) return {err:'no item'};
    const timeEls=Array.from(document.querySelectorAll('[class*="time"],[class*="date"],[class*="Time"],[class*="Date"]')).slice(0,12).map(e=>({cls:String(e.className).slice(0,50),txt:e.innerText.trim().slice(0,40)}));
    return {firstItemText:item.innerText.slice(0,600), timeEls};
  })()`);
  console.log("\n=== 列表页 note-item 探测 ===");
  console.log(JSON.stringify(listInfo, null, 2));
  s.close();

  // 2) 详情页探测（取第一条 note 的 tokenUrl）
  const first = data[0].tokenUrl;
  const u = new URL(first);
  const noteId = u.pathname.split('/').pop();
  const token = u.searchParams.get('xsec_token');
  const exploreUrl = `https://www.xiaohongshu.com/explore/${noteId}?xsec_token=${encodeURIComponent(token)}&xsec_source=pc_search`;
  const t2 = await getTarget(exploreUrl);
  const s2 = new CDPSession(t2.webSocketDebuggerUrl); await s2.ready;
  await s2.send("Page.enable"); await s2.send("Runtime.enable");
  const load2 = s2.once("Page.loadEventFired");
  await s2.send("Page.navigate", { url: exploreUrl });
  await Promise.race([load2, sleep(20000)]);
  await sleep(8000);
  const detailInfo = await ev(s2, `(()=>{
    const dateEls=Array.from(document.querySelectorAll('[class*="date"],[class*="Date"],[class*="time"],[class*="Time"],[class*="publish"],[class*="Publish"]')).slice(0,12).map(e=>({cls:String(e.className).slice(0,50),txt:e.innerText.trim().slice(0,40)}));
    let initTime=null, initTimes=[];
    try{ const html=document.documentElement.innerHTML;
      const re=/"time":(\d{13})/g; let m; while((m=re.exec(html))){ initTimes.push(m[1]); }
      initTime = initTimes[0]||null;
    }catch(e){}
    return {dateEls, initTimeSample:initTime, initTimeCount:initTimes.length};
  })()`);
  console.log("\n=== 详情页时间探测 ===");
  console.log(JSON.stringify(detailInfo, null, 2));
  s2.close();
})().catch(e => { console.error("[失败]", e.message); process.exit(1); });
