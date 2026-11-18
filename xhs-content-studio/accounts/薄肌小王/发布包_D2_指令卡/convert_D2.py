# -*- coding: utf-8 -*-
"""
D2 五图转换：2160×2880 PNG -> 1080×1440 JPG (3:4, quality 92)
防串图：显式 PAIRS 映射，每张 PNG 只转成同名 JPG，逐张独立，不共用 base。
用法：python convert_D2.py
"""
from PIL import Image
import os

BASE = "F:/Cache/.workbuddy/plugins/marketplaces/my-experts/plugins/xhs-content-studio/accounts/薄肌小王/发布包_D2_指令卡"

# PNG 源 -> JPG 输出，一一对应（与 render_D2.cjs 的 CARDS 顺序一致）
PAIRS = [
    ("card1_封面.png",     "card1_封面.jpg"),
    ("card2_数据.png",     "card2_数据.jpg"),
    ("card3_六卡总览.png", "card3_六卡总览.jpg"),
    ("card4_用法拆解.png", "card4_用法拆解.jpg"),
    ("card5_钩子引导.png", "card5_钩子引导.jpg"),
]

for src, dst in PAIRS:
    sp = os.path.join(BASE, src)
    dp = os.path.join(BASE, dst)
    im = Image.open(sp).convert("RGB")
    im = im.resize((1080, 1440), Image.LANCZOS)
    im.save(dp, "JPEG", quality=92)
    print(f"[OK] {src} -> {dst}  (1080x1440, q92)")

print("DONE: 5 JPG converted.")
