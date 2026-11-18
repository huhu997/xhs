#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘宝图切片: 读取 render_all.mjs 产出的 _slice_jobs.json, 把全页大图按坐标裁出成品 PNG, 并清理临时目录。
用法: python slice_images.py [--root 目录]   (默认当前目录)
依赖: Pillow
"""
import json, os, shutil, argparse
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.root) if args.root else os.getcwd()
    job_file = os.path.join(root, '_slice_jobs.json')
    if not os.path.exists(job_file):
        print('[skip] 未找到 ' + job_file + ' (先跑 render_all.mjs)')
        return
    jobs = json.load(open(job_file, encoding='utf-8'))
    n = 0
    for j in jobs:
        src = j['src']
        out = j['out']
        if not os.path.exists(src):
            print('!! 源图缺失 ' + src)
            continue
        im = Image.open(src)
        box = (int(j['x']), int(j['y']), int(j['x']) + int(j['w']), int(j['y']) + int(j['h']))
        crop = im.crop(box)
        odir = os.path.dirname(out)
        if odir and not os.path.exists(odir):
            os.makedirs(odir, exist_ok=True)
        crop.save(out)
        n += 1
        print('[sliced] ' + os.path.relpath(out, root))
    print('切片完成: ' + str(n) + ' 张')
    tmp = os.path.join(root, '_tmp_full')
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
        print('[clean] 已删除临时目录 _tmp_full')


if __name__ == '__main__':
    main()
