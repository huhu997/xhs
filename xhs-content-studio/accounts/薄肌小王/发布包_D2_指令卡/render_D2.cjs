/**
 * D2 五图渲染脚本（verified marketing-card-render 暖色 Apple 风）
 *
 * 防串图设计：显式 CARDS 映射表，每张 card 单独 goto 自己的 HTML、单独 screenshot 到自己的 PNG。
 * 绝不像 D1 的 render_local.cjs 那样用「主图 HTML 文件名」当所有输出的 base —— 那会导致
 * card4 的 JPG 实际渲成 card1。这里 html / png 一一写死，逐张独立。
 *
 * 用法（Git Bash）：
 *   unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
 *   node render_D2.cjs
 * 产物：当前目录下 5 张 2160×2880 PNG（1080×1440 视口 × deviceScaleFactor 2）
 * 再由 convert_D2.py 缩到 1080×1440 JPG(quality 92)。
 */
const { chromium } = require('C:/Users/admin/.workbuddy/binaries/node/workspace/node_modules/playwright-core');
const path = require('path');
const fs = require('fs');

const EXE = 'C:/Users/admin/.cache/puppeteer/chrome-headless-shell/win64-150.0.7871.24/chrome-headless-shell-win64/chrome-headless-shell.exe';
const DIR = __dirname;

// 每张图：HTML 源 → PNG 输出，一一对应，逐张独立
const CARDS = [
  { html: 'card1_封面.html',     png: 'card1_封面.png' },
  { html: 'card2_数据.html',     png: 'card2_数据.png' },
  { html: 'card3_六卡总览.html', png: 'card3_六卡总览.png' },
  { html: 'card4_用法拆解.html', png: 'card4_用法拆解.png' },
  { html: 'card5_钩子引导.html', png: 'card5_钩子引导.png' },
];

(async () => {
  const browser = await chromium.launch({
    executablePath: EXE,
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars']
  });
  for (const c of CARDS) {
    const htmlPath = path.join(DIR, c.html);
    if (!fs.existsSync(htmlPath)) throw new Error('缺少 HTML 源: ' + htmlPath);
    const page = await browser.newPage({
      viewport: { width: 1080, height: 1440, deviceScaleFactor: 2 }
    });
    await page.goto('file://' + htmlPath, { waitUntil: 'load' });
    await page.waitForTimeout(300);
    const out = path.join(DIR, c.png);
    await page.screenshot({ path: out }); // 每张只截自己的页面，输出到自己的文件名
    console.log(`[OK] ${c.html}  ->  ${c.png}`);
    await page.close();
  }
  await browser.close();
  console.log('DONE: 5 PNG rendered (2160x2880 each).');
})().catch(e => { console.error(e); process.exit(1); });
