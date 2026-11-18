const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const EXE = 'C:/Users/admin/.cache/puppeteer/chrome-headless-shell/win64-150.0.7871.24/chrome-headless-shell-win64/chrome-headless-shell.exe';

const CSS = `
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family:"PingFang SC","Microsoft YaHei UI","Microsoft YaHei","Segoe UI Emoji","Segoe UI",sans-serif;
  background:linear-gradient(160deg,#fcfcfd 0%,#eaedf2 100%);
  color:#1d1d1f; -webkit-font-smoothing:antialiased;
}
.wrap { width:92%; max-width:960px; padding:54px; }
.tag { display:inline-block; background:#0071e3; color:#fff; font-size:30px; padding:10px 26px; border-radius:999px; margin-bottom:34px; font-weight:600; }
h1 { font-size:92px; line-height:1.16; font-weight:800; letter-spacing:-1.5px; }
h2 { font-size:66px; font-weight:800; letter-spacing:-0.5px; margin-bottom:42px; }
.sub { font-size:40px; color:#6e6e73; margin-top:26px; line-height:1.4; }
.hint { margin-top:46px; background:#fff; border:1px solid #e2e2e8; border-radius:18px; padding:28px 34px; font-size:33px; color:#1d1d1f; box-shadow:0 4px 20px rgba(0,0,0,0.04); line-height:1.4; }
.bigstat { background:#fff; border-radius:24px; padding:50px; text-align:center; box-shadow:0 4px 22px rgba(0,0,0,0.05); margin-bottom:36px; }
.bigstat .num { display:block; font-size:118px; font-weight:800; color:#0071e3; line-height:1; }
.bigstat .label { font-size:37px; color:#6e6e73; margin-top:18px; display:block; line-height:1.4; }
.points { display:flex; flex-direction:column; gap:20px; }
.pt { background:#fff; border:1px solid #e2e2e8; border-radius:18px; padding:28px 34px; font-size:40px; box-shadow:0 2px 12px rgba(0,0,0,0.03); }
.list { display:flex; flex-direction:column; gap:18px; }
.row { background:#fff; border:1px solid #e2e2e8; border-radius:18px; padding:30px 34px; font-size:38px; line-height:1.45; box-shadow:0 2px 12px rgba(0,0,0,0.03); }
.row b { color:#0071e3; }
.cta { background:#0071e3; color:#fff; border-radius:24px; padding:54px; text-align:center; font-size:60px; font-weight:800; line-height:1.25; box-shadow:0 8px 30px rgba(0,113,227,0.25); }
`;

function wrap(inner, h) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}</style></head>
  <body style="display:flex;align-items:center;justify-content:center;min-height:${h}px">
  <div class="wrap">${inner}</div></body></html>`;
}

const cards = [
  {
    name: 'card1_封面', w: 1080, h: 1080,
    html: wrap(`
      <div class="tag">信息整理 · AI 知识管理</div>
      <h1>别再无脑收藏了<br>信息整理我拆成模板</h1>
      <p class="sub">300 篇笔记挖出来的结论</p>
      <div class="hint">评论第一诉求是「模板」，不是「工具」</div>
    `, 1080)
  },
  {
    name: 'card2_反直觉', w: 1080, h: 1080,
    html: wrap(`
      <h2>一个反直觉的发现</h2>
      <div class="bigstat"><span class="num">141</span><span class="label">评论里求「模板 / 资料」的条数<br>（远超求教程 / 求工具）</span></div>
      <div class="points">
        <div class="pt">🔍 用户不要 100 个工具，要一个能抄的模板</div>
        <div class="pt">🧩 真正高赞的是「清单 / 搭建 / 降门槛」</div>
        <div class="pt">🛠️ 我据此做了个「四步整理模板」</div>
      </div>
      <div class="hint">工具永远在变，体系才留得下</div>
    `, 1080)
  },
  {
    name: 'card3_高赞三类', w: 1080, h: 1350,
    html: wrap(`
      <h2>真正高赞的 3 类<br>（数据实证）</h2>
      <div class="list">
        <div class="row">📋 <b>清单盘点类</b><br>「2026最好用AI工具分类表」1.1万赞</div>
        <div class="row">🏗️ <b>搭建教程类</b><br>「随手搭建个人知识库」1.1万赞</div>
        <div class="row">👤 <b>普通人降门槛</b><br>「普通人如何构建跨AI档案」6795赞</div>
      </div>
      <div class="hint">数据来自 300 篇笔记 + 上千评论挖掘，非我亲身编造</div>
    `, 1350)
  },
  {
    name: 'card4_四步模板', w: 1080, h: 1350,
    html: wrap(`
      <h2>我的「信息整理四步」</h2>
      <div class="list">
        <div class="row">① <b>输入</b>　先把碎片信息收口到一个入口</div>
        <div class="row">② <b>分类</b>　按「是否主线 / 是否复用」二分</div>
        <div class="row">③ <b>沉淀</b>　模板化，别每次重新想</div>
        <div class="row">④ <b>复用</b>　建检索，用的时候 10 秒调出</div>
      </div>
      <div class="hint">我试了两周，收藏夹终于不堆灰了（真实记录）</div>
    `, 1350)
  },
  {
    name: 'card5_钩子引导', w: 1080, h: 1080,
    html: wrap(`
      <h2>想要这个模板？</h2>
      <div class="cta">扣【模板】<br>领四步整理模板</div>
      <p class="sub">还放了几个我实测能跑的免费工具，不卖课</p>
      <div class="hint">先搭起自己的体系，比囤工具实在 🌱</div>
    `, 1080)
  },
];

(async () => {
  const out = './D1_images';
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars'] });
  for (const c of cards) {
    const page = await browser.newPage({ viewport: { width: c.w, height: c.h, deviceScaleFactor: 2 } });
    await page.setContent(c.html, { waitUntil: 'load' });
    await page.waitForTimeout(250);
    const p = path.join(out, c.name + '.png');
    await page.screenshot({ path: p });
    console.log('shot ->', p);
    await page.close();
  }
  await browser.close();
  console.log('DONE');
})().catch(e => { console.error(e); process.exit(1); });
