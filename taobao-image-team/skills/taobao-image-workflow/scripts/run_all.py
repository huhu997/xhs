#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键出全套：订单 JSON -> (可选网页端生图) -> 填模板 -> 渲染 -> 切片。

  python scripts/run_all.py order.json --out <输出目录>
  python scripts/run_all.py order.json --out <输出目录> --web   # 先走网页端自动生图

网页端 --web 首次会弹出浏览器让你登录一次，之后登录态持久复用。
不想自动生图时省略 --web：订单里给 product_img 就叠加，都不给就出纯文案参数卡。
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run(cmd, label):
    print(f'\n=== {label} ===', flush=True)
    print('>>> ' + ' '.join(f'"{c}"' if ' ' in c else c for c in cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        print(f'[abort] {label} 失败，退出码 {r.returncode}', flush=True)
        sys.exit(r.returncode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('order')
    ap.add_argument('--out', required=True)
    ap.add_argument('--web', action='store_true', help='先走网页端自动生图并落盘')
    ap.add_argument('--timeout', type=int, default=150, help='网页端等待生成秒数')
    args = ap.parse_args()

    order = os.path.abspath(args.order)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    if not os.path.exists(order):
        print('[abort] 订单不存在:', order)
        sys.exit(1)

    if args.web:
        run([sys.executable, os.path.join(HERE, 'gen_product_web.py'),
             order, '--out', out, '--timeout', str(args.timeout)],
            '0/4 网页端生图 -> 落盘')

    run([sys.executable, os.path.join(HERE, 'fill_template.py'), order, '--out', out],
        '1/4 填模板 -> 4 类 HTML')
    node = shutil.which('node') or 'C:/Program Files/nodejs/node.exe'
    run([node, os.path.join(HERE, 'render_all.mjs'), out],
        '2/4 Chrome CDP 渲染')
    run([sys.executable, os.path.join(HERE, 'slice_images.py'), '--root', out],
        '3/4 切片 -> 成品 PNG')

    prefixes = ('主图_', '白底图_', '导购图_', '详情图_')
    pngs = [p for p in sorted(glob.glob(os.path.join(out, '*.png')))
            if os.path.basename(p).startswith(prefixes)]
    print(f'\n=== 完成 ===  成品 PNG {len(pngs)} 张  ->  {out}', flush=True)
    for p in pngs:
        print('  ' + os.path.basename(p), flush=True)


if __name__ == '__main__':
    main()
