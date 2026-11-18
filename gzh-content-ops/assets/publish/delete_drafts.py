#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清空公众号草稿箱：draft/batchget 列出全部 → draft/delete 逐个删除"""
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


def main():
    creds = load_creds()
    r = http_json(f"{API}/token?grant_type=client_credential"
                  f"&appid={creds['WECHAT_APP_ID']}&secret={creds['WECHAT_APP_SECRET']}")
    if "access_token" not in r:
        sys.exit(f"❌ token 失败: {r}")
    token = r["access_token"]

    # 1. 列出所有草稿
    drafts = []
    offset = 0
    while True:
        r = http_json(f"{API}/draft/batchget?access_token={token}",
                      data=json.dumps({"offset": offset, "count": 20, "no_content": 1}).encode("utf-8"),
                      headers={"Content-Type": "application/json; charset=utf-8"})
        items = r.get("item", [])
        if not items:
            break
        for it in items:
            title = ""
            news = it.get("content", {}).get("news_item", [])
            if news:
                title = news[0].get("title", "")
            drafts.append({"media_id": it["media_id"], "title": title})
        if len(items) < 20:
            break
        offset += len(items)

    print(f"草稿箱共 {len(drafts)} 条：")
    for d in drafts:
        print(f"  - {d['title'][:30]} ({d['media_id'][:16]}…)")

    if not drafts:
        print("没有草稿要删。")
        return

    # 2. 逐个删除
    ok = fail = 0
    for d in drafts:
        rr = http_json(f"{API}/draft/delete?access_token={token}",
                       data=json.dumps({"media_id": d["media_id"]}).encode("utf-8"),
                       headers={"Content-Type": "application/json; charset=utf-8"})
        if rr.get("errcode", 0) == 0:
            ok += 1
        else:
            fail += 1
            print(f"  ❌ 删除失败 {d['title'][:20]}: {rr}")
    print(f"\n✅ 删除完成：成功 {ok}，失败 {fail}")


if __name__ == "__main__":
    main()
