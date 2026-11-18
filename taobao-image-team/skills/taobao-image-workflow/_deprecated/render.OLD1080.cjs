const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const EXE = 'C:/Users/admin/.cache/puppeteer/chrome-headless-shell/win64-150.0.7871.24/chrome-headless-shell-win64/chrome-headless-shell.exe';

async function shot(htmlFile, w, h, out) {
  const browser = await chromium.launch({
    executablePath: EXE,
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars']
  });
  const page = await browser.newPage({
    viewport: { width: w, height: h, deviceScaleFactor: 2 }
  });
  await page.goto('file://' + path.resolve(htmlFile), { waitUntil: 'load' });
  await page.screenshot({ path: out });
  await browser.close();
  console.log('shot ->', out);
}

async function main() {
  const [mainHtml, detailHtml, outDir] = process.argv.slice(2);
  if (!mainHtml || !detailHtml || !outDir) {
    console.error('Usage: node render.cjs <main.html> <detail.html> <output-dir>');
    process.exit(1);
  }
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const mainBase = path.basename(mainHtml, path.extname(mainHtml)).replace(/_main$/, '');
  const detailBase = path.basename(detailHtml, path.extname(detailHtml)).replace(/_detail$/, '');
  await shot(mainHtml, 1080, 1080, path.join(outDir, `${mainBase}_主图.png`));
  await shot(detailHtml, 1080, 1440, path.join(outDir, `${detailBase}_详情图.png`));
}

main().catch(e => { console.error(e); process.exit(1); });
