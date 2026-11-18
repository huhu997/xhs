#!/usr/bin/env python3
"""拼接电商详情长图：多张屏图 -> 750px 宽长图 + 切片。
用法: python stitch_long_image.py out/screen-*.png --width 750 --out out/detail-750.jpg
依赖: pip install pillow
"""
import argparse
import os
import sys
from PIL import Image


def stitch(paths, width, out_path):
    imgs = []
    for p in sorted(paths):
        im = Image.open(p).convert("RGB")
        if im.width != width:
            h = int(im.height * width / im.width)
            im = im.resize((width, h), Image.LANCZOS)
        imgs.append(im)
    total_h = sum(im.height for im in imgs) + (len(imgs) - 1) * 0  # 无间隙拼接
    canvas = Image.new("RGB", (width, total_h), (255, 255, 255))
    y = 0
    for im in imgs:
        canvas.paste(im, (0, y))
        y += im.height
    canvas.save(out_path, "JPEG", quality=88)
    return canvas.size


def slice_long(src_path, out_dir, max_h=1546):
    im = Image.open(src_path).convert("RGB")
    w, h = im.size
    os.makedirs(out_dir, exist_ok=True)
    n = (h + max_h - 1) // max_h
    names = []
    for i in range(n):
        top = i * max_h
        bot = min(top + max_h, h)
        crop = im.crop((0, top, w, bot))
        name = os.path.join(out_dir, f"slice-{i+1:02d}.jpg")
        crop.save(name, "JPEG", quality=88)
        names.append(name)
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+", help="屏图路径（支持 glob）")
    ap.add_argument("--width", type=int, default=750)
    ap.add_argument("--out", default="out/detail-750.jpg")
    ap.add_argument("--slice-dir", default=None, help="长图切片输出目录，默认 <out_dir>/<out_name>-slices")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    size = stitch(args.images, args.width, args.out)
    print(f"[ok] 长图已生成: {args.out} 尺寸={size}")

    slice_dir = args.slice_dir or os.path.join(
        os.path.dirname(args.out) or ".",
        os.path.splitext(os.path.basename(args.out))[0] + "-slices",
    )
    names = slice_long(args.out, slice_dir)
    print(f"[ok] 切片 {len(names)} 张 -> {slice_dir}")


if __name__ == "__main__":
    main()
