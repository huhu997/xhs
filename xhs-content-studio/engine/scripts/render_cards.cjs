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
.row { background:#fff; border:1px solid #e2e2e8; border-radius:18px; padding:30px 34px; font-size:38px; line-height:1.4; box-shadow:0 2px 12px rgba(0,0,0,0.03); }
.row b { color:#0071e3; }
.warn { display:flex; flex-direction:column; gap:20px; }
.wrow { border-radius:18px; padding:32px 36px; font-size:35px; line-height:1.45; }
.wrow.bad { background:#fff0f0; border:1px solid #ffd0d0; color:#c0392b; }
.wrow.warn2 { background:#fff8e8; border:1px solid #ffe0a0; color:#9a6b00; }
.wrow.fix { background:#eaf6ff; border:1px solid #b6dcff; color:#0066cc; }
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
      <div class="tag">普通人副业 · 虚拟品 · 试水记录</div>
      <h1>用AI挖了100个<br>虚拟品选品方向</h1>
      <p class="sub">一单没卖，纯记录 🧾</p>
      <div class="hint">选品 + 合规自查，先活下来再放大 🌱</div>
    `, 1080)
  },
  {
    name: 'card2_为什么做', w: 1080, h: 1080,
    html: wrap(`
      <h2>为什么先挖数据？</h2>
      <div class="bigstat"><span class="num">100+</span><span class="label">用 AI 挖出的虚拟品选品方向</span></div>
      <div class="points">
        <div class="pt">🔍 先挖数据再动手（投研 + AI 练出来的）</div>
        <div class="pt">🧱 不侵权是底线</div>
        <div class="pt">🐢 一单没卖，先搞清楚坑在哪</div>
      </div>
      <div class="hint">副业先活下来，再谈放大</div>
    `, 1080)
  },
  {
    name: 'card3_选品清单', w: 1080, h: 1350,
    html: wrap(`
      <h2>挖到的选品方向<br>（不侵权版）</h2>
      <div class="list">
        <div class="row">🧪 <b>测试类</b>　心理 / 性格 / 职业倾向测试</div>
        <div class="row">📄 <b>模板类</b>　简历 / PPT / 计划表 / 知识库</div>
        <div class="row">🎨 <b>素材类</b>　商用字体 / 图标库 / 配色方案</div>
        <div class="row">📚 <b>教程类</b>　软件实操 / 上架 SOP / 运营笔记</div>
        <div class="row">📦 <b>资料类</b>　考试复习 / 行业报告合集</div>
      </div>
      <div class="hint">案例数据，非我亲身 · 资料类注意版权 · 上线前先问：敢不敢署真名卖</div>
    `, 1350)
  },
  {
    name: 'card4_三个避坑', w: 1080, h: 1350,
    html: wrap(`
      <h2>3个避坑<br>（别人踩过的坑）</h2>
      <div class="warn">
        <div class="wrow bad">🚫 <b>版权红线</b><br>教材 / 网课盗版 / 带 logo 素材，罚起来不手软</div>
        <div class="wrow warn2">⚠️ <b>类目选对</b><br>电子资源类目有门槛，先搞懂再上架</div>
        <div class="wrow fix">🔧 <b>新规应对</b><br>自荐被拒先查资质 + 保证金，别反复提交触发风控</div>
      </div>
    `, 1350)
  },
  {
    name: 'card5_钩子引导', w: 1080, h: 1080,
    html: wrap(`
      <h2>想要这份挖掘表？</h2>
      <div class="cta">扣【清单】<br>领选品方向 + 自查表</div>
      <p class="sub">我边研究边发，一起避坑，欢迎评论区交流踩坑</p>
      <div class="hint">先活下来再放大 🌱</div>
    `, 1080)
  },
];

(async () => {
  const out = './样稿_images';
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
