# -*- coding: utf-8 -*-
"""隔夜美股数据采集：道指/纳指/标普/费半 + 核心个股（东财公开接口）
用法：python fetch_us.py          # 输出 JSON 到 stdout
      python fetch_us.py -o us.json
"""
import argparse, json, sys
from datetime import datetime

import requests

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/116.0",
    "Referer": "https://data.eastmoney.com/",
}

# 美股指数 / 核心个股 secid（东财）
US_INDEX_SECIDS = {
    "道琼斯": "100.DJIA",
    "纳斯达克": "100.NDX",
    "标普500": "100.SPX",
    "富时中国A50": "100.XIN9",
}
US_STOCK_SECIDS = {
    "英伟达": "105.NVDA",
    "苹果": "105.AAPL",
    "特斯拉": "105.TSLA",
    "微软": "105.MSFT",
}


def _get(url, timeout=10):
    r = requests.get(url, headers=_HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch(secids_map):
    secids = ",".join(secids_map.values())
    d = _get(
        f"https://push2delay.eastmoney.com/api/qt/ulist.np/get"
        f"?fltt=2&secids={secids}&fields=f2,f3,f15,f16,f12,f14,f17,f18"
    ).get("data", {}).get("diff", [])
    result = {}
    for x in d or []:
        name = x.get("f14", "")
        result[name] = {
            "最新价": x.get("f2"),
            "涨跌幅%": x.get("f3"),
            "最高": x.get("f15"),
            "最低": x.get("f16"),
            "开盘": x.get("f17"),
            "昨收": x.get("f18"),
        }
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--output", default=None)
    args = p.parse_args()

    data = {
        "date": datetime.now().strftime("%Y%m%d"),
        "indices": fetch(US_INDEX_SECIDS),
        "stocks": fetch(US_STOCK_SECIDS),
        "source": "东方财富 push2delay 美股接口",
    }
    out = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[完成] 已写入: {args.output}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
