#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用投递：读 公众号预览.html + 同目录 *.png → 上传永久素材 → 替换 src → draft/add

用法：
    python upload_preview.py <dir> <title> <digest>

说明：
- 自动提取 HTML 内 <img src="xxx.png"> 的名字，按出现顺序去重上传，替换成微信 url。
- 封面 thumb_media_id 取名字为 cover 的那张的 media_id。
- 绕过本机死代理 127.0.0.1:1080（系统 HTTP_PROXY 指向它但没起服务）。
"""
import sys, re, json, pathlib, time, urllib.request, io

MAX_BYTES = 1_900_000   # 微信永久图片素材上限 2MB，留余量

# 绕过本机死代理：urllib 默认会读 HTTP_PROXY 环境变量走 127.0.0.1:1080（该代理未启动）
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

sys.path.insert(0, r"F:/桌面/zcode工作区/_wx_read")
from news_publish import load_creds, get_token, http_json

API = "https://api.weixin.qq.com/cgi-bin"


def load_payload(path):
    """读图；超 2MB 则自动压到 1080 宽 JPEG（返回 bytes, filename, content_type）"""
    data = path.read_bytes()
    if len(data) <= MAX_BYTES:
        return data, path.name, "image/png"
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width > 1080:
        im = im.resize((1080, int(im.height * 1080 / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88, optimize=True)
    out = buf.getvalue()
    print(f"  ⤵ {path.name}: {len(data)//1024}KB → JPEG {len(out)//1024}KB")
    return out, path.stem + ".jpg", "image/jpeg"


def upload_img_with_url(token, path):
    """永久素材上传图片，返回 (media_id, url)"""
    path = pathlib.Path(path)
    data, fname, ctype = load_payload(path)
    # HTTP 头/文件名必须是 ASCII：中文图名做安全化，boundary 只用时间戳
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", fname)
    boundary = "----zcode" + str(int(time.time() * 1000))
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="media"; filename="{safe}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode()
    body += data
    body += f"\r\n--{boundary}--\r\n".encode()
    r = http_json(f"{API}/material/add_material?access_token={token}&type=image",
                  data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    if "media_id" not in r:
        raise SystemExit(f"❌ 上传 {path.name} 失败: {r}")
    return r["media_id"], r.get("url", "")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 4:
        raise SystemExit("用法: python upload_preview.py <dir> <title> <digest>")
    d = pathlib.Path(sys.argv[1]).resolve()
    title, digest = sys.argv[2], sys.argv[3]
    # 有「投递版.html」就用它（封面只做 thumb、不内嵌正文）；否则退回预览 HTML
    src_html = d / "投递版.html"
    if not src_html.exists():
        src_html = d / "公众号预览.html"
    html = src_html.read_text(encoding="utf-8")
    names = list(dict.fromkeys(re.findall(r'src="([^"/\\]+?)\.png"', html)))
    if "cover" not in names:
        names.insert(0, "cover")          # 封面仍需上传，只为拿 thumb_media_id
    print(f"📂 {d}\n📄 投递源: {src_html.name}\n🖼 图片({len(names)}): {names}")

    creds = load_creds()
    token = get_token(creds["WECHAT_APP_ID"], creds["WECHAT_APP_SECRET"])
    print("✅ token OK")

    urls, ids = {}, {}
    for n in names:
        p = d / f"{n}.png"
        if not p.exists():
            raise SystemExit(f"❌ 缺图: {p}")
        mid, url = upload_img_with_url(token, p)
        urls[n], ids[n] = url, mid
        print(f"  ✅ {n}: {mid[:16]}…")

    new_html = html
    for n in names:
        new_html = new_html.replace(f'src="{n}.png"', f'src="{urls[n]}"')

    payload = {"articles": [{
        "title": title, "author": "", "digest": digest, "content": new_html,
        "content_source_url": "", "thumb_media_id": ids["cover"],
        "need_open_comment": 0, "only_fans_can_comment": 0,
    }]}
    r = http_json(f"{API}/draft/add?access_token={token}",
                  data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                  headers={"Content-Type": "application/json; charset=utf-8"})
    print("📨 draft/add:", r)
    if r.get("media_id"):
        (d / "draft_id.txt").write_text(r["media_id"], encoding="utf-8")
        print(f"✅ 草稿已建: {r['media_id']}")
    else:
        raise SystemExit(f"❌ 投递失败: {r}")


if __name__ == "__main__":
    main()
