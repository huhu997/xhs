#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A 股盘面数据多源核对器（新浪指数 + 腾讯交叉 + 东财全市场逐股扫描）

来源：zcode工作区/articles/20260928-jiehou-kaimen/verify_data.py（9/28 实盘验证过的口径），
本版只做两件事：① 日期参数化 ② 输出路径可指定。数据口径与判定阈值一字未改。

口径要点（与稿子里的数字必须同源）：
  - 涨跌家数：东财全市场逐股 f3 字段扫描，分页 100×70 页
  - 涨跌停判定：主板 ±9.7% / 创业板与科创板 ±19.7% / 北交所 ±29.7%
  - 涨停池 tc 用东财 getTopicZTPool 的 tc 字段（与逐股扫描口径可能差几只，用时注明哪个口径）

用法：
    python market_verify.py                       # 今天
    python market_verify.py --date 20261105       # 指定日
    python market_verify.py --date 20261105 --out v.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import urllib.request

urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/116.0"}
UT = "7eea3edcaed734bea9cbfc24409ed989"
OUT: dict = {}


def get(url: str, headers: dict | None = None, encoding: str = "utf-8") -> str:
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode(encoding, "ignore")


def zt_pool(date: str, api: str = "getTopicZTPool", sort: str = "fbt%3Aasc") -> dict | None:
    try:
        r = json.loads(get(
            f"https://push2ex.eastmoney.com/{api}?ut={UT}&dpt=wz.ztzt"
            f"&Pageindex=0&pagesize=500&sort={sort}&date={date}"))
        return r.get("data")
    except Exception:
        return None


def find_prev(date: str, max_back: int = 12) -> str:
    """从 date 往前找最近一个有涨停池数据的交易日（跳过周末与节假日）。"""
    d = dt.datetime.strptime(date, "%Y%m%d").date()
    for i in range(1, max_back + 1):
        p = d - dt.timedelta(days=i)
        if p.weekday() >= 5:
            continue
        s = p.strftime("%Y%m%d")
        data = zt_pool(s)
        if data and data.get("tc"):
            return s
    return ""


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="A 股盘面数据多源核对")
    ap.add_argument("--date", default=None, help="交易日 YYYYMMDD，默认今天")
    ap.add_argument("--prev", default=None, help="上一交易日，默认自动往前找")
    ap.add_argument("--out", default=None, help="结果 JSON 输出路径，默认同目录 verify.json")
    ap.add_argument("--quiet", action="store_true", help="只写文件不打印")
    a = ap.parse_args()

    DATE = a.date or dt.datetime.now().strftime("%Y%m%d")
    PREV = a.prev or find_prev(DATE)
    OUT["_date"] = DATE
    OUT["_prev"] = PREV or "(未找到)"
    print(f"=== 核对日 {DATE} / 上一交易日 {PREV or '未找到'} ===", flush=True)

    # 1. 新浪指数（含成交额，万元）
    try:
        txt = get("https://hq.sinajs.cn/list=s_sh000001,s_sz399001,s_sz399006,s_sh000688,s_bj899050",
                  headers={"Referer": "https://finance.sina.com.cn"}, encoding="gbk")
        sina = {}
        for line in txt.strip().split("\n"):
            if "=" not in line:
                continue
            code = line.split("=")[0].split("_")[-1]
            parts = line.split('"')[1].split(",")
            if len(parts) >= 6:
                sina[code] = {"名称": parts[0], "收盘": float(parts[1]), "涨跌幅%": float(parts[3]),
                              "成交额亿": round(float(parts[5]) / 1e4, 2)}
        OUT["sina"] = sina
        if "000001" in sina and "399001" in sina:
            OUT["两市成交额亿"] = round(sina["000001"]["成交额亿"] + sina["399001"]["成交额亿"], 0)
    except Exception as e:
        OUT["sina_err"] = str(e)

    # 2. 腾讯交叉
    try:
        txt = get("https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688", encoding="gbk")
        tx = {}
        for line in txt.strip().split(";"):
            if "~" not in line:
                continue
            p = line.split('"')[1].split("~")
            tx[p[2]] = {"名称": p[1], "收盘": float(p[3]), "涨跌幅%": float(p[32])}
        OUT["tencent"] = tx
    except Exception as e:
        OUT["tencent_err"] = str(e)

    # 3. 全市场逐股扫描：涨跌家数 + 涨跌停
    try:
        rows = []
        for pn in range(1, 70):
            d = json.loads(get(
                "https://push2delay.eastmoney.com/api/qt/clist/get"
                f"?pn={pn}&pz=100&po=1&np=1&fltt=2&invt=2&fid=f3"
                "&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048&fields=f3,f12,f14")).get("data")
            if not d or not d.get("diff"):
                break
            rows.extend(d["diff"])
            if len(d["diff"]) < 100:
                break
        up = sum(1 for x in rows if isinstance(x.get("f3"), (int, float)) and x["f3"] > 0)
        dn = sum(1 for x in rows if isinstance(x.get("f3"), (int, float)) and x["f3"] < 0)
        flat = sum(1 for x in rows if x.get("f3") == 0)
        lim_up, lim_dn = [], []
        for x in rows:
            c, f3 = str(x.get("f12", "")), x.get("f3")
            if not isinstance(f3, (int, float)):
                continue
            is20 = c.startswith(("30", "68"))
            isbj = c.startswith(("8", "4", "92"))
            thr = 19.7 if is20 else (29.7 if isbj else 9.7)
            if f3 >= thr:
                lim_up.append(x.get("f14"))
            if f3 <= -thr:
                lim_dn.append(x.get("f14"))
        OUT["breadth"] = {"样本": len(rows), "上涨": up, "下跌": dn, "平盘": flat,
                          "涨停(≥阈值)": len(lim_up), "跌停(≥阈值)": len(lim_dn),
                          "_口径": "东财全市场逐股 f3 扫描"}
    except Exception as e:
        OUT["breadth_err"] = str(e)

    # 4. 东财涨跌停池（tc 口径）
    for tag, api, sort in [("zt_pool", "getTopicZTPool", "fbt%3Aasc"),
                           ("dt_pool", "getTopicDTPool", "fund%3Aasc")]:
        d = zt_pool(DATE, api, sort)
        if d is None:
            OUT[tag + "_err"] = "接口无返回"
            continue
        pool = d.get("pool") or []
        OUT[tag] = {"tc": d.get("tc"),
                    "前8": [{"n": x.get("n"), "c": x.get("c"), "zdp": round(x.get("zdp", 0), 2),
                             "连板": x.get("lbc")} for x in pool[:8]],
                    "连板分布": {str(k): sum(1 for x in pool if x.get("lbc") == k) for k in
                             sorted({x.get("lbc") for x in pool if isinstance(x.get("lbc"), int)})}}

    # 5. 上一交易日涨停股 → 当日表现
    if PREV:
        try:
            d = zt_pool(PREV)
            pool = (d or {}).get("pool") or []
            codes = [str(x.get("c")) for x in pool]
            OUT["昨日涨停数"] = len(codes)
            perf = []
            for i in range(0, len(codes), 50):
                batch = codes[i:i + 50]
                q = ",".join(("sh" if c.startswith(("6", "9")) else "sz") + c for c in batch)
                txt = get(f"https://qt.gtimg.cn/q={q}", encoding="gbk")
                for line in txt.strip().split(";"):
                    if "~" not in line:
                        continue
                    p = line.split('"')[1].split("~")
                    if len(p) > 32:
                        try:
                            perf.append({"n": p[1], "c": p[2], "zdp": float(p[32])})
                        except Exception:
                            pass
            if perf:
                ups = [x for x in perf if x["zdp"] > 0]
                zts = [x for x in perf if x["zdp"] >= 9.7]
                perf_sorted = sorted(perf, key=lambda x: -x["zdp"])
                mid = sorted(x["zdp"] for x in perf)[len(perf) // 2]
                OUT["昨日涨停今日表现"] = {
                    "样本": len(perf), "上涨家数": len(ups),
                    "上涨占比%": round(100 * len(ups) / len(perf), 1),
                    "再涨停(≥9.7%)": len(zts), "涨幅中位数%": round(mid, 2),
                    "前5": perf_sorted[:5], "后5": perf_sorted[-5:],
                    "平均涨幅%": round(sum(x["zdp"] for x in perf) / len(perf), 2)}
        except Exception as e:
            OUT["zt_perf_err"] = str(e)

    # 6. 板块（行业+概念 升/降序头部）
    def boards(fs: str, n: int = 12) -> dict:
        out = {}
        for tag, po in [("领涨", 1), ("领跌", 0)]:
            try:
                d = json.loads(get(
                    "https://push2delay.eastmoney.com/api/qt/clist/get"
                    f"?pn=1&pz={n}&np=1&fltt=2&invt=2&fid=f3&po={po}&fs={fs}&fields=f3,f14")).get("data", {}).get("diff", [])
                out[tag] = [{"名称": x.get("f14"), "涨跌幅%": x.get("f3")} for x in d]
            except Exception as e:
                out[tag] = str(e)
        return out

    OUT["industry"] = boards("m:90+t:2", 12)
    OUT["concept"] = boards("m:90+t:3", 12)

    # 7. 行业主力净流入 Top/Bottom
    try:
        d = json.loads(get(
            "https://push2delay.eastmoney.com/api/qt/clist/get"
            "?pn=1&pz=200&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t:2&fields=f14,f3,f62")).get("data", {}).get("diff", [])
        rows2 = sorted([x for x in d if isinstance(x.get("f62"), (int, float))], key=lambda x: -x["f62"])
        OUT["flow_in"] = [{"名称": x["f14"], "涨跌幅%": x["f3"], "净流入亿": round(x["f62"] / 1e8, 2)} for x in rows2[:8]]
        OUT["flow_out"] = [{"名称": x["f14"], "涨跌幅%": x["f3"], "净流入亿": round(x["f62"] / 1e8, 2)} for x in rows2[-6:]]
    except Exception as e:
        OUT["flow_err"] = str(e)

    # 8. 隔夜美股
    try:
        txt = get("https://hq.sinajs.cn/list=gb_dji,gb_ixic,gb_inx,gb_nvda,gb_aapl,gb_msft,gb_tsla,gb_sox,gb_intc",
                  headers={"Referer": "https://finance.sina.com.cn"})
        us = {}
        for line in txt.strip().split("\n"):
            if '"' not in line:
                continue
            code = line.split("=")[0].split("_")[-1]
            p = line.split('"')[1].split(",")
            if len(p) > 2:
                us[code] = {"名称": p[0], "最新价": p[1], "涨跌幅%": p[2]}
        OUT["us"] = us
    except Exception as e:
        OUT["us_err"] = str(e)

    out_path = pathlib.Path(a.out) if a.out else pathlib.Path(__file__).resolve().parent / "verify.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(OUT, ensure_ascii=False, indent=2), encoding="utf-8")

    if not a.quiet:
        print(json.dumps(OUT, ensure_ascii=False, indent=1))
    print(f"\n✓ 已写入 {out_path}", flush=True)

    # 一致性自检：逐股扫描 vs 涨停池 tc
    b = OUT.get("breadth") or {}
    zt_tc = (OUT.get("zt_pool") or {}).get("tc")
    dt_tc = (OUT.get("dt_pool") or {}).get("tc")
    if b and zt_tc is not None:
        print(f"口径对照：逐股扫描 涨停 {b.get('涨停(≥阈值)')} / 跌停 {b.get('跌停(≥阈值)')}  "
              f"| 东财池 tc 涨停 {zt_tc} / 跌停 {dt_tc}", flush=True)
        print("  ⚠ 两个口径可能差几只，稿子里只用一套并注明来源。", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
