#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成投前预览：画廊预览.html（10图一览+封面双裁剪模拟）+ 公众号预览.html（手机宽度全文）
用法: python make_previews.py
"""
import pathlib, sys

BASE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import upload_article as ua

ACCENT, LINE = "#2E6B4F", "#DAD3C4"
GALLERY = """<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8">
<title>画廊预览 · 9/23 复盘</title>
<style>
body{background:#EDE8DC;font-family:"Microsoft YaHei UI","Microsoft YaHei",sans-serif;margin:0;padding:28px 34px;color:#16251B}
h1{font-size:22px;margin:0 0 6px}
.meta{font-size:13px;color:#5A5A54;margin-bottom:22px}
.grid{display:flex;flex-wrap:wrap;gap:18px}
.cell{width:calc(50% - 9px);background:#fff;border:1.5px solid #DAD3C4}
.cell .cap{font-size:13px;font-weight:700;padding:9px 12px;border-bottom:1.5px solid #DAD3C4;color:#2E6B4F}
.cell img{width:100%;display:block}
.crops{display:flex;gap:18px;margin-top:24px}
.crop{background:#fff;border:1.5px solid #DAD3C4;padding:0}
.crop .t{font-size:13px;font-weight:700;padding:9px 12px;border-bottom:1.5px solid #DAD3C4;color:#2E6B4F}
.crop .box{overflow:hidden;position:relative;background:#F5F1E8}
.crop .box img{position:absolute;display:block}
.w235{width:__W235__px;height:__H235__px}
.w235 img{width:__W235__px;left:0;top:__T235__px}
.w11{width:300px;height:300px}
.w11 img{width:__W11__px;left:__L11__px;top:0}
</style></head><body>
<h1>A股每日复盘 · 2026.09.23 · 配图一览（forest-ink）</h1>
<div class="meta">10 张 · Gemini 生图 / HTML 直出 · A股红涨绿跌 · 数据：2026-09-23 收盘多源核实</div>
<div class="grid">
__CELLS__
</div>
<h1 style="margin-top:34px;font-size:19px;">封面裁剪模拟（公众号大图/小图）</h1>
<div class="crops">
  <div class="crop"><div class="t">2.35:1 中心横带（pic_crop_235_1）</div>
    <div class="box w235"><img src="cover.png"></div></div>
  <div class="crop"><div class="t">1:1 中心方块（pic_crop_1_1）</div>
    <div class="box w11"><img src="cover.png"></div></div>
</div>
</body></html>"""

CAPS = {
    "cover": "cover · 封面：1.76万亿 / 51家涨停 / -0.39% / 缩量退潮，方向不变",
    "data": "data · 数据总览（缩量普跌，只有一处逆势）",
    "verify": "verify · 昨日观察点回看（2应验 / 1一半 / 1未兑现）",
    "money": "money · 资金去向（昨天涨的今天跌，昨天跌的今天涨）",
    "chain": "chain · 今天的三条链（换座位的第二回合）",
    "clues": "clues · 换个视角：四条辅助线索",
    "ebb": "ebb · 今天退潮的三个刻度（涨停/跌停/最高板）",
    "outlook": "outlook · 明日观察点（4条可量化）",
    "share": "share · 赞转引导",
}

PHONE = """<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8">
<title>公众号预览 · 9/23 复盘</title>
<style>
body{background:#EDE8DC;font-family:"Microsoft YaHei UI","Microsoft YaHei",sans-serif;margin:0;padding:24px;display:flex;justify-content:center;gap:26px;align-items:flex-start}
.phone{width:420px;background:#FFFFFF;border:1.5px solid #D6D0C0;padding:0;box-shadow:0 2px 10px rgba(0,0,0,.08)}
.phone .topbar{background:#2E6B4F;color:#fff;padding:12px 16px;font-size:13px;font-weight:700}
.phone .inner{padding:18px 16px}
.title{font-size:20px;font-weight:900;line-height:1.4;margin:0 0 10px}
.digest{font-size:13px;color:#5A5A54;line-height:1.7;border-left:3px solid #DAD3C4;padding-left:10px;margin-bottom:16px}
.coverwrap{margin-bottom:16px}
.coverwrap .lb{font-size:12px;color:#5A5A54;margin:14px 0 6px}
.c235{width:388px;height:__H235p__px;overflow:hidden;position:relative;background:#F5F1E8}
.c235 img{position:absolute;width:388px;left:0;top:__T235p__px}
.c11w{width:200px;height:200px;overflow:hidden;position:relative;background:#F5F1E8}
.c11w img{position:absolute;width:__W11p__px;left:__L11p__px;top:0}
.meta{font-size:12px;color:#5A5A54;margin-top:8px}
</style></head><body>
<div class="phone">
  <div class="topbar">公众号 · 草稿预览（手机宽度 420px）</div>
  <div class="inner">
    <p class="title">__TITLE__</p>
    <div class="digest">__DIGEST__</div>
    <div class="coverwrap">
      <div class="lb">封面 · 2.35:1 横带（大图）</div>
      <div class="c235"><img src="cover.png"></div>
      <div class="lb">封面 · 1:1 方块（小图）</div>
      <div class="c11w"><img src="cover.png"></div>
      <div class="meta">数据：2026-09-23 收盘 · 多源核实 · 不构成投资建议</div>
    </div>
    __BODY__
  </div>
</div>
<div class="phone" style="width:420px;">
  <div class="topbar">配图文件清单</div>
  <div class="inner" style="font-size:13px;line-height:2;color:#4A4A44;">__LIST__</div>
</div>
</body></html>"""




def _crop_css():
    """按实际封面尺寸算裁剪几何（Gemini 与 HTML 直出的尺寸不同）"""
    from PIL import Image
    W, H = Image.open(BASE / "cover.png").size
    # 2.35:1 横带（宽 560 / 388 两档）
    h235 = round(560 / 2.35)
    t235 = -round((H - W / 2.35) / 2 * (560 / W))
    h235p = round(388 / 2.35)
    t235p = -round((H - W / 2.35) / 2 * (388 / W))
    # 1:1 中心方块
    side = min(W, H)
    sc = 300 / side
    w11 = round(W * sc)
    l11 = -round((W - side) / 2 * sc)
    scp = 200 / side
    w11p = round(W * scp)
    l11p = -round((W - side) / 2 * scp)
    return {"__W235__": str(560), "__H235__": str(h235), "__T235__": str(t235),
            "__W11__": str(w11), "__L11__": str(l11),
            "__H235p__": str(h235p), "__T235p__": str(t235p),
            "__W11p__": str(w11p), "__L11p__": str(l11p)}


def _fill(html, d):
    for k, v in d.items():
        html = html.replace(k, v)
    return html

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cells = "\n".join(
        f'<div class="cell"><div class="cap">{CAPS[n]}</div><img src="{n}.png"></div>'
        for n in ua.IMAGES)
    g = _fill(GALLERY.replace("__CELLS__", cells), _crop_css())
    (BASE / "画廊预览.html").write_text(g, encoding="utf-8")

    body = ua.build_content({k: f"{k}.png" for k in ua.IMAGES})
    lst = "<br>".join(f"{n}.png　{BASE / (n + '.png')}" for n in ua.IMAGES)
    html = (PHONE.replace("__TITLE__", ua.TITLE).replace("__DIGEST__", ua.DIGEST)
            .replace("__BODY__", body).replace("__LIST__", lst))
    html = _fill(html, _crop_css())
    (BASE / "公众号预览.html").write_text(html, encoding="utf-8")
    print("OK 画廊预览.html / 公众号预览.html")


if __name__ == "__main__":
    main()
