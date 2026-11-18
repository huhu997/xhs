#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产品图落盘助手：把任意来源的图（Gemini/宿主生图/实拍）归一到约定路径。

用法:
  1) 输出标准生图 prompt（复制给任意生图工具）:
       python gen_product.py order.json
  2) 把拿到的图规范化并落盘到 <out>/product_<sku>.png:
       python gen_product.py order.json --save C:/path/to/gen.png --out <out>
  3) 之后重跑 fill_template.py 即自动拾取，无需改订单。

设计意图：生图后端与排版解耦。脚本层不绑定任何 AI 服务，
也不要求 API key；AI 在会话里生完图只需做一次 --save。
"""
import argparse, json, os, sys
from PIL import Image

MAX_EDGE = 1600


def build_prompt(d):
    desc = d.get('product_prompt')
    if not desc:
        return None
    return (
        "白底纯色背景商品摄影，主体为：" + desc + "\n"
        "要求：主体完整居中、竖版构图 3:4、占比约 70%、柔和均匀影棚光、高清质感。\n"
        "严禁出现：任何文字、字母、数字、logo、水印、标签、价格牌、人物、手部、"
        "场景杂物、其他商品。\n"
        "背景纯白或极浅灰，无阴影堆砌，便于直接叠加到左图右文模板。\n"
        "建议尺寸：1024x1536"
    )


def normalize(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = Image.new('RGB', im.size, (255, 255, 255))
        bg.paste(im, mask=im.getchannel('A'))
        im = bg
    else:
        im = im.convert('RGB')
    w, h = im.size
    if max(w, h) > MAX_EDGE:
        r = MAX_EDGE / max(w, h)
        im = im.resize((int(w * r), int(h * r)), Image.LANCZOS)
    im.save(dst, format='PNG')
    return dst, im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('order')
    ap.add_argument('--save', default=None, help='待落盘的图片路径')
    ap.add_argument('--out', default='.', help='输出目录（与 fill_template 的 --out 一致）')
    args = ap.parse_args()

    with open(args.order, encoding='utf-8') as f:
        d = json.load(f)
    sku = d.get('sku', 'SKU')
    dst = os.path.join(args.out, f'product_{sku}.png')

    if args.save:
        if not os.path.exists(args.save):
            print('[error] 图片不存在:', args.save)
            sys.exit(1)
        out, size = normalize(args.save, dst)
        print(f'[ok] 已落盘: {out}  {size[0]}x{size[1]}')
        print(f'[ok] 现在重跑 fill_template.py --out {args.out} 即自动拾取，无需改订单')
        return

    p = build_prompt(d)
    if not p:
        print('[info] 订单无 product_prompt，无需生图（出纯文案参数卡）')
        return
    print('=== 生图 prompt ===')
    print(p)
    print('=== 落盘路径 ===')
    print(dst)
    print('=== 下一步 ===')
    print('把上面的 prompt 交给生图工具，拿到图片后执行:')
    print(f'  python scripts/gen_product.py {args.order} --save <图片路径> --out {args.out}')


if __name__ == '__main__':
    main()
