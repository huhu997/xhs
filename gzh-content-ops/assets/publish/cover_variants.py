#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""封面 3 个方向方案（同一个标题），生成 PNG 供挑选"""
from PIL import Image, ImageDraw, ImageFont
import pathlib

FONT = "C:/Windows/Fonts/msyh.ttc"
W, H = 900, 500
BG = (241, 242, 238)     # 米白
INK = (17, 20, 23)       # 深墨
ACCENT = (232, 93, 42)   # 橙红
MUTED = (154, 154, 154)  # 灰

title = "52家涨停，0家跌停，一只跌停都没有"
OUT = pathlib.Path("F:/桌面/zcode工作区/_wx_read/cover_variants")
OUT.mkdir(parents=True, exist_ok=True)


def wrap(d, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    lines.append(cur)
    return lines


def A():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(FONT, 26)
    fbig = ImageFont.truetype(FONT, 190)
    fmid = ImageFont.truetype(FONT, 72)
    ft = ImageFont.truetype(FONT, 38)
    d.text((64, 40), "数据派 · 财经快评", font=fb, fill=ACCENT)
    # 超大核心数字 "0" + 标签 "跌停"
    x = d.text((64, 96), "0", font=fbig, fill=ACCENT)[0] if False else 64
    d.text((64, 96), "0", font=fbig, fill=ACCENT)
    w0 = d.textlength("0", font=fbig)
    d.text((64 + w0 + 16, 190), "跌停", font=fmid, fill=INK)
    # 标题
    lines = wrap(d, title, ft, W - 128)
    y = 340
    for ln in lines[:2]:
        d.text((64, y), ln, font=ft, fill=INK)
        y += 54
    img.save(OUT / "A_超大数字.png")


def B():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(FONT, 26)
    ft = ImageFont.truetype(FONT, 48)
    fbig = ImageFont.truetype(FONT, 62)
    fd = ImageFont.truetype(FONT, 22)
    # 上区：米白 + 品牌 + 标题
    d.text((64, 42), "数据派 · 财经快评", font=fb, fill=ACCENT)
    lines = wrap(d, title, ft, W - 128)
    y = 120
    for ln in lines[:2]:
        d.text((64, y), ln, font=ft, fill=INK)
        y += 66
    # 下区：深墨色块 + 核心数字
    d.rectangle([0, 280, W, H], fill=INK)
    d.text((64, 310), "0 跌停", font=fbig, fill=ACCENT)
    d.text((64, 430), "数据派 · 财经快评  ·  2026.08.26", font=fd, fill=(255, 255, 255))
    img.save(OUT / "B_上下分割.png")


def C():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(FONT, 26)
    ft = ImageFont.truetype(FONT, 44)
    fcard = ImageFont.truetype(FONT, 56)
    # 背景淡灰 K 线柱
    import random
    random.seed(3)
    for i in range(9):
        x = 480 + i * 46
        h = random.randint(40, 160)
        y = 380 - h
        d.rectangle([x, y, x + 18, 380], fill=(226, 226, 220))
    # 品牌 + 标题
    d.text((64, 42), "数据派 · 财经快评", font=fb, fill=ACCENT)
    lines = wrap(d, title, ft, 420)
    y = 120
    for ln in lines[:2]:
        d.text((64, y), ln, font=ft, fill=INK)
        y += 60
    # 橙红数字卡片
    d.rounded_rectangle([64, 330, 420, 460], radius=16, fill=ACCENT)
    d.text((92, 356), "0 跌停", font=fcard, fill=(255, 255, 255))
    img.save(OUT / "C_数据卡片.png")


A(); B(); C()
print("3 个封面方案已生成到:", OUT)
for f in sorted(OUT.glob("*.png")):
    print(" ", f.name)
