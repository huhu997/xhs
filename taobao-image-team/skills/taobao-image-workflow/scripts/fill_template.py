#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘宝电商图 · 参数化出图入口 (支持可选产品图叠加)
用法: python fill_template.py <order.json> [--out <目录>]
订单可含 "product_img": "<绝对路径>"  -> 主图左图右文 + 导购首图叠加产品图
无 product_img 时, 主图/导购首图保持纯文案参数卡 (向后兼容)
模板风格: 深蓝科技风 + 橙红 (源自已验证可上架的爆款结构)
"""
import json, os, sys, argparse, base64, io
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name), encoding='utf-8') as f:
        return f.read()


TPL_MAIN = load('template_main.html')
TPL_DETAIL = load('template_detail.html')
TPL_GUIDE = load('template_guide.html')
TPL_WB = load('template_whitebg.html')


GEN_PROMPT_TPL = """【商品图生图 prompt · 内部用，禁止写进上架物料】
白底纯色背景商品摄影，主体为：{desc}
要求：主体完整居中、竖版构图 3:4、占比约 70%、柔和均匀影棚光、高清质感。
严禁出现：任何文字、字母、数字、logo、水印、标签、价格牌、人物、手部、场景杂物、其他商品。
背景纯白或极浅灰，无阴影堆砌，便于直接叠加到左图右文模板。
建议尺寸：1024x1536
落盘路径（约定式，脚本自动拾取）：{path}
"""

def build_product(order, out_dir='.'):
    """产品图解析优先级：
    1) product_img 指定且文件存在 -> 用它
    2) 约定路径 <out>/product_<sku>.png 存在 -> 自动拾取（生图落盘即用，零改单）
    3) 有 product_prompt 但无图 -> 写出生图任务单，返回 None（本次出纯文案卡）
    4) 都没有 -> None
    可选 product_crop: [x1,y1,x2,y2] 比例数组，仅对需要去杂背景的实拍图启用。
    """
    sku = order.get('sku', 'SKU')
    auto_path = os.path.join(out_dir, f'product_{sku}.png')
    pp = order.get('product_img')
    p = None
    if pp:
        cand = pp if os.path.isabs(pp) else os.path.join(os.getcwd(), pp)
        if os.path.exists(cand):
            p = cand
        else:
            print('[warn] product_img 不存在:', cand)
    if not p and os.path.exists(auto_path):
        p = auto_path
        print(f'[auto] 拾取约定路径产品图: {auto_path}')
    if not p:
        desc = order.get('product_prompt')
        if desc:
            task = os.path.join(out_dir, f'生图任务单_{sku}.txt')
            with open(task, 'w', encoding='utf-8') as f:
                f.write(GEN_PROMPT_TPL.format(desc=desc, path=auto_path))
            print(f'[need-gen] 已生成生图任务单: {task}')
            print(f'[need-gen] 生图后存为 {auto_path}，重跑本脚本即自动叠加（无需改订单）')
        return None
    try:
        im = Image.open(p).convert('RGB')
        crop = order.get('product_crop')
        if crop and len(crop) == 4:
            w, h = im.size
            im = im.crop((int(w * crop[0]), int(h * crop[1]),
                          int(w * crop[2]), int(h * crop[3])))
            print(f'[crop] 按比例裁剪 {crop}')
        buf = io.BytesIO()
        im.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print('[warn] product_img 处理失败:', e)
        return None


def render_main(d, pb):
    points = "".join(f'<div class="pt">{p}</div>' for p in d.get('points', []))
    left = f'<div class="left"><img src="data:image/png;base64,{pb}"></div>' if pb else ''
    has = '' if pb else 'no-img'
    return (TPL_MAIN
            .replace('{{HAS_IMG}}', has)
            .replace('{{LEFT}}', left)
            .replace('{{BADGE}}', d.get('badge', ''))
            .replace('{{TITLE_LINE1}}', d.get('title_line1', ''))
            .replace('{{TITLE_HL}}', d.get('title_hl', ''))
            .replace('{{SUB}}', d.get('sub', ''))
            .replace('{{POINTS}}', points)
            .replace('{{PRICE}}', d.get('price', ''))
            .replace('{{FOOT}}', d.get('foot', '')))


def render_detail(d):
    hd_title = d.get('detail_title') or (d['title_line1'] + ((' ' + d['title_hl']) if d.get('title_hl') else ''))
    sections = ""
    for sec in d.get('detail', []):
        h = sec['h']
        if sec['type'] == 'ul':
            items = "".join(f'<li>{i}</li>' for i in sec['items'])
            sections += f'<div class="sec"><h2>{h}</h2><ul>{items}</ul></div>'
        elif sec['type'] == 'cards':
            cards = "".join(
                f'<div class="card"><div class="n">{c["n"]}</div><div class="t"><b>{c["t"]}</b><br/>{c["d"]}</div></div>'
                for c in sec['cards'])
            sections += f'<div class="sec"><h2>{h}</h2><div class="cards">{cards}</div></div>'
        elif sec['type'] == 'steps':
            steps = "".join(
                f'<div class="step"><div class="n">{s["n"]}</div><div><div class="x">{s["x"]}</div><div class="y">{s["y"]}</div></div></div>'
                for s in sec['steps'])
            sections += f'<div class="sec"><h2>{h}</h2><div class="steps">{steps}</div></div>'
    ft = d.get('detail_ft', '内容为个人整理重制，非官方出品，不承诺任何收益，请理性购买。')
    return (TPL_DETAIL
            .replace('{{HD_BADGE}}', d.get('badge', ''))
            .replace('{{HD_TITLE}}', hd_title)
            .replace('{{HD_SUB}}', d.get('sub', ''))
            .replace('{{SECTIONS}}', sections)
            .replace('{{FT}}', ft))


def render_guide(d, pb):
    themes = ['dark', 'light', 'light', 'light', 'light']
    cards = ""
    for idx, g in enumerate(d.get('guide', [])):
        theme = themes[idx] if idx < len(themes) else 'light'
        kind = g.get('kind', 'points')
        if 'points' in g:
            inner = "".join(f'<div class="pt">{p}</div>' for p in g['points'])
            foot = (f'<div class="bar"><span class="price">{g["price"]}</span><span class="r">{g.get("foot","")}</span></div>'
                    if g.get('price') else '')
            body = f'<div class="pts">{inner}</div>{foot}'
        elif 'list' in g:
            inner = "".join(f'<div class="li">{i}</div>' for i in g['list'])
            body = f'<div class="list">{inner}</div>'
        elif 'steps' in g:
            inner = "".join(
                f'<div class="step"><div class="n">{s["n"]}</div><div><div class="x">{s["x"]}</div><div class="y">{s["y"]}</div></div></div>'
                for s in g['steps'])
            body = f'<div class="steps">{inner}</div>'
        elif 'tiers' in g:
            inner = "".join(
                f'<div class="tier"><div><div class="a">{t["a"]}</div><div class="b">{t["b"]}</div></div><div class="c">{t["c"]}</div></div>'
                for t in g['tiers'])
            body = f'<div class="tiers">{inner}</div>'
        else:
            body = ""
        hl = g.get('hl', '')
        title_html = g['line1'] + (f'<br/><span class="o">{hl}</span>' if hl else '')
        if idx == 0 and pb:
            cards += (f'<div class="card {theme} has-img"><div class="pimg"><img src="data:image/png;base64,{pb}"></div>'
                      f'<div class="body"><div class="badge">{g["badge"]}</div><div class="t">{title_html}</div>{body}</div></div>')
        else:
            cards += (f'<div class="card {theme}"><div class="badge">{g["badge"]}</div>'
                      f'<div class="t">{title_html}</div>{body}</div>')
    return (TPL_GUIDE
            .replace('{{SKU}}', d.get('sku', ''))
            .replace('{{CARDS}}', cards))


def render_whitebg(d):
    wb_title = d.get('whitebg_title', d['title_line1'])
    wb_sub = d.get('whitebg_sub', d.get('sub', ''))
    return (TPL_WB
            .replace('{{WB_TITLE}}', wb_title)
            .replace('{{WB_SUB}}', wb_sub))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('order')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    with open(args.order, encoding='utf-8') as f:
        d = json.load(f)
    sku = d['sku']
    out = args.out or sku
    os.makedirs(out, exist_ok=True)
    pb = build_product(d, out)
    if pb:
        print('[ok] 产品图已嵌入 (base64 内联) -> 主图左图右文 + 导购首图叠加')
    else:
        print('[info] 无 product_img, 主图/导购首图保持纯文案参数卡')
    open(f'{out}/主图_{sku}.html', 'w', encoding='utf-8').write(render_main(d, pb))
    open(f'{out}/详情图_{sku}.html', 'w', encoding='utf-8').write(render_detail(d))
    open(f'{out}/导购图3x4_{sku}.html', 'w', encoding='utf-8').write(render_guide(d, pb))
    open(f'{out}/白底图_{sku}.html', 'w', encoding='utf-8').write(render_whitebg(d))
    print(f'[ok] 生成 4 类 HTML -> {out}/  (主图/详情/导购3x4/白底)')


if __name__ == '__main__':
    main()
