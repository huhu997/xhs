#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「数据派财经快评」文案生成：喂当日数据 → DeepSeek 输出 标题/正文/核心数字 三元组
用法：python generate.py a.json us.json [--period 盘前|收盘]
"""
import argparse, json, os, pathlib, re, sys

import requests

def _load_env_file():
    """优先读 ~/.baoyu-skills/.env（与本包 news_publish.py 同源），失败则退回 os.environ。"""
    env_path = pathlib.Path.home() / ".baoyu-skills" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env_file()

def _k(*names):
    """按优先级取第一个非空环境变量，取不到返回空串（该 provider 会被自动跳过）。"""
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v
    return ""

# 密钥一律从环境变量 / ~/.baoyu-skills/.env 读取，禁止硬编码。
# 2026-11-05 脱敏：原文件曾在此处明文写死 4 个 key，已改为动态读取。
PROVIDERS = [
    {"name": "deepseek", "base": "https://api.deepseek.com/chat/completions", "model": "deepseek-chat", "key": _k("DEEPSEEK_API_KEY")},
    {"name": "qwen", "base": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", "model": "qwen-plus", "key": _k("QWEN_API_KEY", "DASHSCOPE_API_KEY")},
    {"name": "hunyuan", "base": "https://api.hunyuan.cloud.tencent.com/v1/chat/completions", "model": "hunyuan-pro", "key": _k("HUNYUAN_API_KEY")},
    {"name": "kimi", "base": "https://api.moonshot.cn/v1/chat/completions", "model": "kimi-k2-thinking-turbo", "key": _k("MOONSHOT_API_KEY", "KIMI_API_KEY")},
]
PROVIDERS = [p for p in PROVIDERS if p["key"]]
if not PROVIDERS:
    raise SystemExit("❌ 未读到任何模型 key：请在 ~/.baoyu-skills/.env 或环境变量中配置 "
                     "DEEPSEEK_API_KEY / QWEN_API_KEY / HUNYUAN_API_KEY / MOONSHOT_API_KEY 之一")

SYSTEM = """你是「数据派财经快评」公众号的写手，每天写 150-300 字的短评。

硬规则：
1. 你的价值 = 一眼点出今天数据里最值得注意的反差/异常（这是编辑价值，不是复述行情）。读者看你的原因是你"总能报出别人没注意到的数字和反差"。
2. 结构 = 反差开头（钩子，一句话点出反常）→ 支撑这个反差的事实细节（数据/走势）→ 结束（收在反差本身，不延伸建议）。
3. 选反差优先：盘中反转（先跌后涨/低开高走/高开低走）> 背离（A股vs美股、板块vs指数、个股之间）> 极端值（0跌停、涨停潮）> 单股异动。
4. 口语、像朋友转述行情，可以有"有意思/没想到/反着来/唯独"这类带信息量的点评词。
5. **红线（绝对禁止）**：①荐股——"该买/该卖/可以买/别追/上车"；②预测涨跌——"明天涨/明天跌/有望突破/要调整"；③无根据的主观判断——"资金乐观/情绪到顶/主力在跑/说明经济XX"（只允许"数据+数据"的客观对比）；④行动建议——"该盯/建议关注/别错过"。
6. 所有数字必须来自输入数据，一个都不能编；反差必须建立在真实数据上，不能为了反差编角度。
7. 全程中文。
8. 标题 ≤20 字，用事实反差做钩子（如"英伟达独跌1.59%，苹果微软却在涨"），不用感叹词、不评价。**如果主体是重大事件（财报/发布会/政策），标题必须带事件关键词**，如"英伟达财报亮眼，股价却独跌1.59%"——事件标题优先于纯涨跌数字标题。**涉及财报时段的措辞规范**：财报发布前的时段叫"收盘"（如"收盘跌1.59%"），财报发布后的叫"盘后"（如"盘后先跌3%再转涨"）；**禁止用"盘前/盘中"称呼财报时段**。标题可二选一突出重点（收盘跌 or 盘后反转），正文必须两段都写。
9. figure 是全文最核心的一个数字，格式"数字 单位"，封面要放大它。
10. 盘前：主体=隔夜美股/A50（含日内走势），A股昨日收盘一句参考，禁止复述成今日行情。
11. 一事为主：选一个反差展开，其他数据最多一句带过，禁止平铺罗列所有指数涨跌。
12. **重大事件最高优先**：如果"今日重要事件"里有财报/发布会/政策/并购等事件，**必须**把"事件 + 股价反应"作为主体。**股价反应要写完整时间线：事件前收盘价 + 事件后盘后变化，两个阶段都写**（如"财报前收盘跌1.59%，财报后盘后先跌3%再转涨"）——行情接口给的是事件前正常时段收盘价，新闻里的"盘后/盘中"描述是事件后反应，**缺一个都不完整**。写法：先给事件（财报/发布会内容+数据），再给"事件前收盘 → 事件后盘后变化"的完整股价反应，最后可对比其他标的。没有事件新闻时才用纯行情反差。
13. 结尾收在反差本身（一句话点破反常即可），**禁止重复标题原句**。

只输出一个 JSON，不要任何其他文字：
{"title":"标题","content":"正文（用\\n\\n分段，3-4段）","figure":"核心数字"}"""


def call_llm(system, user):
    last_err = None
    for p in PROVIDERS:
        try:
            payload = {"model": p["model"],
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": user}],
                       "temperature": 0.7}
            r = requests.post(p["base"], json=payload,
                              headers={"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"},
                              proxies={"http": None, "https": None}, timeout=120)
            r.raise_for_status()
            print(f"[LLM] 使用 {p['name']} ({p['model']})", file=sys.stderr)
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            last_err = e
            print(f"[LLM] {p['name']} 失败: {e}", file=sys.stderr)
    raise SystemExit(f"❌ 所有 LLM provider 都失败: {last_err}")


def _fmt_market(items):
    """把 {名: {最新价,涨跌幅%,开盘,最高,最低,昨收}} 渲染成带日内走势的一行"""
    parts = []
    for k, v in items.items():
        pct = v.get("涨跌幅%")
        op, hi, lo, last = v.get("开盘"), v.get("最高"), v.get("最低"), v.get("最新价")
        trend = ""
        if op is not None and last is not None and op and last:
            if last > op:
                trend = "（低开高走）"
            elif last < op:
                trend = "（高开低走）"
        parts.append(f"{k} {pct}%{trend}")
    return "、".join(parts)


def build_user(a_data, us_data, period, news_data=None):
    def idx(a):
        return ", ".join(f"{k} {v.get('涨跌幅%', v.get('收盘',''))}%" for k, v in a.get("indices", {}).items())

    lines = [f"今天是 {a_data.get('date','')}，写一条{period}快评。", ""]

    # 今日重要事件（最优先喂给 AI）
    if news_data and news_data.get("news"):
        lines.append("【今日重要事件/新闻（来源可靠，可作快评主题）】")
        for kw, items in news_data["news"].items():
            for it in items[:2]:
                lines.append(f"  [{it.get('时间','')}] {it.get('标题','')}｜{it.get('摘要','')[:60]}")
        lines.append("")

    if period == "盘前":
        # 盘前：主打隔夜美股新信息；A股昨日收盘只给一行指数参考，不给领涨板块/涨停（避免AI复述昨日）
        lines.append("【重点：隔夜美股（最新信息，含日内走势）】")
        if us_data.get("indices"):
            lines.append("  指数：" + _fmt_market(us_data["indices"]))
        if us_data.get("stocks"):
            lines.append("  个股：" + _fmt_market(us_data["stocks"]))
        lines.append("")
        lines.append("【A股昨日收盘，仅一句话参考，禁止展开复述】")
        if a_data.get("indices"):
            lines.append("  四大指数：" + idx(a_data))
    else:
        lines.append("【A股当日行情】")
        if a_data.get("indices"):
            lines.append("  四大指数：" + idx(a_data))
        if a_data.get("breadth"):
            b = a_data["breadth"]
            lines.append(f"  涨跌家数：上涨{b.get('上涨家数')} / 下跌{b.get('下跌家数')}")
        if a_data.get("limit"):
            l = a_data["limit"]
            lines.append(f"  涨停 {l.get('涨停')} 家 / 跌停 {l.get('跌停')} 家")
            if l.get("涨停代表"):
                lines.append("  涨停代表：" + ", ".join(x["名称"] for x in l["涨停代表"]))
        if a_data.get("sectors"):
            s = a_data["sectors"]
            lines.append("  领涨板块：" + ", ".join(f"{x['名称']}+{x['涨跌幅%']}%" for x in s.get("领涨", [])))
            lines.append("  领跌板块：" + ", ".join(f"{x['名称']}{x['涨跌幅%']}%" for x in s.get("领跌", [])))

    if period != "盘前" and us_data.get("indices"):
        lines.append("")
        lines.append("隔夜美股：")
        lines.append("  指数：" + ", ".join(f"{k} {v.get('涨跌幅%')}%" for k, v in us_data["indices"].items()))
        if us_data.get("stocks"):
            lines.append("  个股：" + ", ".join(f"{k} {v.get('涨跌幅%')}%" for k, v in us_data["stocks"].items()))
    lines.append("")
    lines.append("请输出 JSON。")
    return "\n".join(lines)


def parse(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise SystemExit(f"❌ 输出不是 JSON: {raw[:200]}")
    return json.loads(m.group(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a_data", help="A股数据 JSON 路径")
    ap.add_argument("us_data", help="美股数据 JSON 路径")
    ap.add_argument("--period", default="收盘", choices=["盘前", "收盘", "盘中"])
    ap.add_argument("--news", default=None, help="今日新闻 JSON 路径（可选）")
    args = ap.parse_args()

    a = json.loads(pathlib.Path(args.a_data).read_text(encoding="utf-8"))
    u = json.loads(pathlib.Path(args.us_data).read_text(encoding="utf-8"))
    n = json.loads(pathlib.Path(args.news).read_text(encoding="utf-8")) if args.news and pathlib.Path(args.news).exists() else None
    user = build_user(a, u, args.period, n)
    raw = call_llm(SYSTEM, user)
    out = parse(raw)
    out["period"] = args.period
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
