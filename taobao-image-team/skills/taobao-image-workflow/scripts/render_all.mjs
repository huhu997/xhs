// taobao-image-workflow/render_all.mjs
// 用本机 Chrome(CDP) 渲染淘宝全套素材: 主图/白底图(fixed) + 导购图3x4(strip) + 详情图(detail切片)
// 用法: node render_all.mjs [目录]   (无参=当前目录; 目录可为订单输出根, 自动递归一层找 SKU)
// 产物: 各 SKU 目录的 *.png + 中间 _tmp_full/ + _slice_jobs.json + _render_manifest.json
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const ROOT = process.argv[2] ? path.resolve(process.argv[2]) : process.cwd();
const PORT = 9356;
const TMP = path.join(ROOT, '_tmp_full');
const MAX_SLICE_H = 2800;            // 详情图切片上限(1440宽, 比例<2)
const DETAIL_W = 750, DETAIL_DSF = 1.92;

// 1) Chrome 路径探测
const CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Users/admin/.cache/puppeteer/chrome-headless-shell/win64-153.0.8010.36/chrome-headless-shell-win64/chrome-headless-shell.exe',
  'C:/Users/admin/.cache/puppeteer/chrome-headless-shell/win64-150.0.7871.24/chrome-headless-shell-win64/chrome-headless-shell.exe'
];
const CHROME = CANDIDATES.find(c => fs.existsSync(c));
if (!CHROME) { console.error('未找到 Chrome, 请安装或在脚本顶部 CANDIDATES 增加路径'); process.exit(1); }
const IS_SHELL = CHROME.includes('chrome-headless-shell');
console.log('[chrome] ' + CHROME);

// 2) 递归(深度2)收集 html 并按目录分组为 SKU
function walk(dir, depth, out) {
  if (depth > 2) return;
  let ents;
  try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
  for (const e of ents) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, depth + 1, out);
    else if (e.name.endsWith('.html')) out.push(p);
  }
}
const htmls = [];
walk(ROOT, 0, htmls);
const byDir = new Map();
for (const h of htmls) {
  const dir = path.dirname(h);
  if (!byDir.has(dir)) byDir.set(dir, []);
  byDir.get(dir).push(h);
}

// 3) 构建 jobs
const jobs = [];
for (const [dir, files] of byDir) {
  const b = path.basename(dir);
  const nameOf = f => path.basename(f);
  for (const f of files.filter(f => nameOf(f).startsWith('主图_'))) {
    jobs.push({ kind: 'fixed', html: f, out: f.replace(/\.html$/, '.png'), w: 800, h: 800, dsf: 1.8, tag: b + '/' + nameOf(f) });
  }
  const wf = files.find(f => nameOf(f).startsWith('白底图_'));
  if (wf) jobs.push({ kind: 'fixed', html: wf, out: wf.replace(/\.html$/, '.png'), w: 800, h: 800, dsf: 1, tag: b + '/' + nameOf(wf) });
  const gf = files.find(f => nameOf(f).startsWith('导购图3x4_'));
  if (gf) {
    const gb = nameOf(gf).replace('导购图3x4_', '').replace(/\.html$/, '');
    jobs.push({ kind: 'strip', html: gf, outPrefix: path.join(dir, '导购图_' + gb + '_'), w: 720, h: 960, dsf: 2, count: 5, tag: b + '/' + nameOf(gf) });
  }
  for (const f of files.filter(f => nameOf(f).startsWith('详情图_'))) {
    const suffix = nameOf(f).slice(0, -5).replace('详情图_', '');
    jobs.push({ kind: 'detail', html: f, outPrefix: path.join(dir, '详情图_' + suffix + '_'), w: DETAIL_W, dsf: DETAIL_DSF, tag: b + '/' + nameOf(f) });
  }
}
if (!jobs.length) { console.error('没有找到可渲染的淘宝图 HTML(主图_/白底图_/导购图3x4_/详情图_)'); process.exit(1); }
console.log('[jobs] ' + jobs.length + ' 个页面, 来自 ' + byDir.size + ' 个 SKU 目录');

fs.mkdirSync(TMP, { recursive: true });

// 4) 启 Chrome CDP
const cargs = ['--remote-debugging-port=' + PORT, '--user-data-dir=' + path.join(TMP, 'profile'), '--no-first-run', '--disable-gpu', '--hide-scrollbars'];
if (!IS_SHELL) cargs.unshift('--headless=new');
cargs.push('about:blank');
const chrome = spawn(CHROME, cargs, { stdio: 'ignore', detached: true });
chrome.unref();

const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets = null;
for (let i = 0; i < 40; i++) {
  try { targets = await (await fetch('http://127.0.0.1:' + PORT + '/json/list')).json(); break; } catch { await sleep(400); }
}
if (!targets) { console.error('CDP 未就绪'); process.exit(1); }
const page = targets.find(t => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0; const pending = new Map();
const send = (method, params) => new Promise((resolve, reject) => {
  const mid = ++id; pending.set(mid, { resolve, reject });
  ws.send(JSON.stringify({ id: mid, method, params: params || {} }));
});
ws.onmessage = ev => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) { const p = pending.get(msg.id); pending.delete(msg.id); msg.error ? p.reject(new Error(msg.error.message)) : p.resolve(msg.result); }
};
await new Promise(r => { ws.onopen = r; });
await send('Page.enable');

const crops = [];
const manifest = [];
let problems = 0;

for (let ji = 0; ji < jobs.length; ji++) {
  const job = jobs[ji];
  const vh = job.h || 1000;
  await send('Emulation.setDeviceMetricsOverride', { width: job.w, height: vh, deviceScaleFactor: job.dsf, mobile: false });
  await send('Page.navigate', { url: pathToFileURL(job.html).href });
  await sleep(800);
  const expr = 'JSON.stringify({sw: document.documentElement.scrollWidth, sh: document.documentElement.scrollHeight,' +
    ' blocks: Array.from(document.body.children).map(function(e){var r=e.getBoundingClientRect();return {top:r.top+window.scrollY, bottom:r.bottom+window.scrollY};})})';
  const info = JSON.parse((await send('Runtime.evaluate', { expression: expr, returnByValue: true })).result.value);
  const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  const buf = Buffer.from(shot.data, 'base64');

  if (job.kind === 'fixed') {
    fs.writeFileSync(job.out, buf);
    const ew = Math.round(job.w * job.dsf), eh = Math.round(job.h * job.dsf);
    if (info.sw !== job.w || info.sh !== job.h) { problems++; console.log('!! 页面尺寸异常 ' + job.tag + ' css ' + info.sw + 'x' + info.sh); }
    manifest.push({ file: path.relative(ROOT, job.out), expect: ew + 'x' + eh, css: info.sw + 'x' + info.sh });
    console.log('[fixed] ' + job.tag + ' -> ' + path.basename(job.out) + '  ' + ew + 'x' + eh);
    continue;
  }

  const tmp = path.join(TMP, String(ji).padStart(2, '0') + '_' + path.basename(job.html).replace('.html', '.png'));
  fs.writeFileSync(tmp, buf);
  const deviceW = Math.round(job.w * job.dsf);

  if (job.kind === 'strip') {
    const pieceH = Math.round(job.h * job.dsf);
    const need = pieceH * job.count;
    if (Math.abs(info.sh * job.dsf - need) > 2) { problems++; console.log('!! 导购图总高异常 ' + job.tag + ' css高 ' + info.sh + ' 期望 ' + (need / job.dsf)); }
    for (let i = 0; i < job.count; i++) {
      crops.push({ src: tmp, out: job.outPrefix + String(i + 1) + '.png', x: 0, y: i * pieceH, w: deviceW, h: pieceH });
    }
    console.log('[strip] ' + job.tag + ' -> ' + job.count + ' 张 ' + deviceW + 'x' + pieceH);
    continue;
  }

  // detail: 按段落边界切片, 单张 <= MAX_SLICE_H
  const maxCss = MAX_SLICE_H / job.dsf;
  const bounds = [0];
  for (const bl of info.blocks) { const v = Math.round(bl.bottom); if (v > bounds[bounds.length - 1]) bounds.push(v); }
  const total = info.sh;
  if (bounds[bounds.length - 1] < total) bounds.push(total);
  const cuts = [0]; let start = 0;
  for (let i = 1; i < bounds.length; i++) {
    if (bounds[i] - start > maxCss) {
      const prev = bounds[i - 1];
      if (prev > start) { cuts.push(prev); start = prev; }
      while (bounds[i] - start > maxCss) { cuts.push(Math.round(start + maxCss)); start = Math.round(start + maxCss); }
    }
  }
  cuts.push(total);
  const uniq = cuts.filter((v, i, a) => i === 0 || v > a[i - 1]);
  for (let i = 0; i < uniq.length - 1; i++) {
    const y0 = Math.round(uniq[i] * job.dsf), y1 = Math.round(uniq[i + 1] * job.dsf);
    crops.push({ src: tmp, out: job.outPrefix + String(i + 1).padStart(2, '0') + '.png', x: 0, y: y0, w: deviceW, h: y1 - y0 });
  }
  console.log('[detail] ' + job.tag + ' -> ' + (uniq.length - 1) + ' 片, 全长 ' + info.sh + ' css / ' + Math.round(total * job.dsf) + ' px');
}

fs.writeFileSync(path.join(ROOT, '_slice_jobs.json'), JSON.stringify(crops, null, 1));
fs.writeFileSync(path.join(ROOT, '_render_manifest.json'), JSON.stringify({ root: ROOT, jobs: jobs.length, crops: crops.length, problems, manifest }, null, 1));
console.log('渲染完成: ' + jobs.length + ' 页面, 待切片 ' + crops.length + ' 张, 异常 ' + problems + ' 处');
try { await send('Browser.close'); } catch (e) {}
await sleep(300);
ws.close();
process.exit(0);
