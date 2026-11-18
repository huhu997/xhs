#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「数据派财经快评」编排：数据采集 → AI 生成 → 封面+投递（一条全自动）
用法：python run_daily.py [盘前|盘中|收盘]   （默认收盘）
"""
import json, pathlib, subprocess, sys
from datetime import datetime

BASE = pathlib.Path("F:/桌面/zcode工作区/_wx_read")
PY = "C:/Program Files (x86)/python3.12/python.exe"
FETCH_A = "F:/桌面/zcode工作区/.zcode/skills/公众号文章创作/scripts/fetch-market-data.py"


def step(cmd, *args):
    subprocess.run([PY, str(cmd), *args], cwd=BASE, check=True)


def main():
    period = sys.argv[1] if len(sys.argv) > 1 else "收盘"
    if datetime.now().weekday() >= 5:
        print("周末休市，跳过。")
        return
    print(f"=== 快评流水线启动（{period}）===")

    print("[1/3] 采集 A股 + 美股 + 新闻数据...")
    step(FETCH_A, "-o", "today.json", "--quiet")
    step("fetch_us.py", "-o", "us.json")
    step("fetch_news.py", "-o", "news.json")

    print("[2/3] AI 生成快评...")
    r = subprocess.run([PY, "generate.py", "today.json", "us.json", "--period", period, "--news", "news.json"],
                       cwd=BASE, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"❌ 生成失败:\n{r.stderr}")
    gen = json.loads(r.stdout)
    print(f"    标题: {gen['title']}")
    print(f"    核心数字: {gen['figure']}")

    print("[3/3] 生成封面 + 投草稿箱...")
    import news_publish
    result = news_publish.publish(gen["title"], gen["content"], gen["figure"])
    print("投递结果:", result)
    if "media_id" in result:
        print(f"\n✅ 快评草稿已入箱 media_id={result['media_id']}")
        print("   去 mp.weixin.qq.com → 草稿箱 检查后点发布")


if __name__ == "__main__":
    main()
