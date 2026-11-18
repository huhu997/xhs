# -*- coding: utf-8 -*-
"""
从定稿 markdown 生成公众号可用 HTML（内联样式，无外链）。
主题：财经严肃 #0E2A47 / 报表纸 #F4F1EA / 旧金 #C8A24B
数据色：涨 #D9462B / 跌 #2E7D5B / 中性 #8B8577
"""
import re
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "04-article-edited.md")

INK = "#0E2A47"
PAPER = "#F4F1EA"
GOLD = "#C8A24B"
UP = "#D9462B"
DOWN = "#2E7D5B"
MUTE = "#8B8577"
TEXT = "#26262B"

text = open(SRC, encoding="utf-8").read()
lines = [l.rstrip("\n") for l in text.split("\n")]

blocks = []
i = 0
while i < len(lines):
    l = lines[i]
    s = l.strip()
    if not s:
        i += 1
        continue
    if s.startswith("# "):
        blocks.append(("h1", s[2:].strip()))
    elif s.startswith("## "):
        blocks.append(("h2", s[3:].strip()))
    elif s.startswith("> "):
        blocks.append(("meta", s[2:].strip()))
    elif s == "---":
        blocks.append(("hr", ""))
    else:
        blocks.append(("p", s))
    i += 1

# 把开篇三行数据合并成一个看板
DATA_MARKS = ("上涨 4869", "涨停 84 只", "昨天封住涨停的票，今天 95 只")
merged = []
buf = []
for kind, val in blocks:
    if kind == "p" and val.startswith(DATA_MARKS):
        buf.append(val)
        continue
    if buf:
        merged.append(("data", buf))
        buf = []
    merged.append((kind, val))
if buf:
    merged.append(("data", buf))
blocks = merged

# hr 之后的三段当作免责区
hr_idx = next((n for n, (k, v) in enumerate(blocks) if k == "hr"), None)
if hr_idx is not None:
    blocks = blocks[:hr_idx] + [("hr", "")] + [
        ("foot", v) if k == "p" else (k, v) for k, v in blocks[hr_idx + 1:]
    ]


def strong(s, words):
    for w in words:
        if w in s:
            s = s.replace(w, '<strong style="font-weight:600;color:%s;">%s</strong>' % (INK, w), 1)
    return s


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cell(label, num, color, sub=""):
    subhtml = (
        '<div style="font-size:11px;line-height:1.5;color:%s;margin-top:2px;">%s</div>' % (MUTE, sub)
        if sub
        else ""
    )
    return (
        '<td style="padding:12px 6px;text-align:center;vertical-align:middle;">'
        '<div style="font-size:11px;letter-spacing:1px;color:%s;margin-bottom:4px;">%s</div>'
        '<div style="font-size:26px;line-height:1.1;font-weight:700;color:%s;'
        'font-family:Georgia,\'Times New Roman\',serif;">%s</div>%s</td>'
        % (MUTE, label, color, num, subhtml)
    )


def render_data(vals):
    a = esc(vals[0]) if len(vals) > 0 else ""
    b = esc(vals[1]) if len(vals) > 1 else ""
    c = esc(vals[2]) if len(vals) > 2 else ""
    row1 = (
        "<tr>"
        + cell("上涨", "4869", UP)
        + cell("下跌", "624", DOWN)
        + cell("平盘", "80", MUTE)
        + "</tr>"
    )
    row2 = (
        "<tr>"
        + cell("涨停", "84", UP)
        + cell("跌停", "0", MUTE)
        + cell("封板次日", "95", UP, "116 只样本中")
        + "</tr>"
    )
    return (
        '<section style="margin:22px 0 26px;">'
        '<section style="border:1px solid rgba(14,42,71,0.14);border-radius:4px;'
        'background:#FFFDF7;overflow:hidden;">'
        '<section style="padding:9px 14px;background:rgba(200,162,75,0.10);'
        'border-bottom:1px solid rgba(14,42,71,0.10);font-size:11px;'
        'letter-spacing:2px;color:%s;">2026.11.05　收盘读数</section>'
        '<table style="width:100%%;border-collapse:collapse;table-layout:fixed;">%s%s</table>'
        "</section>"
        '<section style="margin-top:8px;font-size:11px;line-height:1.6;color:%s;">'
        "涨跌家数为逐股扫描口径（5927 只扫描池，5573 只有价格）。涨停 84 只，跌停 0 只（收盘封板口径）。"
        "</section></section>"
    ) % (GOLD, row1, row2, MUTE)


body = []
for kind, val in blocks:
    if kind == "h1":
        body.append(
            '<h1 style="margin:0 0 18px;font-size:27px;line-height:1.42;font-weight:700;'
            'color:%s;letter-spacing:.5px;'
            "font-family:'Noto Serif SC','Songti SC',Georgia,serif;\">%s</h1>" % (INK, esc(val))
        )
    elif kind == "meta":
        body.append(
            '<section style="margin:0 0 30px;padding-bottom:14px;'
            'border-bottom:2px solid %s;">'
            '<span style="font-size:12px;letter-spacing:2px;color:%s;">%s</span></section>'
            % (GOLD, MUTE, esc(val))
        )
    elif kind == "h2":
        if val.startswith("三、"):
            body.append(
                '<section style="margin:30px 0 8px;">'
                '<img src="08-illustration.png" alt="同一天里，防守端在跌、进攻端在涨" '
                'style="display:block;width:100%;height:auto;'
                'border:1px solid rgba(14,42,71,0.10);" />'
                '<section style="margin-top:9px;font-size:11px;line-height:1.6;color:' + MUTE + ';">'
                "2026-11-05 收盘，行业／概念板块指数口径；左右两栏同一比例尺。"
                "</section></section>"
            )
        body.append(
            '<section style="margin:36px 0 16px;padding-left:11px;border-left:3px solid %s;">'
            '<span style="font-size:18px;font-weight:700;color:%s;line-height:1.5;'
            "font-family:'Noto Serif SC','Songti SC',Georgia,serif;\">%s</span></section>"
            % (GOLD, INK, esc(val))
        )
    elif kind == "data":
        body.append(render_data(val))
    elif kind == "p":
        body.append(
            '<p style="margin:0 0 19px;font-size:16px;line-height:1.92;color:%s;'
            'letter-spacing:.3px;text-align:justify;">%s</p>'
            % (TEXT, strong(esc(val), ["4869", "624", "81.9%", "95 只", "4.42%"]))
        )
    elif kind == "hr":
        body.append(
            '<section style="margin:34px 0 22px;height:1px;background:rgba(14,42,71,0.16);"></section>'
        )
    elif kind == "foot":
        body.append(
            '<p style="margin:0 0 13px;font-size:12px;line-height:1.85;color:%s;'
            'letter-spacing:.2px;text-align:justify;">%s</p>' % (MUTE, esc(val))
        )

inner = "\n".join(body)

# 公众号会自动加标题，粘贴版去掉 h1 避免重复
inner_paste = re.sub(r"<h1[^>]*>.*?</h1>", "", inner, count=1)

paste = (
    '<section style="max-width:677px;margin:0 auto;padding:26px 20px 10px;'
    'background:%s;color:%s;font-size:16px;line-height:1.9;">\n%s\n</section>'
    % (PAPER, TEXT, inner_paste)
)

open(os.path.join(BASE, "08-article-paste.html"), "w", encoding="utf-8").write(paste)

preview = (
    '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    "<title>昨天封板的票，今天八成还在涨</title></head>"
    '<body style="margin:0;padding:0;background:#E7E2D6;">'
    '<section style="max-width:717px;margin:0 auto;padding:30px 0 40px;">'
    '<section style="max-width:677px;margin:0 auto;padding:34px 20px 10px;'
    'background:%s;color:%s;font-size:16px;line-height:1.9;">%s</section>'
    "</section></body></html>" % (PAPER, TEXT, inner)
)
open(os.path.join(BASE, "08-article.html"), "w", encoding="utf-8").write(preview)

print("written paste=%d preview=%d" % (len(paste), len(preview)))
