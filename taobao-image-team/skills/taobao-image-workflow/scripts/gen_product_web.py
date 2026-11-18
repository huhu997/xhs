#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""网页端生图 -> 自动落盘（无需 API key，无需手动选模型）。

设计：脚本层不绑定任何 AI 服务。用 Playwright 接管一个**持久化 profile 的浏览器**，
第一次在弹出的窗口里登录一次，之后登录态长期复用；脚本只负责
「贴 prompt -> 发送 -> 等生成 -> 抓图 -> 归一化落盘到 <out>/product_<sku>.png」。
落盘后重跑 fill_template.py 会自动拾取，无需改订单。

三档用法（从稳到自动）：
  A 手动档（零配置，最稳，任何网页生图工具都行）：
       自己在网页端生图 -> 保存图片 ->
       python scripts/gen_product.py order.json --save <图> --out <out>
  B 半自动档（本脚本，推荐自用）：
       python scripts/gen_product_web.py order.json --out <out> --probe   # 先探通道
       python scripts/gen_product_web.py order.json --out <out>           # 自动跑
  C 会话档：说「生一张」，由宿主生图工具出图后 --save 落盘。

参数:
  --url      网页生图入口，默认 Gemini 网页端；可换成任意国内网页生图工具
  --profile  持久化 profile 目录，默认 ~/.workbuddy/ecom-web-profile
  --proxy    显式给浏览器指定代理 server（如 http://127.0.0.1:7956），默认不指定
  --timeout  等待生成图片的秒数，默认 150
  --probe    只验证浏览器/CDP 通道并列出标签页，不生图（headless，不弹窗）
  --headless 无头模式（已登录过 profile 才可用；首次登录必须有头）

合规：Gemini 等境外工具名属硬违规词，只能出现在内部脚本/任务单，
      绝不可写进上架图、标题、详情文案。本脚本不会把任何工具名写进图片。
"""
import os

# 关键：env 里的代理常指向已失效的本地端口，会拖累 Playwright 连本地 CDP。
# 先清掉；确实需要代理的用户用 --proxy 显式传回。
for _k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
           'ALL_PROXY', 'all_proxy'):
    os.environ.pop(_k, None)
os.environ['NO_PROXY'] = '127.0.0.1,localhost'
os.environ['no_proxy'] = '127.0.0.1,localhost'

import argparse
import base64
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from gen_product import build_prompt, normalize

DEFAULT_URL = 'https://gemini.google.com/app'
DEFAULT_PROFILE = os.path.join(os.path.expanduser('~'), '.workbuddy', 'ecom-web-profile')

INPUT_SELECTORS = [
    'div[contenteditable="true"]',
    '[contenteditable="true"]',
    'textarea',
    '[role="textbox"]',
    '.ql-editor',
]
SEND_SELECTORS = [
    'button[aria-label*="Send"]', 'button[aria-label*="send"]',
    'button[aria-label*="发送"]', 'button[aria-label*="提交"]',
    'button[data-testid*="send"]', 'button[mattooltip*="Send"]',
]
DOWNLOAD_SELECTORS = [
    'button[aria-label*="Download"]', 'button[aria-label*="download"]',
    'button[aria-label*="下载"]', '[data-testid*="download"]',
    'a[download]',
]
LOGIN_HINTS = ('accounts.google.com', 'signin', 'login', '登录')


def log(msg):
    print(msg, flush=True)


def find_first(page, selectors, timeout=3000):
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=timeout, state='visible')
            if el:
                return el, sel
        except Exception:
            continue
    return None, None


def snapshot_images(page):
    try:
        return page.evaluate("""() => Array.from(document.images)
            .map((im, i) => ({i, src: (im.currentSrc || im.src || '').slice(0, 200),
                              w: im.naturalWidth, h: im.naturalHeight, alt: im.alt || ''}))""")
    except Exception:
        return []


def wait_new_image(page, baseline_keys, timeout):
    """轮询等待生成出的新大图出现，返回图片元素索引。"""
    deadline = time.time() + timeout
    last_tick = 0
    while time.time() < deadline:
        try:
            imgs = snapshot_images(page)
            cands = [x for x in imgs
                     if x['w'] >= 512 and x['h'] >= 512
                     and (x['src'], x['w'], x['h']) not in baseline_keys]
            if cands:
                return cands[-1]
        except Exception:
            pass
        if time.time() - last_tick >= 15:
            log(f'  ...等待生成中（已等 {int(timeout - (deadline - time.time()))}s）')
            last_tick = time.time()
        page.wait_for_timeout(1500)
    return None


def grab_by_download(page, tmp_path):
    for sel in DOWNLOAD_SELECTORS:
        try:
            btn = page.query_selector(sel)
            if not btn or not btn.is_visible():
                continue
            with page.expect_download(timeout=10000) as di:
                btn.click()
            dl = di.value
            dl.save_as(tmp_path)
            return tmp_path
        except Exception:
            continue
    return None


def grab_by_canvas(page, idx, tmp_path):
    """把页面 img 画到 canvas 取回 dataURL，绕过 blob URL 与跨域限制。"""
    try:
        data = page.evaluate("""(idx) => {
            const im = document.images[idx];
            if (!im || !im.naturalWidth) return null;
            const c = document.createElement('canvas');
            c.width = im.naturalWidth; c.height = im.naturalHeight;
            c.getContext('2d').drawImage(im, 0, 0);
            return c.toDataURL('image/png');
        }""", idx)
        if data and ',' in data:
            Path(tmp_path).write_bytes(base64.b64decode(data.split(',', 1)[1]))
            return tmp_path
    except Exception as e:
        log(f'  [warn] canvas 取图失败: {type(e).__name__}: {e}')
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('order')
    ap.add_argument('--out', default='.', help='与 fill_template.py --out 一致')
    ap.add_argument('--url', default=DEFAULT_URL)
    ap.add_argument('--profile', default=DEFAULT_PROFILE)
    ap.add_argument('--proxy', default=None, help='显式代理 server')
    ap.add_argument('--timeout', type=int, default=150)
    ap.add_argument('--probe', action='store_true')
    ap.add_argument('--headless', action='store_true')
    args = ap.parse_args()

    with open(args.order, encoding='utf-8') as f:
        d = json.load(f)
    sku = d.get('sku', 'SKU')
    prompt = build_prompt(d)
    dst = os.path.join(args.out, f'product_{sku}.png')
    os.makedirs(args.out, exist_ok=True)

    if not prompt and not args.probe:
        log('[error] 订单缺 product_prompt，无需生图（会出纯文案参数卡）')
        sys.exit(1)

    launch_kw = {}
    if args.proxy:
        launch_kw['proxy'] = {'server': args.proxy}
    launch_kw['viewport'] = {'width': 1440, 'height': 960}
    launch_kw['accept_downloads'] = True

    with sync_playwright() as pw:
        if args.probe:
            # 通道自检：headless + 临时 profile，不碰正式登录态、不弹窗
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                ctx = pw.chromium.launch_persistent_context(
                    td, headless=True, **launch_kw)
                pg = ctx.new_page()
                pg.goto('about:blank')
                log('[probe] Chromium 启动 OK；当前标签页:')
                for p in ctx.pages:
                    log(f'  - {p.url}')
                log(f'[probe] 正式 profile: {args.profile}  (存在={os.path.isdir(args.profile)})')
                log(f'[probe] 目标落盘路径: {dst}')
                ctx.close()
            log('[probe] 通道可用。去掉 --probe 即进入半自动生图。')
            return

        os.makedirs(args.profile, exist_ok=True)
        log(f'[1/5] 启动持久化浏览器  profile={args.profile}')
        ctx = pw.chromium.launch_persistent_context(
            args.profile, headless=args.headless, **launch_kw)

        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            log(f'[2/5] 打开 {args.url}')
            try:
                page.goto(args.url, wait_until='domcontentloaded', timeout=45000)
            except Exception as e:
                log(f'[error] 页面打不开: {type(e).__name__}: {e}')
                log('  网页可达性由你的网络/浏览器决定。可换 --url，或走手动档 A（最稳）。')
                sys.exit(3)

            # 首次登录等待：检测到登录页则提示，最多等 180s 让用户手动登录
            deadline = time.time() + 180
            while time.time() < deadline:
                u = (page.url or '').lower()
                if any(h in u for h in LOGIN_HINTS):
                    if time.time() - (deadline - 180) < 5:
                        log('[!] 检测到未登录：请在弹出的浏览器窗口里登录一次，'
                            '登录态会存进 profile，以后不用再登。脚本自动等待...')
                    page.wait_for_timeout(2000)
                    continue
                break

            baseline = snapshot_images(page)
            base_keys = {(x['src'], x['w'], x['h']) for x in baseline}

            log('[3/5] 定位输入框并发送 prompt')
            inp, sel = find_first(page, INPUT_SELECTORS, timeout=12000)
            if not inp:
                log('[error] 没找到输入框（网页 DOM 可能改版）。')
                log('  兜底：手动在网页里贴 prompt 生图 -> 保存图片 -> '
                    f'python scripts/gen_product.py {args.order} --save <图> --out {args.out}')
                sys.exit(4)
            log(f'  输入框命中: {sel}')
            try:
                inp.click()
                inp.fill(prompt)
            except Exception:
                page.keyboard.insert_text(prompt)
            page.wait_for_timeout(600)

            sent = False
            btn, bsel = find_first(page, SEND_SELECTORS, timeout=1500)
            if btn and btn.is_enabled():
                btn.click()
                sent = True
                log(f'  发送按钮命中: {bsel}')
            if not sent:
                page.keyboard.press('Enter')
                log('  用 Enter 发送')

            log(f'[4/5] 等待生成（最多 {args.timeout}s）')
            cand = wait_new_image(page, base_keys, args.timeout)
            if not cand:
                log('[warn] 超时未捕获到新生成的大图（可能未登录/额度限制/网页改版）。')
                log('  兜底：手动保存图片后执行 '
                    f'python scripts/gen_product.py {args.order} --save <图> --out {args.out}')
                sys.exit(5)
            log(f"  捕获图片: idx={cand['i']} {cand['w']}x{cand['h']} src={cand['src'][:60]}")

            tmp = os.path.join(args.out, f'_web_raw_{sku}.png')
            raw = grab_by_download(page, tmp)
            if raw:
                log('  取图方式: 下载按钮（原图）')
            else:
                raw = grab_by_canvas(page, cand['i'], tmp)
                if raw:
                    log('  取图方式: canvas 提取')
            if not raw:
                log('[warn] 自动取图失败（跨域/改版）。')
                log('  兜底：右键保存图片后执行 '
                    f'python scripts/gen_product.py {args.order} --save <图> --out {args.out}')
                sys.exit(6)

            log('[5/5] 归一化落盘')
            out, size = normalize(raw, dst)
            try:
                os.remove(raw)
            except Exception:
                pass
            log(f'[ok] 已落盘: {out}  {size[0]}x{size[1]}')
            log(f'[ok] 现在重跑 fill_template.py --out {args.out} 即自动拾取，无需改订单')
        finally:
            ctx.close()


if __name__ == '__main__':
    main()
