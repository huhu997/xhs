#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号「数据派财经快评」· news 图文发布（v3：三封面方案自动轮换）
视觉规范定稿：
  底色 #F1F2EE 米白 · 标题 #111417 深墨 · 强调 #E85D2A 橙红 · 正文 #2A2A2A
  封面三方案轮换：A超大数字 / B上下分割 / C数据卡片（核心数字由文案一并给出）
  正文：首段钩子(17px粗) / 中段(16px行高1.8) / 末段态度(16px粗)，数字自动橙色加粗
"""
import json, pathlib, random, re, sys, time, urllib.request
from PIL import Image, ImageDraw, ImageFont

API = "https://api.weixin.qq.com/cgi-bin"
FONT = "C:/Windows/Fonts/msyh.ttc"
OUT_DIR = pathlib.Path("F:/桌面/zcode工作区/_wx_read")

THEME = {
    "bg": "#F1F2EE", "ink": "#111417", "text": "#2A2A2A",
    "accent": "#E85D2A", "muted": "#9A9A9A",
    "body": 16, "body_hook": 17, "line_height": 1.8,
}
STYLE_POOL = ["A", "B", "C"]   # 三个封面方案
RECENT_AVOID = 2               # 最近 2 次不重复


def _hex(c):
    return tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


def _wrap(d, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    lines.append(cur)
    return lines


# ---------- 三个封面方案（900x900，文字水平居中，内容集中在中心安全区）----------
# 2.35:1 显示时微信取中心横带 y 258-642；1:1 显示全图；核心内容全放横带内并居中
Y0 = 258          # 2.35:1 中心横带起点
BAND_H = 384      # 横带高度
CW = 900          # 画布宽（水平居中基准）


def _center(d, y, text, font, fill, W=CW):
    """水平居中画字"""
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)


def cover_A(title, figure, out_path):
    """A 超大数字：品牌 + 巨大橙红数字 + 标签 + 标题，全部水平居中"""
    W, H = 900, 900
    bg, ink, accent, muted = (_hex(THEME[k]) for k in ("bg", "ink", "accent", "muted"))
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(FONT, 26)
    ft = ImageFont.truetype(FONT, 34)
    fd = ImageFont.truetype(FONT, 22)
    num, label = (figure.split(" ", 1) + [""])[:2]
    size = 170 if len(num) <= 2 else (130 if len(num) <= 5 else 100)
    fbig = ImageFont.truetype(FONT, size)
    fmid = ImageFont.truetype(FONT, 58)
    _center(d, Y0 + 26, "数据派 · 财经快评", fb, accent)
    _center(d, Y0 + 76, num, fbig, accent)
    if label:
        _center(d, Y0 + 262, label, fmid, ink)
    y = Y0 + 300 if label else Y0 + 276
    for ln in _wrap(d, title, ft, W - 200)[:2]:
        _center(d, y, ln, ft, ink)
        y += 48
    _center(d, Y0 + 352, time.strftime("%Y.%m.%d"), fd, muted)
    img.save(out_path)
    return out_path


def cover_B(title, figure, out_path):
    """B 上下分割（中心横带内）：品牌+标题 / 深墨块 + 橙红核心数字，全部居中"""
    W, H = 900, 900
    bg, ink, accent = (_hex(THEME[k]) for k in ("bg", "ink", "accent"))
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(FONT, 26)
    ft = ImageFont.truetype(FONT, 40)
    fbig = ImageFont.truetype(FONT, 64)
    fd = ImageFont.truetype(FONT, 22)
    _center(d, Y0 + 22, "数据派 · 财经快评", fb, accent)
    y = Y0 + 70
    for ln in _wrap(d, title, ft, W - 200)[:2]:
        _center(d, y, ln, ft, ink)
        y += 54
    d.rectangle([0, Y0 + 200, W, Y0 + BAND_H], fill=ink)
    _center(d, Y0 + 224, figure, fbig, accent)
    _center(d, Y0 + 336, "数据派 · 财经快评  ·  " + time.strftime("%Y.%m.%d"), fd, (255, 255, 255))
    img.save(out_path)
    return out_path


def cover_C(title, figure, out_path):
    """C 数据卡片：K线柱 + 橙红圆角卡片，全部居中"""
    W, H = 900, 900
    bg, ink, accent, muted = (_hex(THEME[k]) for k in ("bg", "ink", "accent", "muted"))
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(FONT, 26)
    ft = ImageFont.truetype(FONT, 42)
    fcard = ImageFont.truetype(FONT, 52)
    fd = ImageFont.truetype(FONT, 22)
    random.seed(hash(figure) % 1000)
    for i in range(9):   # 右侧 K 线柱（居中带内右半区）
        x = 500 + i * 42
        h = random.randint(50, 170)
        d.rectangle([x, Y0 + 210 - h, x + 16, Y0 + 210], fill=(226, 226, 220))
    _center(d, Y0 + 22, "数据派 · 财经快评", fb, accent)
    y = Y0 + 74
    for ln in _wrap(d, title, ft, 440)[:2]:
        _center(d, y, ln, ft, ink)
        y += 58
    d.rounded_rectangle([CW // 2 - 178, Y0 + 220, CW // 2 + 178, Y0 + 350], radius=16, fill=accent)
    _center(d, Y0 + 248, figure, fcard, (255, 255, 255))
    _center(d, Y0 + 358, time.strftime("%Y.%m.%d"), fd, muted)
    img.save(out_path)
    return out_path


COVERS = {"A": cover_A, "B": cover_B, "C": cover_C}


def pick_style(hist_path):
    """自动轮换：从 A/B/C 里挑最近 RECENT_AVOID 次没用过的"""
    used = []
    if hist_path.exists():
        try:
            used = json.loads(hist_path.read_text(encoding="utf-8"))
        except Exception:
            used = []
    for s in STYLE_POOL:
        if s not in used[-RECENT_AVOID:]:
            return s
    return STYLE_POOL[0]


def record_style(hist_path, style, title):
    try:
        hist = json.loads(hist_path.read_text(encoding="utf-8")) if hist_path.exists() else []
    except Exception:
        hist = []
    hist.append({"style": style, "title": title, "date": time.strftime("%Y-%m-%d")})
    hist_path.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")


def make_cover(title, figure, out_path):
    hist = OUT_DIR / ".cover_history.json"
    style = pick_style(hist)
    COVERS[style](title, figure, out_path)
    record_style(hist, style, title)
    return style


# ---------- API 部分 ----------
def http_json(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def load_creds():
    env = pathlib.Path.home() / ".baoyu-skills" / ".env"
    creds = {}
    for line in env.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip().strip('"').strip("'")
    return creds


def get_token(appid, secret):
    r = http_json(f"{API}/token?grant_type=client_credential&appid={appid}&secret={secret}")
    if "access_token" not in r:
        raise SystemExit(f"❌ token 失败: {r}")
    return r["access_token"]


def upload_img(token, img_path):
    img_path = pathlib.Path(img_path)
    boundary = "----zcode" + str(int(time.time() * 1000))
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="media"; filename="%s"\r\n' % img_path.name.encode()
    body += b"Content-Type: image/png\r\n\r\n"
    body += img_path.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    r = http_json(f"{API}/material/add_material?access_token={token}&type=image",
                  data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    if "media_id" not in r:
        raise SystemExit(f"❌ 上传封面失败: {r}")
    return r["media_id"]


def highlight(text):
    t = re.sub(r'([+-]?\d+(?:\.\d+)?%)',
               lambda m: f'<span style="color:{THEME["accent"]};font-weight:bold;">{m.group(1)}</span>', text)
    t = re.sub(r'(\d+(?:\.\d+)?(?:家|只|跌停|涨停|连板|板|亿港元|万亿|亿|次))',
               lambda m: f'<span style="color:{THEME["accent"]};font-weight:bold;">{m.group(1)}</span>', t)
    return t


def to_html(text):
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    hook = f'<p style="font-size:{THEME["body_hook"]}px;color:{THEME["ink"]};font-weight:bold;line-height:{THEME["line_height"]};margin:0 0 14px;">'
    mid = f'<p style="font-size:{THEME["body"]}px;color:{THEME["text"]};line-height:{THEME["line_height"]};margin:0 0 14px;">'
    tail = f'<p style="font-size:{THEME["body"]}px;color:{THEME["ink"]};font-weight:bold;line-height:{THEME["line_height"]};margin:0;">'
    out = []
    for i, p in enumerate(paras):
        p = highlight(p)
        if i == 0 and len(paras) > 1:
            out.append(hook + p + "</p>")
        elif i == len(paras) - 1 and len(paras) > 1:
            out.append(tail + p + "</p>")
        else:
            out.append(mid + p + "</p>")
    return "".join(out)


def add_news_draft(token, title, content, thumb_media_id):
    payload = {"articles": [{"article_type": "news", "title": title,
                             "content": content, "thumb_media_id": thumb_media_id,
                             # 封面原图 900x900，用裁剪坐标分别出 2.35:1（中心横带）和 1:1（全图）两张封面
                             "pic_crop_235_1": [0.0, 0.287, 1.0, 0.713],
                             "pic_crop_1_1": [0.0, 0.0, 1.0, 1.0]}]}
    return http_json(f"{API}/draft/add?access_token={token}",
                     data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                     headers={"Content-Type": "application/json; charset=utf-8"})


def publish(title, text, figure):
    """一条快评 = 标题 + 正文 + 封面核心数字；自动轮换封面方案 + 投草稿箱"""
    creds = load_creds()
    token = get_token(creds["WECHAT_APP_ID"], creds["WECHAT_APP_SECRET"])
    cover_path = OUT_DIR / "cover.png"
    style = make_cover(title, figure, str(cover_path))
    thumb = upload_img(token, cover_path)
    content = to_html(text)
    r = add_news_draft(token, title, content, thumb)
    print(f"封面方案: {style} | 核心数字: {figure} | 标题字数: {len(title)}")
    return r


if __name__ == "__main__":
    title = "52家涨停，0家跌停，一只跌停都没有"
    figure = "0 跌停"
    text = ("今天 A 股涨停 52 家，跌停 0 家——注意，是一个都没有。\n\n"
            "昨天还有 2 只跌停，今天直接清零。全市场找不到一只被按死跌停的。\n\n"
            "跌停代表最恐慌的那批人，他们今天一个都没跑，情绪到了“只进不出”的温度。\n\n"
            "记住这个数字：0 跌停。它比“上证涨 0.59%”更能告诉你市场现在有多热。")
    r = publish(title, text, figure)
    print("draft/add 结果:", r)
    if "media_id" in r:
        print(f"\n✅ 快评草稿已入箱！media_id: {r['media_id']}")
        print("   确认：mp.weixin.qq.com → 草稿箱")
