#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实测：draft/add 是否支持「文字消息」（无封面纯文字）"""
import json, pathlib, sys, urllib.request

API = "https://api.weixin.qq.com/cgi-bin"


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


def try_draft(token, article_type, **extra):
    article = {"article_type": article_type,
               "title": "测试·文字消息",
               "content": "这是一条测试文字消息，验证 article_type 是否支持。"}
    article.update(extra)
    payload = {"articles": [article]}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        r = http_json(f"{API}/draft/add?access_token={token}", data=data,
                      headers={"Content-Type": "application/json; charset=utf-8"})
        return r
    except urllib.error.HTTPError as e:
        return {"HTTPError": e.code, "body": e.read().decode("utf-8", "ignore")[:300]}
    except Exception as e:
        return {"EXC": str(e)}


def main():
    creds = load_creds()
    appid, secret = creds.get("WECHAT_APP_ID", ""), creds.get("WECHAT_APP_SECRET", "")
    if not appid or not secret:
        sys.exit("❌ 没读到凭证")

    print("① 获取 token（验证 IP 白名单）……")
    r = http_json(f"{API}/token?grant_type=client_credential&appid={appid}&secret={secret}")
    print("   ", r)
    if "access_token" not in r:
        sys.exit("❌ token 失败，先处理 IP 白名单 / 凭证")
    token = r["access_token"]
    print("   ✓ token 成功\n")

    print("② 试 article_type=text（纯文字，无封面）……")
    print("   ->", try_draft(token, "text"))

    print("\n③ 试 article_type=newspic 不带 image_info（确认 newspic 是否强制要图）……")
    print("   ->", try_draft(token, "newspic"))

    print("\n④ 试 article_type=news 不带 thumb_media_id（确认 news 是否强制要封面）……")
    print("   ->", try_draft(token, "news"))


if __name__ == "__main__":
    sys.exit(main())
