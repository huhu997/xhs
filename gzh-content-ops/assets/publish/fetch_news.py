# -*- coding: utf-8 -*-
"""重大事件/新闻抓取：按预置重点关键词搜东财新闻，输出当天标题+摘要+时间
用法：python fetch_news.py [-o news.json]
"""
import argparse, json, re, sys, urllib.parse, urllib.request
from datetime import datetime

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://so.eastmoney.com/",
}
SEARCH_URL = "https://search-api-web.eastmoney.com/search/jsonp"

# 预置重点关键词（可增删）
KEYWORDS = ["英伟达", "苹果", "特斯拉", "微软", "美联储", "A50", "阿里", "台积电"]


def search(keyword, pagesize=4):
    param = {"uid": "", "keyword": keyword, "type": ["cmsArticleWebOld"],
             "pageSize": pagesize, "pageIndex": 1}
    param_str = json.dumps(param, ensure_ascii=False, separators=(",", ":"))
    url = f"{SEARCH_URL}?cb=cb&param={urllib.parse.quote(param_str, safe='')}"
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        text = r.read().decode("utf-8", "ignore")
    m = re.search(r"^[^(]*\((.*)\)\s*$", text, re.S)
    if not m:
        return []
    data = json.loads(m.group(1))
    items = data.get("result", {}).get("cmsArticleWebOld", []) or []
    today = datetime.now().strftime("%Y-%m-%d")
    out = []
    for it in items:
        date = it.get("date", "")
        if not date.startswith(today):
            continue
        title = re.sub(r"</?em>", "", it.get("title", ""))
        content = re.sub(r"</?em>", "", it.get("content", ""))
        out.append({
            "时间": date[11:16],
            "标题": title,
            "摘要": content[:120],
            "来源": it.get("mediaName", ""),
        })
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--output", default=None)
    args = p.parse_args()

    news = {}
    for kw in KEYWORDS:
        try:
            items = search(kw)
            if items:
                news[kw] = items
        except Exception as e:
            print(f"[fetch_news] {kw} 失败: {e}", file=sys.stderr)

    data = {"date": datetime.now().strftime("%Y%m%d"), "news": news}
    out = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[完成] 新闻已写入: {args.output}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
