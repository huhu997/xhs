#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号「发布」通道（freepublish）：发布草稿 + 查发布记录"""
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
    token_r = http_json(f"{API}/token?grant_type=client_credential"
                        f"&appid={creds['WECHAT_APP_ID']}&secret={creds['WECHAT_APP_SECRET']}")
    if "access_token" not in token_r:
        sys.exit(f"token 失败: {token_r}")
    token = token_r["access_token"]

    media_id = "k1zdMd1BWM6ypV0YZ7trD07NSynZ3-hT6INBxQyfQpY9ZdVPBlx_WG-G7nlU5kMy"

    print("① freepublish/submit 发布草稿……")
    r = http_json(f"{API}/freepublish/submit?access_token={token}",
                  data=json.dumps({"media_id": media_id}).encode("utf-8"),
                  headers={"Content-Type": "application/json; charset=utf-8"})
    print("   ->", r)

    print("\n② freepublish/batchget 查发布记录……")
    r2 = http_json(f"{API}/freepublish/batchget?access_token={token}",
                   data=json.dumps({"offset": 0, "count": 10, "no_content": 1}).encode("utf-8"),
                   headers={"Content-Type": "application/json; charset=utf-8"})
    if "item" in r2:
        for it in r2["item"]:
            arts = it.get("article_id", it)
            print(f"   发布记录 article_id={arts} 时间={it.get('update_time','')}")
    else:
        print("   ->", r2)


if __name__ == "__main__":
    main()
