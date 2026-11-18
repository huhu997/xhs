#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号内容运营专家团 · 统一工具库 CLI

一个入口，覆盖 S3 渲染 / S5 合规 / S6 发布的全部机械动作。
设计原则：吃文件不吃约定，所有参数显式传入，不依赖当前目录、不依赖旧项目结构。

用法：
    python gzh.py creds                          # 凭证体检（只报键名与长度，不打印值）
    python gzh.py token                          # 换 access_token 验证连通
    python gzh.py account [--live]               # 账号名/封面署名唯一真源，可与微信后台实时核对
    python gzh.py brand   <path...> [--strict]   # 扫旧账号名（封面署名改没改干净）
    python gzh.py check   <img.png> [--ratio 2.35]
    python gzh.py render  <a.html> <out.png> --width 1880 --height 800
    python gzh.py risk    <path...> [--strict] [--json]
    python gzh.py publish --html <a.html> --title "..." --cover <c.png>
                          [--digest "..."] [--author ""] [--dry-run] [--no-article-type]

退出码：0 成功 / 1 参数或环境错误 / 2 合规阻断 / 3 接口失败
"""
from __future__ import annotations

import argparse
import io
import json
import os
import pathlib
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request

# ---------- 全局：绕开本机死代理 ----------
# 本机 HTTP_PROXY/HTTPS_PROXY 指向 127.0.0.1:1080（拨号型客户端，常常没起），
# urllib 会无条件继承 → 所有出网请求 502。必须显式清空 ProxyHandler。
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

API = "https://api.weixin.qq.com/cgi-bin"
TOOL_DIR = pathlib.Path(__file__).resolve().parent
EXPERT_DIR = TOOL_DIR.parent.parent           # assets/tools -> 专家包根
CREDS_PATH = pathlib.Path.home() / ".baoyu-skills" / ".env"
ACCOUNT_MD = EXPERT_DIR / "config" / "account.md"   # 账号名/封面署名唯一真源
# 记录/规范类文档里引用旧名是「说明」，不是出图源，默认不参与阻断；--include-docs 可强制全扫。
SKIP_DOC_RE = re.compile(
    r"^(?:09-recap\.md|account\.md|cover-spec\.md|README\.md|CHANGELOG\.md|"
    r"lanmu-wulinwaizhuan\.md|.*-compliance.*\.md|.*-report\.md)$", re.I)
CHROME_CANDIDATES = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
]
MAX_MATERIAL_BYTES = 1_900_000               # 微信永久素材上限 2MB，留余量


def log(msg: str) -> None:
    print(msg, flush=True)


def die(msg: str, code: int = 1) -> None:
    print(f"✗ {msg}", file=sys.stderr, flush=True)
    raise SystemExit(code)


# ---------- 凭证 ----------
def load_creds() -> dict:
    """从 ~/.baoyu-skills/.env 读凭证；缺失时回落到环境变量。"""
    creds: dict[str, str] = {}
    if CREDS_PATH.exists():
        for line in CREDS_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("WECHAT_APP_ID", "WECHAT_APP_SECRET"):
        if not creds.get(k) and os.environ.get(k):
            creds[k] = os.environ[k]
    return creds


def http_json(url: str, data: bytes | None = None, headers: dict | None = None, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        die(f"网络请求失败：{e}。若报 502/超时，检查是否残留 HTTP_PROXY 指向未启动的 127.0.0.1:1080", 3)
    except json.JSONDecodeError:
        die(f"接口返回非 JSON：{url}", 3)


def get_token(creds: dict) -> str:
    appid, secret = creds.get("WECHAT_APP_ID"), creds.get("WECHAT_APP_SECRET")
    if not appid or not secret:
        die(f"缺少凭证：{CREDS_PATH} 里没有 WECHAT_APP_ID / WECHAT_APP_SECRET", 1)
    r = http_json(f"{API}/token?grant_type=client_credential&appid={appid}&secret={secret}")
    if "access_token" not in r:
        # 40164 = IP 白名单未加；40013 = appid 无效；40125 = secret 无效
        die(f"取 token 失败：{r}（40164 多为 IP 白名单未加本机公网 IP，需后台自助添加）", 3)
    return r["access_token"]


# ---------- 账号身份 / 署名 ----------
def load_account() -> dict:
    """读 config/account.md 的 MACHINE-READABLE 块；账号名不写死在封面模板里。"""
    if not ACCOUNT_MD.exists():
        die(f"账号配置缺失：{ACCOUNT_MD}（见 config/account.md 模板）", 1)
    text = ACCOUNT_MD.read_text(encoding="utf-8")
    m = re.search(r"<!-- MACHINE-READABLE START -->(.*?)<!-- MACHINE-READABLE END -->", text, re.S)
    if not m:
        die(f"账号配置缺 MACHINE-READABLE 块：{ACCOUNT_MD}", 1)
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    out["old_list"] = [x.strip() for x in out.get("old_names", "").split("|") if x.strip()]
    return out


def scan_old_brand(paths, include_docs: bool = False) -> list[dict]:
    """扫源码里的旧账号名。PNG 里的字扫不出来，所以封面必须由 HTML 渲染。"""
    old = load_account().get("old_list", [])
    if not old:
        return []
    files: list[pathlib.Path] = []
    for p in paths:
        p = pathlib.Path(p)
        if p.is_dir():
            files += [f for f in p.rglob("*")
                      if f.is_file() and f.suffix.lower() in (".html", ".htm", ".md", ".txt")]
        elif p.exists():
            files.append(p)
    hits: list[dict] = []
    for f in files:
        if "_audit" in f.parts:            # 服务端回拉的审查副本不是产出源
            continue
        if not include_docs and SKIP_DOC_RE.match(f.name):   # 复盘/规范里引用旧名属说明
            continue
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            for name in sorted(old, key=len, reverse=True):   # 最长优先，一行只报一次
                if name in line:
                    hits.append({"file": str(f), "line": i, "name": name,
                                 "text": line.strip()[:110]})
                    break
    return hits


def cmd_account(a) -> int:
    cfg = load_account()
    log(f"配置    : {ACCOUNT_MD}")
    log(f"账号名  : {cfg.get('account_name')}   (更新于 {cfg.get('account_name_updated')})")
    log(f"笔名    : {cfg.get('pen_name')}")
    log(f"封面署名: {cfg.get('cover_byline')}")
    log(f"禁用旧名: {' / '.join(cfg.get('old_list', []))}")
    log(f"定位    : {cfg.get('positioning', '未配置')}   (更新于 {cfg.get('positioning_updated', '-')})")
    log(f"默认栏目: {cfg.get('default_column', '未配置')}")
    log(f"禁区题材: {cfg.get('banned_topics', '未配置')}")
    if a.live:
        r = http_json(f"{API}/account/getaccountbasicinfo?access_token={get_token(load_creds())}")
        live = r.get("nickname") or f"接口未返回昵称：{r}"
        log(f"微信后台昵称: {live}")
        if live != cfg.get("account_name"):
            log("⚠ 后台昵称与配置不一致：按 config/account.md 第 4 节走改名 SOP，并重渲染所有含署名的图。")
            return 1
        log("✓ 后台昵称与配置一致")
    return 0


def cmd_brand(a) -> int:
    hits = scan_old_brand(a.paths, include_docs=a.include_docs)
    if a.json:
        log(json.dumps(hits, ensure_ascii=False, indent=2))
    elif not hits:
        log("✓ 未发现旧账号名")
    else:
        log(f"✗ 发现 {len(hits)} 处旧账号名：")
        for h in hits[:40]:
            log(f"  {h['file']}:{h['line']}  [{h['name']}]  {h['text']}")
        log("  改成 config/account.md 的 cover_byline 后重渲染封面；历史归档可留档，新稿必须先清干净。")
    return 1 if (hits and a.strict) else 0


# ---------- 图片 ----------
def _shrink(path: pathlib.Path) -> tuple[bytes, str, str]:
    """超限则压到 1080 宽 JPEG，返回 (bytes, filename, content_type)。"""
    data = path.read_bytes()
    if len(data) <= MAX_MATERIAL_BYTES:
        return data, path.name, "image/png"
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    if im.width > 1080:
        im = im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=86, optimize=True)
    return buf.getvalue(), path.stem + ".jpg", "image/jpeg"


def _multipart(field: str, filename: str, ctype: str, payload: bytes) -> tuple[bytes, str]:
    boundary = "----gzh" + str(int(time.time() * 1000))
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode()
    body += payload
    body += f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def upload_material(token: str, img: pathlib.Path) -> str:
    """永久图片素材 → media_id（封面 thumb 必须用这个）。"""
    payload, fname, ctype = _shrink(img)
    body, ct = _multipart("media", fname, ctype, payload)
    r = http_json(f"{API}/material/add_material?access_token={token}&type=image",
                  data=body, headers={"Content-Type": ct})
    if "media_id" not in r:
        die(f"上传永久素材失败（{img.name}）：{r}", 3)
    return r["media_id"]


def upload_content_image(token: str, img: pathlib.Path) -> str:
    """正文内图 → 微信图床 URL。"""
    payload, fname, ctype = _shrink(img)
    body, ct = _multipart("media", fname, ctype, payload)
    r = http_json(f"{API}/media/uploadimg?access_token={token}",
                  data=body, headers={"Content-Type": ct})
    if "url" not in r:
        die(f"上传正文图失败（{img.name}）：{r}", 3)
    return r["url"]


# ---------- 子命令 ----------
def cmd_creds(a) -> int:
    creds = load_creds()
    log(f"凭证文件: {CREDS_PATH} {'✓ 存在' if CREDS_PATH.exists() else '✗ 不存在'}")
    for k in ("WECHAT_APP_ID", "WECHAT_APP_SECRET"):
        v = creds.get(k, "")
        log(f"  {k}: {'已设置，长度 ' + str(len(v)) if v else '✗ 未设置'}")
    ok = bool(creds.get("WECHAT_APP_ID") and creds.get("WECHAT_APP_SECRET"))
    log(f"结论: {'✓ 凭证齐备，可尝试 publish' if ok else '✗ 凭证不全，publish 会失败'}")
    return 0 if ok else 1


def cmd_token(a) -> int:
    token = get_token(load_creds())
    log(f"✓ access_token 获取成功（长度 {len(token)}，前 6 位 {token[:6]}…）")
    return 0


def cmd_check(a) -> int:
    from PIL import Image
    p = pathlib.Path(a.image)
    if not p.exists():
        die(f"文件不存在：{p}", 1)
    size = p.stat().st_size
    im = Image.open(p)
    w, h = im.size
    ratio = w / h
    log(f"文件: {p.name}")
    log(f"  尺寸: {w} × {h}")
    log(f"  比例: {ratio:.3f}:1" + (f"（目标 {a.ratio}:1，偏差 {abs(ratio / a.ratio - 1) * 100:.1f}%）" if a.ratio else ""))
    log(f"  体积: {size / 1024:.1f} KB" + ("  ⚠ 超 2MB，上传时会自动压缩" if size > MAX_MATERIAL_BYTES else ""))
    bad = False
    if a.ratio and abs(ratio / a.ratio - 1) > 0.02:
        log(f"  ✗ 比例不符，公众号封面会裁切")
        bad = True
    if size > MAX_MATERIAL_BYTES:
        log("  ⚠ 体积偏大（可上传，会被压成 JPEG）")
    return 2 if bad else 0


def _find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if pathlib.Path(c).exists():
            return c
    die("未找到 Chrome / Edge，无法截图。请显式指定或装一个。", 1)


def cmd_render(a) -> int:
    import subprocess
    src, out = pathlib.Path(a.html).resolve(), pathlib.Path(a.png).resolve()
    if not src.exists():
        die(f"HTML 不存在：{src}", 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    # 移动端预览一致性：若页面未固定宽度（非封面等固定画布），强制 html/body 宽=目标宽，
    # 否则本机 headless 默认按 980 布局、再用 --width 截图会把右侧裁掉，预览失真。
    # （此 headless 版本无视 viewport meta，只能用强制宽度兜底；封面页有固定 width 会被跳过。）
    html_text = src.read_text(encoding="utf-8", errors="ignore")
    _has_fixed = ('width:1880' in html_text or 'width: 1880' in html_text
                 or 'html,body { width' in html_text or 'html,body{width' in html_text)
    if not _has_fixed:
        inject = f'<style>html,body{{width:{a.width}px !important;overflow-x:hidden;}}</style>'
        if "</head>" in html_text:
            html_text = html_text.replace("</head>", inject + "</head>", 1)
        else:
            # 正文常是「无 <html>/<body> 的 HTML 片段」：没有 </head> 可替换，
            # 旧版 replace 静默失效 → Chrome 自动补全的 body 仍按 980px 布局，
            # 再用 --width 375 截图就会「每行切字、表格缺右列」的假裁切。
            # 片段形态直接把样式前置，浏览器补全 html/body 后同样生效。
            html_text = inject + html_text
        tmp_html = src.with_suffix(".render-tmp.html")
        tmp_html.write_text(html_text, encoding="utf-8")
        src = tmp_html
    chrome = _find_chrome()
    # 独立 user-data-dir，避免和正在运行的 Chrome/Opera 抢 singleton 锁
    with tempfile.TemporaryDirectory(prefix="gzh-render-") as tmp:
        cmd = [
            chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--window-size={a.width},{a.height}",
            f"--screenshot={out}",
            f"--user-data-dir={tmp}",
            "--default-background-color=00000000" if a.transparent else "--default-background-color=ffffffff",
            src.as_uri(),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    # 清理注入 viewport 的临时文件
    if src != src.with_suffix(".render-tmp.html") and src.name.endswith(".render-tmp.html"):
        try:
            src.unlink()
        except OSError:
            pass
    if not out.exists() or out.stat().st_size == 0:
        die(f"截图失败（exit={r.returncode}）：{(r.stderr or r.stdout)[-500:]}", 1)
    from PIL import Image
    w, h = Image.open(out).size
    log(f"✓ {out.name}  {w} × {h}  {out.stat().st_size / 1024:.1f} KB")
    if (w, h) != (a.width, a.height):
        log(f"  ⚠ 实际尺寸与预期 {a.width}×{a.height} 不符，检查 HTML 是否设了固定宽高")
    return 0


def cmd_risk(a) -> int:
    """委托给同包 riskcheck.py（BLOCK 阻断 / WARN 人工判断）。

    重要语义：BLOCK 不等于「文章一定违规」，它等于「必须人工裁定」。
    财经稿里「中国」几乎每条都会命中（中国经济周刊 / 中国市场 / 中国石油…），
    这类已确认的误伤用 --ignore-words 显式排除，不要为了过扫描去改文章措辞。
    """
    pub = EXPERT_DIR / "assets" / "publish"
    if not (pub / "riskcheck.py").exists():
        die(f"找不到 riskcheck.py：{pub}", 1)
    sys.path.insert(0, str(pub))
    import importlib
    rc = importlib.import_module("riskcheck")
    paths = [pathlib.Path(p) for p in a.paths]
    hits = rc.scan_paths(paths, include_meta=getattr(a, "include_meta", False))

    ignore = {w.strip() for w in (a.ignore_words or "").split(",") if w.strip()}
    # --json 时 stdout 必须只留 JSON，人类可读内容全走 stderr
    out = sys.stderr if a.json else sys.stdout

    def say(msg: str) -> None:
        print(msg, file=out, flush=True)

    if ignore:
        skipped = [h for h in hits if getattr(h, "word", "") in ignore]
        hits = [h for h in hits if getattr(h, "word", "") not in ignore]
        if skipped:
            say(f"（按 --ignore-words 跳过 {len(skipped)} 处：" +
                "、".join(sorted({h.word for h in skipped})) + "）")

    rc.report(hits, stream=out, strict=a.strict, verbose_safe=getattr(a, "verbose_safe", False))

    if a.json:
        rows = [h.as_dict() if hasattr(h, "as_dict") else dict(h) for h in hits]
        print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))

    block = [h for h in hits if getattr(h, "level", "") == "BLOCK"]
    if block:
        say(f"⛔ {len(block)} 处 BLOCK 待人工裁定（可能是误伤，逐条看上下文，别盲改）")
        return 2
    return 0


def cmd_verify(a) -> int:
    """A 股盘面数据多源核对（委托 market_verify.py）。"""
    import subprocess
    script = TOOL_DIR / "market_verify.py"
    if not script.exists():
        die(f"找不到 market_verify.py：{script}", 1)
    cmd = [sys.executable, str(script)]
    if a.date:
        cmd += ["--date", a.date]
    if a.prev:
        cmd += ["--prev", a.prev]
    if a.out:
        cmd += ["--out", a.out]
    if a.quiet:
        cmd += ["--quiet"]
    return subprocess.run(cmd).returncode


# ---------- 微信兼容：CSS 内联化 ----------
# 公众号 draft/add 只保留内联 style=""，会整体剥掉 <style> 与 class 选择器。
# 发送前把 <style> 规则内联到各元素的 style 属性，颜色/边框/底色/分隔线才能在微信存活。
# 已是内联、无 <style>/class 的 HTML 原样返回（零副作用）。
def _parse_decl(block: str) -> dict:
    out = {}
    for part in block.split(";"):
        part = part.strip()
        if ":" not in part:
            continue
        k, _, v = part.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k and v:
            out[k] = v
    return out


def inline_css(html: str) -> str:
    if "<style" not in html and "class=" not in html:
        return html
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.I | re.S))
    elem_rules, class_rules, id_rules = [], {}, {}
    for m in re.finditer(r"([^{}]+)\{([^{}]+)\}", css):
        sels = [s.strip() for s in m.group(1).split(",") if s.strip()]
        decls = _parse_decl(m.group(2))
        for sel in sels:
            if sel.startswith(".") and " " not in sel:
                n = sel[1:]; d = dict(class_rules.get(n, {})); d.update(decls); class_rules[n] = d
            elif sel.startswith("#") and " " not in sel:
                n = sel[1:]; d = dict(id_rules.get(n, {})); d.update(decls); id_rules[n] = d
            else:
                tg = re.match(r"[a-zA-Z][\w-]*", sel)
                if tg:
                    elem_rules.append((tg.group(0).lower(), decls))
    if not (elem_rules or class_rules or id_rules):
        return html

    def repl(m: re.Match) -> str:
        tag = m.group(1).lower()
        attrs = m.group(2) or ""
        classes = set()
        for c in re.findall(r'class="([^"]*)"', attrs):
            classes.update(c.split())
        ids = re.findall(r'id="([^"]*)"', attrs)
        out = {}
        for t, d in elem_rules:
            if t == tag:
                out.update(d)
        for c in classes:
            if c in class_rules:
                out.update(class_rules[c])
        for i in ids:
            if i in id_rules:
                out.update(id_rules[i])
        if not out:
            return m.group(0)
        existing = {}
        es = re.search(r'style="([^"]*)"', attrs)
        if es:
            existing = _parse_decl(es.group(1))
        merged = dict(out)
        for k, v in existing.items():
            merged.setdefault(k, v)  # 已有 inline 优先
        new_style = "; ".join(f"{k}: {v}" for k, v in merged.items())
        attrs2 = re.sub(r'\s*style="[^"]*"', "", attrs).strip()
        closing = "/" if m.group(3).startswith("/") else ""
        return f"<{tag} {attrs2} style=\"{new_style}\"{closing}>"

    html = re.sub(r"<([a-zA-Z][\w-]*)((?:\s[^>]*?)?)(/?>)", repl, html)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.I | re.S)
    return html


def cmd_publish(a) -> int:
    html_path = pathlib.Path(a.html).resolve()
    cover = pathlib.Path(a.cover).resolve()
    if not html_path.exists():
        die(f"HTML 不存在：{html_path}", 1)
    if not cover.exists():
        die(f"封面不存在：{cover}", 1)
    if len(a.title) > 64:
        die(f"标题 {len(a.title)} 字，超过公众号 64 字上限", 1)

    html = html_path.read_text(encoding="utf-8")

    # 账号署名闸门：账号改名后最容易漏的是封面 cover.html 里写死的旧名，
    # 图一旦重渲染进草稿箱，用户看到的就是「号换了、图上还印着旧号」。
    # 扫的是 HTML 源码而非 PNG，所以封面必须经 HTML 渲染（禁止直接改图）。
    if not getattr(a, "allow_old_brand", False):
        srcs = [html_path.parent / "cover.html", html_path, cover.with_suffix(".html")]
        srcs = [p for p in dict.fromkeys(srcs) if p.exists()]
        hits = scan_old_brand(srcs)
        if hits:
            log("✗ 推送被拦：检测到旧账号名（图片/正文署名没跟着改名）：")
            for h in hits[:20]:
                log(f"  {h['file']}:{h['line']}  [{h['name']}]  {h['text']}")
            die("按 config/account.md 改署名并重新渲染封面；确需保留才加 --allow-old-brand", 1)

    # 收集 HTML 内引用的本地图片（相对 HTML 所在目录）
    local_imgs = list(dict.fromkeys(re.findall(r'src="([^"\\]+?\.(?:png|jpg|jpeg|PNG|JPG))"', html)))
    local_imgs = [n for n in local_imgs if not n.startswith(("http://", "https://", "data:"))]

    # 检查是否有 h1 刊头（会与公众号标题重复）
    if re.search(r"<h1[\s>]", html, re.I):
        log("⚠ HTML 含 <h1>，公众号会自动再加一次标题，可能出现重复。建议用去掉刊头的粘贴版。")

    log(f"HTML   : {html_path.name}  ({len(html)} 字符)")
    log(f"标题   : {a.title}  ({len(a.title)} 字)")
    log(f"封面   : {cover.name}  ({cover.stat().st_size / 1024:.1f} KB)")
    log(f"正文图 : {len(local_imgs)} 张 {local_imgs if local_imgs else ''}")

    if a.dry_run:
        log("\n[dry-run] 只做本地校验，未联网、未写任何数据。")
        log("✓ 文件齐备，去掉 --dry-run 即可真推草稿箱。")
        return 0

    creds = load_creds()
    token = get_token(creds)
    log("✓ token OK")

    # 修稿重推前，自动删除同标题的旧草稿。
    # 铁律：draft/add 只会「新增」，迭代修稿若不清理就会堆一箱历史版本，
    # 用户在草稿箱看到的是多条旧封面/旧插图（金字标题、糊图、被 1:1 裁掉的标题）。
    if getattr(a, "replace_same_title", True):
        try:
            r = http_json(f"{API}/draft/batchget?access_token={token}",
                          data=json.dumps({"offset": 0, "count": 20, "no_content": 1}).encode("utf-8"),
                          headers={"Content-Type": "application/json"})
            for it in r.get("item", []):
                for n in (it.get("content") or {}).get("news_item", []):
                    if n.get("title") == a.title:
                        mid_old = it.get("media_id")
                        rr = http_json(f"{API}/draft/delete?access_token={token}",
                                       data=json.dumps({"media_id": mid_old}).encode("utf-8"),
                                       headers={"Content-Type": "application/json"})
                        if rr.get("errcode", 0) == 0:
                            log(f"✓ 清理同标题旧草稿 {mid_old[:20]}…")
        except SystemExit:
            raise
        except Exception as e:
            log(f"⚠ 清理旧草稿失败（不阻断推送）：{e}")

    # 正文图：本地相对路径 → 微信图床 URL
    if getattr(a, "inline_css", True):
        new_html = inline_css(html)
        log("✓ CSS 已内联化（微信兼容：<style>/class → 内联 style，颜色/边框/分隔线可在微信存活）")
    else:
        new_html = html
    for name in local_imgs:
        p = (html_path.parent / name).resolve()
        if not p.exists():
            die(f"正文引用的图片不存在：{p}", 1)
        url = upload_content_image(token, p)
        new_html = new_html.replace(f'src="{name}"', f'src="{url}"')
        log(f"  ✓ 正文图 {name} → {url[:48]}…")

    # 封面永远上传（thumb_media_id 必须是永久素材）
    thumb = upload_material(token, cover)
    log(f"✓ 封面已上传 media_id={thumb[:20]}…")

    article = {
        "title": a.title,
        "author": a.author or "",
        "digest": a.digest or "",
        "content": new_html,
        "content_source_url": "",
        "thumb_media_id": thumb,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    if a.article_type:
        article["article_type"] = "news"

    r = http_json(f"{API}/draft/add?access_token={token}",
                  data=json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8"),
                  headers={"Content-Type": "application/json; charset=utf-8"})
    if "media_id" not in r:
        die(f"draft/add 失败：{r}", 3)

    mid = r["media_id"]
    log(f"\n✅ 草稿已入箱  media_id={mid}")
    log("   下一步：https://mp.weixin.qq.com → 内容与互动 → 草稿箱")
    log("   ⚠ 本工具只写草稿，不群发、不发布。发表键必须人工点。")
    if a.save_id:
        out = html_path.parent / "draft_id.txt"
        out.write_text(mid, encoding="utf-8")
        log(f"   media_id 已写入 {out.name}")
    return 0


# ---------- 入口 ----------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="gzh.py",
        description="公众号内容运营专家团工具库：渲染 / 合规 / 发布",
        epilog="示例：python gzh.py publish --html 08-article-paste.html --title \"标题\" --cover 08-cover.png --dry-run",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("creds", help="凭证体检（不打印密钥）").set_defaults(func=cmd_creds)
    sub.add_parser("token", help="换取 access_token 验证连通").set_defaults(func=cmd_token)

    p = sub.add_parser("account", help="账号名/封面署名唯一真源（可实时核对微信后台）")
    p.add_argument("--live", action="store_true", help="调 account/getaccountbasicinfo 核对昵称")
    p.set_defaults(func=cmd_account)

    p = sub.add_parser("brand", help="扫描旧账号名（检查封面署名是否跟着改名）")
    p.add_argument("paths", nargs="+", help="文件或目录，扫 .html/.md/.txt")
    p.add_argument("--strict", action="store_true", help="命中时以退出码 1 结束（用于流水线阻断）")
    p.add_argument("--json", action="store_true", help="输出 JSON 命中列表")
    p.add_argument("--include-docs", action="store_true",
                   help="连复盘/规范/报告类文档一起扫（默认跳过，它们引用旧名是说明而非出图源）")
    p.set_defaults(func=cmd_brand, include_docs=False)

    p = sub.add_parser("check", help="图片尺寸/比例/体积检查")
    p.add_argument("image")
    p.add_argument("--ratio", type=float, default=None, help="期望宽高比，如封面 2.35")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("render", help="HTML → PNG 截图（Chrome headless）")
    p.add_argument("html")
    p.add_argument("png")
    p.add_argument("--width", type=int, default=1880)
    p.add_argument("--height", type=int, default=800)
    p.add_argument("--transparent", action="store_true", help="透明底")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("risk", help="合规风险扫描（BLOCK 阻断 / WARN 人工判断）")
    p.add_argument("paths", nargs="+")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--json", action="store_true", help="stdout 输出纯 JSON（报告走 stderr）")
    p.add_argument("--ignore-words", default="", help="逗号分隔，跳过已确认的误伤词，如 中国,看多")
    p.add_argument("--include-meta", action="store_true")
    p.add_argument("--verbose-safe", action="store_true")
    p.set_defaults(func=cmd_risk)

    p = sub.add_parser("verify", help="A 股盘面数据多源核对（涨跌家数/涨跌停池/板块/资金流/美股）")
    p.add_argument("--date", default=None, help="交易日 YYYYMMDD，默认今天")
    p.add_argument("--prev", default=None, help="上一交易日，默认自动往前找")
    p.add_argument("--out", default=None, help="结果 JSON 路径")
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("publish", help="推公众号草稿箱（不群发、不发布）")
    p.add_argument("--html", required=True, help="排版好的 HTML（建议用去刊头的粘贴版）")
    p.add_argument("--title", required=True)
    p.add_argument("--cover", required=True, help="封面 PNG，建议 2.35:1")
    p.add_argument("--digest", default="")
    p.add_argument("--author", default="")
    p.add_argument("--dry-run", action="store_true", help="只校验不联网")
    p.add_argument("--no-article-type", dest="article_type", action="store_false",
                   help="不传 article_type 字段（旧版接口兼容）")
    p.add_argument("--save-id", action="store_true", help="把 media_id 写到 HTML 同目录 draft_id.txt")
    p.add_argument("--no-inline", dest="inline_css", action="store_false",
                   help="跳过 CSS 内联化（HTML 已手动内联时可用）")
    p.add_argument("--keep-old", dest="replace_same_title", action="store_false",
                   help="保留同标题旧草稿（默认自动删除，避免草稿箱堆历史版本）")
    p.add_argument("--allow-old-brand", action="store_true",
                   help="跳过旧账号名拦截（仅历史稿重推时用，新稿一律不许）")
    p.set_defaults(func=cmd_publish, article_type=True, inline_css=True, replace_same_title=True)
    return ap


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    a = build_parser().parse_args()
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
