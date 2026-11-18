#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投后回验：draft/get 拉回草稿 → 校验标题/摘要/图片数/span leaf/图片指纹(aHash)
用法: python postcheck.py
"""
import json, pathlib, re, sys, urllib.request

sys.path.insert(0, r"F:/桌面/zcode工作区/_wx_read")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from news_publish import http_json, load_creds, get_token
import upload_article as ua

BASE = pathlib.Path(__file__).resolve().parent
API = "https://api.weixin.qq.com/cgi-bin"


def ahash(img_bytes, size=16):
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(img_bytes)).convert("L").resize((size, size), Image.LANCZOS)
    px = list(im.getdata())
    avg = sum(px) / len(px)
    return sum(1 << i for i, v in enumerate(px) if v > avg)


def hamming(a, b):
    return bin(a ^ b).count("1")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    media_id = (BASE / "draft_id.txt").read_text(encoding="utf-8").strip()
    print("草稿 media_id:", media_id)
    creds = load_creds()
    token = get_token(creds["WECHAT_APP_ID"], creds["WECHAT_APP_SECRET"])
    r = http_json(f"{API}/draft/get?access_token={token}",
                  data=json.dumps({"media_id": media_id}).encode("utf-8"),
                  headers={"Content-Type": "application/json"})
    if "news_item" not in r:
        raise SystemExit(f"❌ draft/get 失败: {r}")
    item = r["news_item"][0]
    content = item.get("content", "")
    print("标题:", item.get("title"))
    print("摘要:", item.get("digest"))
    print("封面 thumb_url:", (item.get("thumb_url") or "")[:60], "…")
    print("图片数(<img>):", len(re.findall(r"<img", content)))
    print("span leaf 数:", len(re.findall(r'<span leaf="">', content)))
    # 草稿里的图是 data-src，先归一化
    urls = re.findall(r'data-src="([^"]+)"', content) or re.findall(r'<img[^>]+src="([^"]+)"', content)
    urls = ["https:" + u if u.startswith("//") else u for u in urls]
    urls = [re.sub(r"^http://", "https://", u) for u in urls]
    print(f"正文图 URL: {len(urls)} 个")
    hits, misses = [], []
    local = [BASE / f"{n}.png" for n in ua.IMAGES]
    remote = []
    for u in urls:
        try:
            remote.append(ahash(fetch(u)))
        except Exception as e:
            print("  下载失败:", u[:50], e)
    for lp in local:
        if not lp.exists():
            continue
        h = ahash(lp.read_bytes())
        if not remote:
            break
        best = min(hamming(h, rh) for rh in remote)
        (hits if best <= 6 else misses).append((lp.name, best))
    print("\n图片指纹核验（aHash，距离≤6 视为命中）:")
    for n, d in hits:
        print(f"  ✅ {n}  距离 {d}")
    for n, d in misses:
        print(f"  ❌ {n}  距离 {d}")
    print(f"\n结论: {len(hits)}/{len(hits) + len(misses)} 命中")


if __name__ == "__main__":
    main()
