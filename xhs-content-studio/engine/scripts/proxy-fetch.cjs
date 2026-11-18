// proxy-fetch.cjs
// 给 Node 的 globalThis.fetch 补上 HTTP 代理支持（Node 22 的 fetch 不认 HTTP_PROXY）。
// 用 https-proxy-agent 走 CONNECT 隧道；本机地址（127.0.0.1/localhost）强制直连。
// 只实现脚本实际用到的子集：status / ok / statusText / headers.get() / text() / json() / arrayBuffer()

const https = require('node:https');
const http = require('node:http');
const { URL } = require('node:url');
const agentMod = require('https-proxy-agent');
const HttpsProxyAgent = agentMod.HttpsProxyAgent || agentMod;

const PROXY =
  (process.env.GEMINI_WEB_PROXY || '').trim() ||
  (process.env.HTTPS_PROXY || '').trim() ||
  (process.env.HTTP_PROXY || '').trim() ||
  (process.env.https_proxy || '').trim() ||
  (process.env.http_proxy || '').trim();

const proxyAgent = PROXY ? new HttpsProxyAgent(PROXY) : undefined;

function isLocalHost(host) {
  if (!host) return true;
  const h = host.toLowerCase();
  return h === 'localhost' || h === '127.0.0.1' || h === '::1' || h === '[::1]' || h.endsWith('.local');
}

function doRequest(urlStr, init, redirectsLeft) {
  return new Promise((resolve, reject) => {
    let u;
    try {
      u = new URL(urlStr);
    } catch (e) {
      return reject(e);
    }
    const isHttps = u.protocol === 'https:';
    const lib = isHttps ? https : http;
    const local = isLocalHost(u.hostname);

    const headers = {};
    const srcHeaders = init.headers || {};
    for (const k of Object.keys(srcHeaders)) {
      const v = srcHeaders[k];
      if (v !== undefined && v !== null) headers[k] = v;
    }
    if (!Object.keys(headers).some((k) => k.toLowerCase() === 'host')) {
      headers['Host'] = u.host;
    }

    const opts = {
      hostname: u.hostname,
      port: u.port || (isHttps ? 443 : 80),
      path: (u.pathname || '/') + (u.search || ''),
      method: (init.method || 'GET').toUpperCase(),
      headers,
      agent: local ? undefined : proxyAgent,
      maxHeaderSize: 512 * 1024,
    };

    const req = lib.request(opts, (res) => {
      const status = res.statusCode || 0;
      const loc = res.headers.location;
      const redirectable = [301, 302, 303, 307, 308].includes(status);
      if (loc && redirectable && redirectsLeft > 0) {
        res.resume();
        let nextUrl;
        try {
          nextUrl = new URL(loc, u).toString();
        } catch (e) {
          return reject(e);
        }
        const nextInit = { ...init };
        if (status === 303 || ((status === 301 || status === 302) && opts.method === 'POST')) {
          nextInit.method = 'GET';
          delete nextInit.body;
        }
        return resolve(doRequest(nextUrl, nextInit, redirectsLeft - 1));
      }

      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const buf = Buffer.concat(chunks);
        const resp = {
          status,
          ok: status >= 200 && status < 300,
          statusText: res.statusMessage || '',
          url: urlStr,
          redirected: false,
          headers: {
            get(name) {
              const k = String(name).toLowerCase();
              const v = res.headers[k];
              if (v === undefined) return null;
              return Array.isArray(v) ? v.join(', ') : String(v);
            },
            has(name) {
              return res.headers[String(name).toLowerCase()] !== undefined;
            },
            forEach(cb) {
              for (const k of Object.keys(res.headers)) cb(res.headers[k], k);
            },
            raw() {
              return res.headers;
            },
          },
          text: async () => buf.toString('utf8'),
          json: async () => JSON.parse(buf.toString('utf8')),
          arrayBuffer: async () => buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength),
          body: null,
          clone() {
            return resp;
          },
        };
        resolve(resp);
      });
    });

    req.on('error', reject);

    if (init.signal) {
      if (init.signal.aborted) {
        req.destroy(new Error('Request aborted'));
      } else {
        init.signal.addEventListener('abort', () => req.destroy(new Error('Request aborted')));
      }
    }

    const body = init.body;
    if (body !== undefined && body !== null) {
      if (typeof body === 'string' || Buffer.isBuffer(body)) {
        req.write(body);
      } else if (typeof body.pipe === 'function') {
        body.pipe(req);
        return;
      } else {
        req.write(String(body));
      }
    }
    req.end();
  });
}

const origFetch = globalThis.fetch;

globalThis.fetch = async function proxyFetch(url, init) {
  const urlStr =
    typeof url === 'string'
      ? url
      : url && typeof url === 'object' && 'url' in url
        ? String(url.url)
        : String(url);
  return doRequest(urlStr, init || {}, 5);
};

// 便于排查
if (process.env.PROXY_FETCH_DEBUG) {
  console.error('[proxy-fetch] installed, proxy =', PROXY || '(none)', 'origFetch =', typeof origFetch);
}
