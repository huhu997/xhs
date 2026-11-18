# -*- coding: utf-8 -*-
"""D2B: 2160x2880 PNG -> 1080x1440 JPG (explicit 1:1 mapping) + self-contained preview page."""
import os
import io
import base64
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "output")

MAP = [
    ("card1", "card1_封面.jpg"),
    ("card2", "card2_场景.jpg"),
    ("card3", "card3_四栏结构.jpg"),
    ("card4", "card4_可复制示例.jpg"),
    ("card5", "card5_钩子引导.jpg"),
]
TITLES = [
    "① 封面 · 一图看懂",
    "② 场景 · 重复交代的三句话",
    "③ 结构 · 4 栏矩阵",
    "④ 示例 · 可复制文本",
    "⑤ 钩子 · 扣【档案】",
]
DESCS = [
    "换 AI 不用重新交代自己 / 04 栏纯文字",
    "身份、要什么、怎么说话，各讲一遍",
    "只写稳定不变的，会变的留在对话里",
    "一段能直接复制的档案原文",
    "4 栏字段模板 + 示例，纯分享不卖课",
]


def main():
    for pid, jpg in MAP:
        png = os.path.join(SRC, pid + ".png")
        if not os.path.exists(png):
            raise FileNotFoundError(png)
        im = Image.open(png).convert("RGB").resize((1080, 1440), Image.LANCZOS)
        out = os.path.join(HERE, jpg)
        im.save(out, "JPEG", quality=92)
        print("JPG", jpg, im.size, os.path.getsize(out) // 1024, "KB")

    cards = []
    for (_, jpg), title, desc in zip(MAP, TITLES, DESCS):
        im = Image.open(os.path.join(HERE, jpg)).convert("RGB")
        im.thumbnail((430, 580), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82)
        b64 = base64.b64encode(buf.getvalue()).decode()
        cards.append('<div class="card"><div class="img"><img src="data:image/jpeg;base64,'
                     + b64 + '"></div><div class="cap"><b>' + title
                     + '</b><span>' + desc + '</span></div></div>')

    html = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>D2B 配图预览 · 跨 AI 共享个人档案</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:28px;background:#f5f5f7;color:#1d1d1f;
font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
h1{font-size:22px;margin:0 0 6px;font-weight:650}p.sub{margin:0 0 18px;color:#6e6e73;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px}
.card{background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.07);border:1px solid #e8e8ed}
.img{display:flex;justify-content:center;padding:10px}.img img{width:100%;max-width:430px;border-radius:8px;display:block}
.cap{padding:12px 14px 15px;display:flex;flex-direction:column;gap:4px;border-top:1px solid #f0f0f2}
.cap b{font-size:13px;font-weight:650}.cap span{font-size:11.5px;color:#6e6e73;line-height:1.5}
.tags{margin-bottom:18px}.tag{display:inline-block;background:#fff1ec;color:#e04a28;font-size:11px;
padding:4px 10px;border-radius:20px;margin-right:8px}
.note{background:#fff;border:1px solid #e8e8ed;border-radius:12px;padding:14px 16px;
font-size:12.5px;color:#3a3a3c;line-height:1.7;margin-bottom:20px}
</style></head><body>
<h1>薄肌小王 · D2B 配图（5 张，按上传顺序）</h1>
<p class="sub">一图看懂｜换 AI 不用重新交代自己 · 1080×1440 / 3:4 · guizang 瑞士风 safety-orange</p>
<div class="tags"><span class="tag">换选题</span><span class="tag">换形态</span><span class="tag">换视觉</span>
<span class="tag">0 编造体验</span><span class="tag">无串图</span></div>
<div class="note"><b>这版和前两篇错在哪：</b>选题改用「跨 AI 共享个人档案」（近期 6795 赞信号）；
形态是图解 / 结构拆解，不做观点论证、不给提示词清单；正文零数据论据、零人设自证、零连载提示；
视觉从 Apple 暖色圆角卡换成 guizang 瑞士网格方角卡。D1＝观点帖，D2＝实操帖，D2B＝结构图解帖。
<b>D2 与 D2B 是第 2 篇的二选一，不要两版都发。</b></div>
<div class="grid">""" + "".join(cards) + """</div></body></html>"""

    out = os.path.join(HERE, "配图预览_D2B.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("PREVIEW", out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
