# -*- coding: utf-8 -*-
"""9/28 盘面数据多源独立核实（新浪+腾讯+东财全市场逐股扫描+昨日涨停股今日表现+板块/资金流+美股）"""
import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/116.0"}
UT = "7eea3edcaed734bea9cbfc24409ed989"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = {}


def get(url, headers=None, encoding="utf-8"):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode(encoding, "ignore")


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
                      "涨停(≥阈值)": len(lim_up), "跌停(≥阈值)": len(lim_dn)}
except Exception as e:
    OUT["breadth_err"] = str(e)

# 4. 东财涨跌停池（tc 口径）+ 昨日涨停池（9/16）
for tag, api, sort, date in [
    ("zt_pool_today", "getTopicZTPool", "fbt%3Aasc", "20260928"),
    ("dt_pool_today", "getTopicDTPool", "fund%3Aasc", "20260928"),
]:
    try:
        d = json.loads(get(
            f"https://push2ex.eastmoney.com/{api}?ut={UT}&dpt=wz.ztzt"
            f"&Pageindex=0&pagesize=500&sort={sort}&date={date}")).get("data") or {}
        pool = d.get("pool") or []
        OUT[tag] = {"tc": d.get("tc"),
                    "前8": [{"n": x.get("n"), "c": x.get("c"), "zdp": round(x.get("zdp", 0), 2),
                             "连板": x.get("lbc")} for x in pool[:8]],
                    "连板分布": {str(k): sum(1 for x in pool if x.get("lbc") == k) for k in
                             sorted({x.get("lbc") for x in pool if isinstance(x.get("lbc"), int)})}}
    except Exception as e:
        OUT[tag + "_err"] = str(e)

# 5. 昨日（9/25）涨停股 → 今日（9/28）表现
try:
    d = json.loads(get(
        f"https://push2ex.eastmoney.com/getTopicZTPool?ut={UT}&dpt=wz.ztzt"
        f"&Pageindex=0&pagesize=500&sort=fbt%3Aasc&date=20260925")).get("data") or {}
    pool = d.get("pool") or []
    codes = [str(x.get("c")) for x in pool]
    OUT["昨日涨停数"] = len(codes)
    # 腾讯批量报价（分批 50 只）
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
            "样本": len(perf), "上涨家数": len(ups), "上涨占比%": round(100 * len(ups) / len(perf), 1),
            "再涨停(≥9.7%)": len(zts), "涨幅中位数%": round(mid, 2),
            "前5": perf_sorted[:5], "后5": perf_sorted[-5:],
            "平均涨幅%": round(sum(x["zdp"] for x in perf) / len(perf), 2)}
except Exception as e:
    OUT["zt_perf_err"] = str(e)

# 6. 板块（行业+概念 升/降序头部）
def boards(fs, n=12):
    out = {}
    for tag, po in [("领涨", 1), ("领跌", 0)]:
        try:
            d = json.loads(get(
                f"https://push2delay.eastmoney.com/api/qt/clist/get"
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

# 8. 关注板块（旅游/消费/港口/广西/农业等）
try:
    allb = []
    for fs, label in [("m:90+t:2", "行业"), ("m:90+t:3", "概念")]:
        d = json.loads(get(
            "https://push2delay.eastmoney.com/api/qt/clist/get"
            f"?pn=1&pz=500&np=1&fltt=2&invt=2&fid=f3&po=1&fs={fs}&fields=f3,f14,f62,f104,f105")).get("data", {}).get("diff", [])
        for x in d:
            x["_src"] = label
        allb.extend(d)
    keys = ["旅游", "酒店", "景点", "免税", "餐饮", "航空", "机场", "港口", "航运", "广西", "北部湾", "东盟",
            "基建", "水泥", "物流", "白酒", "食品", "零售", "影视", "短剧", "传媒", "游戏", "农业", "化肥",
            "数字乡村", "土地", "黄金", "白银", "稀土永磁", "半导体", "存储", "光模块", "CPO", "消费电子"]
    watch = []
    for x in allb:
        n = str(x.get("f14", ""))
        if any(k in n for k in keys):
            watch.append({"名称": n, "类型": x["_src"], "涨跌幅%": x.get("f3"),
                          "净流入亿": round(x["f62"] / 1e8, 2) if isinstance(x.get("f62"), (int, float)) else None,
                          "上涨家数": x.get("f104"), "下跌家数": x.get("f105")})
    OUT["watch_boards"] = sorted(watch, key=lambda x: -(x["涨跌幅%"] if isinstance(x["涨跌幅%"], (int, float)) else -99))
except Exception as e:
    OUT["watch_err"] = str(e)

# 9. 隔夜美股
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

with open(os.path.join(HERE, "verify.json"), "w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=2)
print(json.dumps(OUT, ensure_ascii=False, indent=1))
