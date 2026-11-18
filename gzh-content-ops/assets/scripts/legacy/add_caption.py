# -*- coding: utf-8 -*-
"""第七回 配图叠加中文标注（PIL 绘制，水印覆盖 + 标题条，保证无乱码）。
输入：candidates/ 里挑定的图；输出：同目录定稿 png（cover.png / 配图-0X-xxx.png）。
"""
from PIL import Image, ImageDraw, ImageFont
import pathlib, sys

BASE = pathlib.Path(__file__).resolve().parent
CAND = BASE / "candidates"
sys.stdout.reconfigure(encoding="utf-8")

FB = "C:/Windows/Fonts/msyhbd.ttc"
INK = (35, 30, 25)
RED = (196, 58, 42)
GRN = (46, 138, 102)
WHITE = (255, 255, 255)
CREAM = (248, 236, 214)


def _fit_font(draw, text, max_w, base_size, min_size=18):
    """把字号缩到文字宽度不超过 max_w"""
    size = base_size
    while size > min_size:
        f = ImageFont.truetype(FB, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(FB, min_size)


def top_band(im, title, sub=None, cover=False):
    """顶部深色标题条 + 朱红细线；长标题自动缩字号，保证不出框。"""
    w, h = im.size
    bh = int(h * (0.155 if cover else 0.125))
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, w, bh], fill=(*INK, 226))
    d.rectangle([0, bh, w, bh + 6], fill=(*RED, 255))
    fs = int(bh * (0.42 if sub else 0.5))
    f = _fit_font(d, title, w * 0.90, fs)
    if sub:
        d.text((w / 2, bh * 0.37), title, font=f, fill=WHITE, anchor="mm")
        f2 = _fit_font(d, sub, w * 0.86, int(f.size * 0.58))
        d.text((w / 2, bh * 0.75), sub, font=f2, fill=CREAM, anchor="mm")
    else:
        d.text((w / 2, bh / 2), title, font=f, fill=WHITE, anchor="mm")
    return Image.alpha_composite(im.convert("RGBA"), ov)


def bottom_tag(im, text, color=RED):
    """左下小标签（盖住可能的下角水印）"""
    w, h = im.size
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f = ImageFont.truetype(FB, int(h * 0.030))
    tw = d.textlength(text, font=f)
    pad = int(h * 0.016)
    d.rounded_rectangle([int(w * 0.045), int(h * 0.925), int(w * 0.045) + tw + 2 * pad, int(h * 0.925) + int(h * 0.055)],
                        radius=16, fill=(*color, 232))
    d.text((int(w * 0.045) + pad + tw / 2, int(h * 0.925) + int(h * 0.0275)), text, font=f, fill=WHITE, anchor="mm")
    return Image.alpha_composite(im.convert("RGBA"), ov)


def chips(im, items):
    """底部并排小标签 [(text,color),...]，居中排布"""
    w, h = im.size
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    fs = int(h * 0.030)
    f = ImageFont.truetype(FB, fs)
    pad = int(h * 0.016)
    widths = [d.textlength(t, font=f) + 2 * pad for t, _ in items]
    gap = int(w * 0.02)
    total = sum(widths) + gap * (len(items) - 1)
    x = (w - total) / 2
    cy = int(h * 0.945)
    for (t, c), tw in zip(items, widths):
        d.rounded_rectangle([x, cy - fs * 0.8, x + tw, cy + fs * 0.8], radius=16, fill=(*c, 236))
        d.text((x + tw / 2, cy), t, font=f, fill=WHITE, anchor="mm")
        x += tw + gap
    return Image.alpha_composite(im.convert("RGBA"), ov)


def save(im, name):
    out = BASE / name
    im.convert("RGB").save(out, quality=95)
    print(f"  ✅ {name} {im.size}")


def load(name):
    im = Image.open(CAND / name)
    return im.convert("RGBA")


# ① 封面
im = load("cover-c4.png")
im = top_band(im, "长假两本账 · 第七回", sub="一半火热，一半凉水", cover=True)
save(im, "cover.png")

# ② 外账
im = load("配图-01-洋面-c1.png")
im = top_band(im, "外账：一半火热，一半凉水")
save(im, "配图-01-洋面.png")

# ③ 洋钱袋
im = load("配图-02-洋钱袋-c1.png")
im = top_band(im, "洋钱袋：利率挂在高位")
save(im, "配图-02-洋钱袋.png")

# ④ 院里炉
im = load("配图-03-院里炉-c1.png")
im = top_band(im, "家里账：一炉温火，几瓢凉水")
save(im, "配图-03-院里炉.png")

# ⑤ 磨盘三态（核心：三种活法标签）
im = load("配图-04-磨盘三态-v1.png")
im = top_band(im, "定盘：磨市里的三种活法")
im = chips(im, [("拿定长主意", INK), ("只做极短线", RED), ("卡在中间", GRN)])
save(im, "配图-04-磨盘三态.png")

# ⑥ 开市四看
im = load("配图-05-开市四看-c1.png")
im = top_band(im, "落点：明儿开锣先看四样")
save(im, "配图-05-开市四看.png")

print("全部完成")
