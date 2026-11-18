#!/usr/bin/env bun
/**
 * gemini-gen.mjs — Gemini 图片/文本生成脚本
 *
 * 从 baoyu-danger-gemini-web 提取的核心机制：
 * 1. Cookie 文件缓存 —— 登录一次，后续免浏览器
 * 2. 自动 Cookie 轮换 —— __Secure-1PSIDTS 永不过期
 * 3. 直接调 Gemini 内部 API（StreamGenerate 端点）
 * 4. Opera CDP 取 Cookie（绕过 DevToolsActivePort 问题）
 *
 * 使用:
 *   bun gemini-gen.mjs --login                  从 Opera 获取 Cookie 并缓存
 *   bun gemini-gen.mjs -p "prompt" -i out.png    生成图片
 *   bun gemini-gen.mjs -f prompt.txt -i out.png  从文件读 prompt
 *   bun gemini-gen.mjs --rotate                 手动轮换 Cookie
 *   bun gemini-gen.mjs --status                 查看缓存状态
 *
 * 环境变量:
 *   OPERA_CDP_PORT     Opera 调试端口（默认 9222）
 *   GEMINI_COOKIE_PATH Cookie 缓存路径
 *   HTTPS_PROXY        代理
 */

// @ts-nocheck
import fs from 'node:fs';
import path from 'node:path';

// ═══════════════════════════════════════════════════════════
//  常量
// ═══════════════════════════════════════════════════════════

const API = {
  // Google 首页（拿 NID cookie）
  GOOGLE: 'https://www.google.com',
  // Gemini 主页（拿 SNlM0e token）
  INIT: 'https://gemini.google.com/app',
  // 核心生成端点（逆向工程）
  GENERATE:
    'https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate',
  // Cookie 轮换端点
  ROTATE_COOKIES: 'https://accounts.google.com/RotateCookies',
};

// Gemini 3.0 Pro 模型头（从 baoyu-danger-gemini-web 抄来）
const MODEL_HEADER = {
  'x-goog-ext-525001261-jspb':
    '[1,null,null,null,"9d8ca3786ebdfbea",null,null,0,[4],null,null,1]',
};

const REQ_HEADERS = {
  'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
  Host: 'gemini.google.com',
  Origin: 'https://gemini.google.com',
  Referer: 'https://gemini.google.com/',
  'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  'X-Same-Domain': '1',
};

// Cookie 缓存路径（和 baoyu-danger-gemini-web 共享位置，方便互用）
const COOKIE_PATH = path.resolve(
  process.env.GEMINI_COOKIE_PATH ||
    path.join(
      process.env.APPDATA ||
        path.join(process.env.HOME || 'C:\\Users\\Default', 'AppData', 'Roaming'),
      'baoyu-skills',
      'gemini-web',
      'cookies.json',
    ),
);
const CACHE_DIR = path.dirname(COOKIE_PATH);

// Opera CDP 端口
const OPERA_CDP_PORT = parseInt(process.env.OPERA_CDP_PORT || '9222', 10);

// Linsoc 代理客户端路径（自动启动用）
const LINSOC_PATH = 'C:\\Users\\admin\\AppData\\Roaming\\Linsoc\\1.9.6.6\\Linsoc\\Linsoc.exe';

// ═══════════════════════════════════════════════════════════
//  工具函数
// ═══════════════════════════════════════════════════════════

/** 带超时的 fetch */
async function fetchWithTimeout(url, options = {}, timeoutMs = 30000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}

/**
 * 检测端口是否已开放（快速 TCP 连接测试）
 */
async function isPortOpen(port, timeoutMs = 500) {
  try {
    await Bun.connect({
      hostname: '127.0.0.1',
      port,
      socket: { data() {}, drain() {}, close() {}, error() {} },
      timeout: timeoutMs,
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * 等待端口开放（带超时和轮询）
 */
async function waitForPort(port, timeoutMs = 30000, intervalMs = 1000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await isPortOpen(port)) return true;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return false;
}

/**
 * 自动检测并设置代理
 *
 * 1. 检测常见代理端口（1080: v2ray/Linsoc, 7890/7891: Clash）
 * 2. 如果没找到，自动启动 Linsoc
 * 3. 找到后自动设置 HTTPS_PROXY / HTTP_PROXY
 */
async function detectAndSetProxy() {
  // 用户已显式设置 → 不覆盖
  if (process.env.HTTPS_PROXY || process.env.HTTP_PROXY) return;

  // ── 先检测是否已有代理在运行 ──
  const commonPorts = [
    { port: 1080, desc: 'Linsoc/v2ray' },
    { port: 7890, desc: 'Clash' },
    { port: 7891, desc: 'Clash 备用' },
  ];

  for (const { port, desc } of commonPorts) {
    if (await isPortOpen(port)) {
      const proxyUrl = `http://127.0.0.1:${port}`;
      process.env.HTTPS_PROXY = proxyUrl;
      process.env.HTTP_PROXY = proxyUrl;
      console.log(`  · 检测到代理 [${desc}]: ${proxyUrl}`);
      return;
    }
  }

  // ── 没检测到 → 尝试启动 Linsoc ──
  if (fs.existsSync(LINSOC_PATH)) {
    console.log('  · 未检测到运行中的代理，正在启动 Linsoc...');
    try {
      Bun.spawn([LINSOC_PATH], {
        detached: true,
        stdio: 'ignore',
        windowsHide: false,
        env: { ...process.env },
      });

      console.log('  · 等待 Linsoc 连接 (端口 1080)...');
      const ready = await waitForPort(1080, 30000, 1500);

      if (ready) {
        const proxyUrl = 'http://127.0.0.1:1080';
        process.env.HTTPS_PROXY = proxyUrl;
        process.env.HTTP_PROXY = proxyUrl;
        console.log(`  ✓ Linsoc 已就绪，代理: ${proxyUrl}`);
        console.log('  💡 如需切换节点，点击系统托盘 Linsoc 图标选择"新加坡代理1"');
      } else {
        console.log('  ⚠ Linsoc 已启动但等待超时，请检查系统托盘图标是否已连接');
        console.log('  · 连接后手动选择"新加坡代理1"节点');
      }
    } catch (e) {
      console.log('  ⚠ Linsoc 启动失败: ' + e.message);
      console.log('  · 请手动打开 Linsoc，选"新加坡代理1"节点');
    }
  } else {
    console.log('  · Linsoc 未安装（找不到: ' + LINSOC_PATH + '）');
    console.log('  · 请手动打开梯子客户端');
  }
}

/** Cookie 对象 → Cookie 头字符串 */
function toCookieHeader(cookies) {
  return Object.entries(cookies)
    .filter(([, v]) => typeof v === 'string' && v.length > 0)
    .map(([k, v]) => `${k}=${v}`)
    .join('; ');
}

/** 从 Set-Cookie 头提取指定 cookie 的值 */
function extractCookieValue(setCookie, name) {
  if (!setCookie) return null;
  const re = new RegExp(`(?:^|[;,\\s])${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}=([^;]+)`, 'i');
  const m = setCookie.match(re);
  return m ? m[1] : null;
}

// ═══════════════════════════════════════════════════════════
//  Cookie 文件操作
// ═══════════════════════════════════════════════════════════

/** 从缓存文件读取 Cookie */
function readCookieFile() {
  try {
    if (!fs.existsSync(COOKIE_PATH)) return null;
    const raw = fs.readFileSync(COOKIE_PATH, 'utf8');
    const data = JSON.parse(raw);

    // 支持两种格式
    if (data?.cookieMap) return { ...data.cookieMap };
    if (data?.cookies) return { ...data.cookies };

    // 扁平结构兜底
    const out = {};
    for (const [k, v] of Object.entries(data)) {
      if (typeof v === 'string') out[k] = v;
    }
    return Object.keys(out).length > 0 ? out : null;
  } catch {
    return null;
  }
}

/** 写入 Cookie 缓存文件 */
function writeCookieFile(cookies, source = 'unknown') {
  fs.mkdirSync(CACHE_DIR, { recursive: true });
  const payload = {
    version: 1,
    updatedAt: new Date().toISOString(),
    cookieMap: { ...cookies },
    source,
  };
  fs.writeFileSync(COOKIE_PATH, JSON.stringify(payload, null, 2), 'utf8');
  console.log(`  ✓ Cookie 已缓存: ${COOKIE_PATH}`);
}

/** 读取缓存的 __Secure-1PSIDTS */
function readCachedSidts(sid) {
  const p = path.join(CACHE_DIR, `.cached_1psidts_${sid}.txt`);
  try {
    if (!fs.existsSync(p)) return null;
    return fs.readFileSync(p, 'utf8').trim() || null;
  } catch {
    return null;
  }
}

/** 写入缓存的 __Secure-1PSIDTS */
function writeCachedSidts(sid, sidts) {
  const p = path.join(CACHE_DIR, `.cached_1psidts_${sid}.txt`);
  fs.mkdirSync(CACHE_DIR, { recursive: true });
  fs.writeFileSync(p, sidts, 'utf8');
}

// ═══════════════════════════════════════════════════════════
//  Opera CDP 取 Cookie（绕过 DevToolsActivePort）
// ═══════════════════════════════════════════════════════════

/**
 * 通过 Chrome DevTools Protocol 从 Opera 获取 Cookie
 *
 * 不走 DevToolsActivePort 文件，直接连 HTTP 端点拿 WebSocket URL，
 * 然后通过 WebSocket 发 CDP 命令。Opera 同样支持标准 CDP。
 */
async function fetchCookiesFromOpera() {
  // ── 1. 发现 WebSocket URL ──
  let wsUrl;
  try {
    const res = await fetchWithTimeout(
      `http://127.0.0.1:${OPERA_CDP_PORT}/json/version`,
      {},
      5000,
    );
    const info = await res.json();
    wsUrl = info.webSocketDebuggerUrl;
    if (!wsUrl) throw new Error('webSocketDebuggerUrl 为空');
  } catch (e) {
    throw new Error(
      `无法连接 Opera CDP (127.0.0.1:${OPERA_CDP_PORT})。\n` +
        `  请确保 Opera 已启动: "F:/Programs 应用程序/O浏览器/opera.exe" --remote-debugging-port=${OPERA_CDP_PORT}\n` +
        `  详情: ${e.message}`,
    );
  }

  // ── 2. WebSocket 连接 ──
  const ws = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      ws.close();
      reject(new Error('WebSocket 连接超时'));
    }, 10000);
    ws.onopen = () => {
      clearTimeout(timer);
      resolve();
    };
    ws.onerror = () => {
      clearTimeout(timer);
      reject(new Error('WebSocket 连接失败'));
    };
  });

  // ── 3. CDP 消息收发 ──
  let msgId = 0;
  const pending = new Map();

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      const handler = pending.get(msg.id);
      if (handler) {
        pending.delete(msg.id);
        handler.resolve(msg);
      }
    } catch {}
  };

  ws.onerror = () => {};
  ws.onclose = () => {
    for (const [, h] of pending) h.reject(new Error('WebSocket 已关闭'));
    pending.clear();
  };

  const cdpSend = (method, params = {}, sessionId) => {
    const id = ++msgId;
    const msg = { id, method, params };
    if (sessionId) msg.sessionId = sessionId;
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      try {
        ws.send(JSON.stringify(msg));
      } catch (e) {
        pending.delete(id);
        reject(e);
      }
      setTimeout(() => {
        if (pending.has(id)) {
          pending.delete(id);
          reject(new Error(`CDP 命令超时: ${method}`));
        }
      }, 30000);
    });
  };

  try {
    // ── 4. 找已有 Gemini 页面或新建一个 ──
    const targets = await cdpSend('Target.getTargets');
    let target = targets.result.targetInfos.find(
      (t) => t.type === 'page' && t.url.includes('gemini.google.com'),
    );

    if (!target) {
      const created = await cdpSend('Target.createTarget', {
        url: 'https://gemini.google.com/app',
      });
      target = { targetId: created.result.targetId };
      // 等页面加载
      await new Promise((r) => setTimeout(r, 3000));
    }

    // ── 5. 附加到页面拿 session ──
    const attached = await cdpSend('Target.attachToTarget', {
      targetId: target.targetId,
      flatten: true,
    });
    const sessionId = attached.result.sessionId;

    // ── 6. 启用 Network 域 ──
    await cdpSend('Network.enable', {}, sessionId);

    // ── 7. 获取 Cookie ──
    const result = await cdpSend(
      'Network.getCookies',
      {
        urls: [
          'https://gemini.google.com/',
          'https://accounts.google.com/',
          'https://www.google.com/',
        ],
      },
      sessionId,
    );

    // ── 8. 提取关键 Cookie ──
    const cookieMap = {};
    for (const c of result.result.cookies) {
      if (
        ['__Secure-1PSID', '__Secure-1PSIDTS', 'NID'].includes(c.name) &&
        c.value
      ) {
        cookieMap[c.name] = c.value;
      }
    }

    // 关闭新建的页面
    try {
      await cdpSend('Target.closeTarget', { targetId: target.targetId });
    } catch {}

    return cookieMap;
  } finally {
    ws.close();
  }
}

// ═══════════════════════════════════════════════════════════
//  补充 Cookie
// ═══════════════════════════════════════════════════════════

/** 从 google.com 预检拿 NID */
async function fetchExtraCookies() {
  try {
    const res = await fetchWithTimeout(API.GOOGLE, {}, 15000);
    const sc = res.headers.get('set-cookie');
    const nid = extractCookieValue(sc, 'NID');
    return nid ? { NID: nid } : {};
  } catch {
    return {};
  }
}

// ═══════════════════════════════════════════════════════════
//  SNlM0e Token 获取
// ═══════════════════════════════════════════════════════════

/** 从 Gemini 页面提取 SNlM0e access token */
async function getAccessToken(cookies) {
  const res = await fetchWithTimeout(
    API.INIT,
    {
      headers: {
        ...REQ_HEADERS,
        Cookie: toCookieHeader(cookies),
      },
      redirect: 'follow',
    },
    30000,
  );

  if (!res.ok) throw new Error(`Init 失败: ${res.status} ${res.statusText}`);

  const html = await res.text();
  const m = html.match(/"SNlM0e":"(.*?)"/);
  if (!m) throw new Error('无法提取 SNlM0e token，Cookie 可能已过期');
  return m[1];
}

// ═══════════════════════════════════════════════════════════
//  Cookie 轮换（防过期）
// ═══════════════════════════════════════════════════════════

/**
 * 调 accounts.google.com/RotateCookies 刷新 __Secure-1PSIDTS
 * 每 60 秒限速一次
 */
async function rotateCookies(cookies) {
  const sid = cookies['__Secure-1PSID'];
  if (!sid) throw new Error('缺少 __Secure-1PSID，无法轮换');

  // 60 秒内不重复轮换
  const cachePath = path.join(CACHE_DIR, `.cached_1psidts_${sid}.txt`);
  try {
    const st = fs.statSync(cachePath);
    if (Date.now() - st.mtimeMs <= 60000) return null;
  } catch {}

  const res = await fetchWithTimeout(
    API.ROTATE_COOKIES,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Cookie: toCookieHeader(cookies),
      },
      body: '[000,"-0000000000000000000"]',
    },
    30000,
  );

  if (res.status === 401)
    throw new Error('Cookie 轮换失败 (401)，需重新 --login');
  if (!res.ok) throw new Error(`Cookie 轮换失败: ${res.status}`);

  const sc = res.headers.get('set-cookie');
  const newSidts = extractCookieValue(sc, '__Secure-1PSIDTS');
  if (newSidts) {
    writeCachedSidts(sid, newSidts);
    return newSidts;
  }
  return null;
}

// ═══════════════════════════════════════════════════════════
//  确保会话有效
// ═══════════════════════════════════════════════════════════

/**
 * 尝试取 token，若失败则自动轮换 Cookie 后重试一次
 */
async function ensureSession(cookies) {
  try {
    const token = await getAccessToken(cookies);
    return { token, cookies };
  } catch (err) {
    console.log(`  · Token 失效 (${err.message?.slice(0, 40)}…)，尝试轮换 Cookie...`);
    const newSidts = await rotateCookies(cookies);
    if (newSidts) {
      cookies['__Secure-1PSIDTS'] = newSidts;
      writeCookieFile(cookies, 'rotate');
      const token = await getAccessToken(cookies);
      return { token, cookies };
    }
    throw err;
  }
}

// ═══════════════════════════════════════════════════════════
//  Gemini API 调用
// ═══════════════════════════════════════════════════════════

/**
 * 调 StreamGenerate 端点
 *
 * f.req 格式（逆向自 baoyu-danger-gemini-web）:
 *   [null, JSON.stringify([["prompt"], null, null])]
 */
async function generateContent(prompt, token, cookies) {
  // ── 构造请求 ──
  const inner = JSON.stringify([[prompt], null, null]);
  const fReq = JSON.stringify([null, inner]);
  const body = new URLSearchParams({ at: token, 'f.req': fReq }).toString();

  const res = await fetchWithTimeout(
    API.GENERATE,
    {
      method: 'POST',
      headers: {
        ...REQ_HEADERS,
        ...MODEL_HEADER,
        Cookie: toCookieHeader(cookies),
      },
      body,
    },
    180000, // 3 分钟
  );

  if (res.status !== 200) {
    throw new Error(`API 返回 ${res.status} ${res.statusText}`);
  }

  const text = await res.text();
  return parseResponse(text);
}

// ═══════════════════════════════════════════════════════════
//  响应解析
// ═══════════════════════════════════════════════════════════

function parseResponse(rawText) {
  const result = { text: '', images: [] };

  // ── 全文搜 gg-dl 图片链接 ──
  // URL 出现在 JSON 中，被 " 或 \" 包围，也可能会被 ) 或 ] 或 空白 截断
  const ggdlRe = /https:\/\/lh3\.googleusercontent\.com\/gg-dl\/([a-zA-Z0-9_\/\-.@%=+]+)/g;
  let m;
  while ((m = ggdlRe.exec(rawText)) !== null) {
    const url = 'https://lh3.googleusercontent.com/gg-dl/' + m[1];
    if (!result.images.includes(url)) result.images.push(url);
  }

  // ── 取最后一个 JSON 块提取文本 ──
  let lastJson = null;
  for (const line of rawText.split('\n')) {
    const t = line.trim();
    if (!t) continue;
    try {
      lastJson = JSON.parse(t);
    } catch {}
  }

  if (lastJson) {
    let bodyJson = null;
    for (const part of lastJson) {
      if (!Array.isArray(part)) continue;
      try {
        const raw = part[2];
        if (typeof raw !== 'string') continue;
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed?.[4])) {
          bodyJson = parsed;
          break;
        }
      } catch {}
    }

    if (!bodyJson && lastJson?.[0]?.[5]?.[2]?.[0]?.[1]?.[0]) {
      const code = lastJson[0][5][2][0][1][0];
      if (code === 1037) throw new Error('使用量已达上限，请稍后或切换模型');
      if (code === 1060) throw new Error('IP 被临时封禁，请检查代理或稍后重试');
      if (code === 1050) throw new Error('模型与聊天历史不一致');
      if (code === 1052) throw new Error('模型不可用，请更新脚本');
    }

    if (bodyJson) {
      const candidates = bodyJson[4] || [];
      for (const cand of candidates) {
        if (!Array.isArray(cand)) continue;
        const txt = cand[1]?.[0];
        if (typeof txt === 'string' && !txt.startsWith('http://googleusercontent.com/card_content/')) {
          result.text = txt;
        }
      }
    }
  }

  return result;
}

// ═══════════════════════════════════════════════════════════
//  下载图片
// ═══════════════════════════════════════════════════════════

async function downloadImage(url, outputPath, cookies) {
  // 加 =s2048 拿原图（baoyu-danger-gemini-web 的 full_size 参数）
  const imgUrl = url + '=s2048';

  const headers = {
    'User-Agent': 'Mozilla/5.0',
    Accept: 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
    Referer: 'https://gemini.google.com/',
    Cookie: toCookieHeader(cookies),
  };

  // 手动跟跳转（googleusercontent 的 CDN 需要手动 redirect 才能拿到图片）
  let currentUrl = imgUrl;
  let res;

  for (let i = 0; i < 10; i++) {
    res = await fetchWithTimeout(
      currentUrl,
      { method: 'GET', headers, redirect: 'manual' },
      30000,
    );

    if (res.status >= 300 && res.status < 400) {
      const loc = res.headers.get('location');
      if (!loc) break;
      currentUrl = new URL(loc, currentUrl).toString();
      continue;
    }
    break;
  }

  if (!res || !res.ok) {
    const status = res ? res.status : 'no response';
    throw new Error(`下载图片失败: ${status}`);
  }

  const buf = Buffer.from(await res.arrayBuffer());
  const abs = path.resolve(outputPath);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, buf);
  return abs;
}

// ═══════════════════════════════════════════════════════════
//  CLI
// ═══════════════════════════════════════════════════════════

function printHelp() {
  console.log(`
gemini-gen — Gemini 图片生成工具
（基于 baoyu-danger-gemini-web 逆向工程核心机制）

用法:
  bun gemini-gen.mjs --login                    从 Opera 获取并缓存 Cookie
  bun gemini-gen.mjs -p "提示词" -i 输出.png     生成图片
  bun gemini-gen.mjs -f prompt.txt -i 输出.png   从文件读提示词
  bun gemini-gen.mjs --rotate                   手动轮换 Cookie
  bun gemini-gen.mjs --status                   查看缓存状态
  bun gemini-gen.mjs -h                         显示帮助

选项:
  -p, --prompt <文本>   提示词
  -f, --file <路径>     从文件读取提示词
  -i, --image <路径>    输出图片路径（默认: generated.png）
  --login              从 Opera 获取 Cookie 并缓存到文件
  --rotate             手动轮换 __Secure-1PSIDTS
  --status             查看 Cookie 缓存状态
  -h, --help           显示帮助

环境变量:
  OPERA_CDP_PORT       Opera 调试端口（默认 9222）
  GEMINI_COOKIE_PATH   Cookie 缓存文件路径
  HTTPS_PROXY          代理地址（如 http://127.0.0.1:1080）

	工作流:
	  第一次:  bun gemini-gen.mjs --login
	           → Opera 打开，登录 Gemini → Cookie 缓存到文件
	           → 关掉 Opera，后续不再需要浏览器
	  
	  之后每次: bun gemini-gen.mjs -p "提示词" -i 图片.png
	           → 自动检测/启动 Linsoc 梯子（新加坡代理1）
	           → 直接从缓存 Cookie 调 Gemini API，无需浏览器
	           → Cookie 过期自动轮换，无需手动干预
	`);
}

async function main() {
  const args = process.argv.slice(2);

  // 自动检测代理（在 --help/--status 等之前执行，确保日志顺序正确）
  // --help 和纯参数错误时不检测
  if (args.length > 0 && !args.includes('-h') && !args.includes('--help')) {
    await detectAndSetProxy();
  }

  if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
    printHelp();
    return;
  }

  // ── --login ──
  if (args.includes('--login')) {
    console.log('\n🔑 正在连接 Opera CDP (127.0.0.1:' + OPERA_CDP_PORT + ')...');
    const cookies = await fetchCookiesFromOpera();

    if (!cookies['__Secure-1PSID']) {
      throw new Error(
        '未获取到 __Secure-1PSID。\n' +
          '  请确保已在 Opera 中登录 https://gemini.google.com',
      );
    }

    console.log('  ✓ 已获取 __Secure-1PSID=' + cookies['__Secure-1PSID'].slice(0, 10) + '...');

    // 补充额外 Cookie
    const extra = await fetchExtraCookies();
    Object.assign(cookies, extra);

    // 缓存到文件
    writeCookieFile(cookies, 'opera-cdp');

    // 尝试验证
    try {
      const token = await getAccessToken(cookies);
      console.log('  ✓ Token 验证通过，会话有效');
    } catch (e) {
      console.log('  ⚠  Token 验证失败: ' + e.message);
      console.log('  · Cookie 已缓存，可能已过期。请确保 Opera 中的 Gemini 已登录。');
    }

    console.log('  ✓ 登录完成！现在可以关闭 Opera。\n');
    return;
  }

  // ── --rotate ──
  if (args.includes('--rotate')) {
    const cookies = readCookieFile();
    if (!cookies?.['__Secure-1PSID']) {
      throw new Error('没有缓存的 Cookie，请先执行 --login');
    }
    console.log('\n🔄 正在轮换 Cookie...');
    const newSidts = await rotateCookies(cookies);
    if (newSidts) {
      cookies['__Secure-1PSIDTS'] = newSidts;
      writeCookieFile(cookies, 'rotate');
      console.log('  ✓ Cookie 轮换成功\n');
    } else {
      console.log('  · Cookie 无需轮换\n');
    }
    return;
  }

  // ── --status ──
  if (args.includes('--status')) {
    const cookies = readCookieFile();
    if (!cookies) {
      console.log('\n📭 Cookie 缓存为空。请先执行 --login。\n');
      return;
    }
    console.log('\n📋 Cookie 缓存状态:');
    console.log('  文件: ' + COOKIE_PATH);
    console.log('  __Secure-1PSID:  ' + (cookies['__Secure-1PSID'] ? cookies['__Secure-1PSID'].slice(0, 10) + '...' : '❌'));
    console.log('  __Secure-1PSIDTS: ' + (cookies['__Secure-1PSIDTS'] ? cookies['__Secure-1PSIDTS'].slice(0, 10) + '...' : '❌'));
    console.log('  NID:             ' + (cookies.NID ? '✅' : '❌'));
    if (cookies['__Secure-1PSID']) {
      const c = readCachedSidts(cookies['__Secure-1PSID']);
      if (c) console.log('  缓存 1PSIDTS:    ' + c.slice(0, 10) + '...');
    }
    const proxy = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || '';
    console.log('  代理:            ' + (proxy ? proxy : '直连（如遇网络问题请开梯子）'));
    console.log('');
    return;
  }

  // ── 生图模式 ──
  let prompt = null;
  let promptFile = null;
  let outputImage = 'generated.png';

  for (let i = 0; i < args.length; i++) {
    if ((args[i] === '-p' || args[i] === '--prompt') && i + 1 < args.length) {
      prompt = args[++i];
    } else if ((args[i] === '-f' || args[i] === '--file') && i + 1 < args.length) {
      promptFile = args[++i];
    } else if ((args[i] === '-i' || args[i] === '--image') && i + 1 < args.length) {
      outputImage = args[++i];
    }
  }

  if (promptFile) {
    prompt = fs.readFileSync(path.resolve(promptFile), 'utf8').trim();
  }

  if (!prompt) {
    // 尝试 stdin
    try {
      const s = await Bun.stdin.text();
      if (s.trim()) prompt = s.trim();
    } catch {}
  }

  if (!prompt) {
    throw new Error('请提供提示词（-p 或 -f）');
  }

  // ── 准备 Cookie ──
  let cookies = readCookieFile();
  if (!cookies?.['__Secure-1PSID']) {
    console.log('\n🔑 没有缓存 Cookie，尝试连接 Opera...');
    cookies = await fetchCookiesFromOpera();
    const extra = await fetchExtraCookies();
    Object.assign(cookies, extra);
    writeCookieFile(cookies, 'opera-cdp');
  }

  // ── 确保会话有效 ──
  const { token, cookies: validCookies } = await ensureSession(cookies);
  cookies = validCookies;

  // ── 生图 ──
  const outputPath = path.resolve(outputImage);
  const promptShort = prompt.length > 50 ? prompt.slice(0, 50) + '...' : prompt;
  console.log('\n🎨 生成中: "' + promptShort + '"');
  console.log('  输出: ' + outputPath);

  const result = await generateContent(prompt, token, cookies);

  if (result.images.length === 0) {
    console.log('  ⚠  未返回图片，返回文本:');
    console.log('  ' + (result.text || '(空)').slice(0, 200));
    if (result.text) {
      const txtPath = outputPath.replace(/\.\w+$/, '.txt');
      fs.writeFileSync(txtPath, result.text, 'utf8');
      console.log('  · 文本已保存: ' + txtPath);
    }
    console.log('');
    return;
  }

  // 下载第一张
  console.log('  · 找到 ' + result.images.length + ' 张图片，下载第 1 张...');
  const saved = await downloadImage(result.images[0], outputPath, cookies);
  console.log('  ✓ 已保存: ' + saved);

  // 其余图片
  if (result.images.length > 1) {
    const base = outputPath.replace(/\.(\w+)$/, '');
    const ext = path.extname(outputPath);
    for (let i = 1; i < result.images.length; i++) {
      const p = base + '_' + (i + 1) + ext;
      await downloadImage(result.images[i], p, cookies);
      console.log('  ✓ 已保存: ' + p);
    }
  }

  if (result.text) {
    console.log('  · 文本: ' + result.text.slice(0, 100) + (result.text.length > 100 ? '...' : ''));
  }
  console.log('');
}

main().catch((e) => {
  console.error('\n✗ 错误: ' + e.message + '\n');
  process.exit(1);
});
