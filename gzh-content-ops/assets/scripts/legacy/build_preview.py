#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9/24 盘面长文 → 公众号预览 HTML（客栈暖木主题 · 同福客栈群像版 · 配图位占位，走 Gemini 出图）

满配群像：掌柜(中登小王)/跑堂小散/账房老机/捕快证监爷/算命道长 + 画外音。
与 upload_article.py 同款内联样式 + span leaf 结构，过 _validate_gzh_html.py 0 ERROR。
配图暂用占位卡片，等 Opera 9222 就绪跑 gen_images.py 出图后，换成 <img> 即可投递。
"""
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")

BG = "#F4E8D0"; INK = "#2B2620"; TEXT = "#5A5247"; ACCENT = "#B23A2E"; ACCENT2 = "#3F7A5E"
LINE = "#DCC9A8"; CARD = "#EFE2C6"; PILL = "#F0D9C8"; MISS = "#8A8A85"
UP = "#B23A2E"; DN = "#3F7A5E"

# 角色配色（身份标签，非涨跌色）
ZHANGGUI = ACCENT          # 掌柜·中登小王（绿）
XIAOSAN = "#C8862A"        # 跑堂·小散（琥珀）
LAOJI = "#2F6E8F"          # 账房·老机（青蓝）
YE = "#6B4E9E"             # 捕快·证监爷（靛紫）
DAO = "#B8923F"            # 算命·道长（暗金）

TITLE = "第一回 节前客栈齐收账，退潮江湖各西东"
DIGEST = ("A股江湖每日说书 · 同福客栈版。沪指跌1.22%收3888.37，深成指、创业板均跌超2%，"
          "两市成交1.65万亿、缩量1116亿，上涨1120家、下跌4306家。双节前最后一交易日——"
          "长盈客栈的客官们打烊前忙着收账走人。落袋为安，还是趋势转弱？掌柜、小散、老机、证监爷、道长，各有话说。")


def p(text, size=14, color=TEXT, bold=False):
    w = "font-weight:bold;" if bold else ""
    return f'<p style="font-size:{size}px;color:{color};{w}line-height:1.85;margin:0 0 12px;">{text}</p>'


def h2(t):
    return (f'<section style="font-size:17px;font-weight:bold;color:{INK};border-left:4px solid {ACCENT};'
            f'padding-left:10px;margin:26px 0 12px;line-height:1.5;">{t}</section>')


def kpi(v, k, hl=False):
    bg = PILL if hl else CARD
    bd = ACCENT if hl else LINE
    vc = ACCENT if hl else INK
    return (f'<section style="flex:1;background:{bg};border:1.5px solid {bd};'
            f'padding:12px 6px;text-align:center;">'
            f'<p style="font-size:21px;font-weight:900;color:{vc};margin:0 0 3px;">{v}</p>'
            f'<p style="font-size:11px;color:{TEXT};margin:0;">{k}</p></section>')


def spotlight(main):
    return (f'<section style="background:{ACCENT};color:#FFFFFF;padding:15px 18px;'
            f'margin:18px 0;font-size:15px;font-weight:bold;line-height:1.8;">{main}</section>')


def dlg(speaker, text, color):
    return (f'<section style="display:flex;gap:9px;align-items:flex-start;margin:0 0 9px;">'
            f'<span style="flex:0 0 56px;background:{color};color:#FFFFFF;font-size:12px;font-weight:800;'
            f'text-align:center;padding:5px 0;border-radius:6px;line-height:1.35;">{speaker}</span>'
            f'<p style="flex:1;margin:0;font-size:14px;color:{INK};line-height:1.85;">{text}</p></section>')


def vo(text):
    return (f'<section style="background:#EDE8DC;border-left:3px solid {ACCENT};'
            f'padding:12px 16px;margin:0 0 14px;font-style:italic;'
            f'font-size:14px;color:{INK};line-height:1.85;">🎙️ <span style="font-weight:800;'
            f'color:{ACCENT};font-style:normal;">画外音</span>：{text}</section>')


def lockbox(no, title, html):
    return (f'<section style="background:{CARD};border:1.5px solid {LINE};border-left:4px solid {ACCENT};'
            f'padding:14px 16px;margin:0 0 14px;">'
            f'<p style="font-size:13px;font-weight:800;color:{ACCENT};margin:0 0 6px;letter-spacing:1px;">'
            f'{no} · {title}</p>'
            f'<p style="font-size:14px;color:{INK};margin:0;line-height:1.9;">{html}</p></section>')


def rowbox(rows):
    body = "<br>".join(rows)
    return (f'<section style="background:{CARD};border:1.5px solid {LINE};'
            f'padding:14px 16px;margin:0 0 14px;font-size:14px;color:{INK};line-height:2.0;">{body}</section>')


def img_ph(name, caption):
    return (f'<section style="background:{CARD};border:1.5px solid {LINE};border-left:4px solid {ACCENT};'
            f'padding:18px 16px;margin:18px 0;text-align:center;">'
            f'<p style="font-size:13px;font-weight:800;color:{ACCENT};margin:0 0 6px;letter-spacing:1px;">'
            f'配图待生成 · {name}.png</p>'
            f'<p style="font-size:14px;color:{INK};margin:0;line-height:1.7;">{caption}</p></section>')


def img(name, caption):
    return (f'<section style="margin:18px 0;">'
            f'<img src="{name}.png" style="width:100%;display:block;border-radius:8px;'
            f'border:1.5px solid {LINE};" />'
            f'<p style="font-size:12px;color:{TEXT};margin:6px 0 0;text-align:center;'
            f'font-style:italic;">{caption}</p></section>')


def warnbox(html):
    return (f'<section style="background:#F3E9DC;border:1.5px solid #E0C9AE;padding:13px 16px;'
            f'margin:0 0 14px;font-size:14px;color:{INK};line-height:1.9;">{html}</section>')


def wrap_leaf(html):
    out, depth = [], 0
    for seg in re.split(r"(<[^>]+>)", html):
        if seg.startswith("<"):
            if re.match(r"<\s*span\b", seg) and "leaf" in seg:
                depth += 1
            elif re.match(r"</\s*span\s*>", seg):
                depth = max(0, depth - 1)
            out.append(seg)
        else:
            out.append(f'<span leaf="">{seg}</span>' if seg.strip() and depth == 0 else seg)
    return "".join(out)


def build_content():
    strong = lambda s: f'<strong style="color:{INK};">{s}</strong>'
    gr = lambda s: f'<strong style="color:{ACCENT};">{s}</strong>'
    rt = lambda s: f'<strong style="color:{ACCENT2};">{s}</strong>'
    ph = lambda n, c: img(n, c)
    parts = [
        # 回目 hero
        (f'<section style="background:{ACCENT};padding:24px 20px;margin:0 0 16px;">'
         f'<p style="font-size:11px;letter-spacing:3px;color:#FFFFFF;font-weight:700;margin:0 0 6px;opacity:.92;">'
         f'A股江湖每日说书 · 同福客栈版 · 2026.09.24</p>'
         f'<p style="font-size:23px;font-weight:900;color:#FFFFFF;margin:0;line-height:1.3;">'
         f'第一回　节前客栈齐收账，退潮江湖各西东</p>'
         f'<p style="font-size:12px;color:#FFFFFF;margin:8px 0 0;opacity:.88;">'
         f'⭐ 设为星标，每天18:30说书准时开锣</p></section>'),
        # 开场
        (f'<section style="background:{CARD};border-left:3px solid {ACCENT};'
         f'padding:12px 14px;margin:0 0 16px;border-top:1.5px solid {LINE};border-right:1.5px solid {LINE};'
         f'border-bottom:1.5px solid {LINE};">'
         f'<p style="font-size:12px;font-weight:800;color:{ACCENT};margin:0 0 4px;">【开场】长盈客栈，打烊前的一桩乱</p>'
         f'<p style="font-size:13px;color:{INK};margin:0;line-height:1.75;">'
         f'话说丙午年八月十四，公历2026年9月24日，周四。中秋连国庆，双节将至——这日，正是江湖上最长一次休市前的最后一口气。</p></section>'),
        dlg("掌柜", f'额滴神呀！今儿这账本，咱{strong("长盈客栈")}的客官们，可都忙着收账走人咧。', ZHANGGUI),
        dlg("小散", "掌柜的！我这点碎银子今儿又缩水了！满堂绿油油，俺心慌呐！", XIAOSAN),
        dlg("老机", f'（拨拉算盘）慌甚慌。老朽算了一笔：上证收{strong("3888.37")}、跌{strong("1.22%")}；'
            f'深成指跌{strong("2.34%")}、创业板跌{strong("2.68%")}、科创50跌{strong("2.35%")}。五路镖局，没一路是绿里透红的。', LAOJI),
        dlg("掌柜", f'正是。深成指、创业板盘中一度跌超2%，尾盘略收，方向没改。全市场{gr("涨1120家")}、{rt("跌4306家")}——'
            f'跌的是涨的将近四倍。成交{strong("1.65万亿")}，比昨日还缩了{strong("1116亿")}。', ZHANGGUI),
        dlg("小散", "那、那不更便宜了么？", XIAOSAN),
        dlg("老机", "便宜？量在缩、价在砸，想走的比想接的多，接的人也懒得伸手。这不是捡便宜，这是下杀。", LAOJI),
        dlg("掌柜", f'所以今日这一回，咱单表八字——{strong("落袋为安，还是转弱？")} 列位且沏茶听书。', ZHANGGUI),
        ('<section style="display:flex;gap:8px;margin:0 0 16px;">'
         + kpi("3888.37", "上证指数 -1.22%")
         + kpi("1.65万亿", "成交 · 缩1116亿", hl=True)
         + kpi("52家", "涨停 · 跌停15家")
         + '</section>'),
        ph("cover", "封面题图：回目——第一回 节前客栈齐收账，退潮江湖各西东（客栈暖木调 · 长盈客栈匾额意象，走 Gemini 出图）"),
        ph("data", "数据总览：五指齐绿（上证-1.22% / 深证-2.34% / 创业板-2.68% / 科创50-2.35% / 北证50-1.70%），上涨1120家、下跌4306家"),
        h2("【正传一】五指齐绿，满堂绿影压红妆"),
        dlg("证监爷", "本捕快巡了一圈市面，且听明细。五路指数，齐刷刷绿了脸：", YE),
        (f'<section style="font-size:13px;color:{INK};line-height:2.1;background:{CARD};'
         f'border:1.5px solid {LINE};padding:12px 16px;margin:0 0 14px;">'
         f'上证指数 <b>3888.37</b> <span style="color:{DN};font-weight:800;">-1.22%</span><br>'
         f'深证成指 <b>13316.97</b> <span style="color:{DN};font-weight:800;">-2.34%</span><br>'
         f'创业板指 <b>3288.95</b> <span style="color:{DN};font-weight:800;">-2.68%</span><br>'
         f'科创50 <b>1621.87</b> <span style="color:{DN};font-weight:800;">-2.35%</span><br>'
         f'北证50 <b>1055.74</b> <span style="color:{DN};font-weight:800;">-1.70%</span>'
         f'</section>'),
        dlg("道长", f'贫道夜观天象，见三桩反常，列位细品——', DAO),
        p(f'其一，{strong("五指齐绿，创业板、科创跌幅皆过2%。")}这不是一路镖局调银子，是满堂都在减仓。', 14),
        p(f'其二，{strong("成交1.65万亿，缩了1116亿，跌得却更狠。")}昨日缩量小阴，今日缩量下杀。量没放出、价却往下走。', 14),
        p(f'其三，{strong("跌停从13家跳到15家，涨停停在52家。")}高位接力明显转弱。{strong("退潮从不自指数起，自跌停板与接力断档起。")}', 14),
        dlg("掌柜", "（敲桌）指数跌了一分有余，里头的人却已迈出门槛咯。", ZHANGGUI),
        h2("【正传二】昨日四桩悬案，今日如何了结"),
        dlg("掌柜", "老规矩。昨日俺撂下的是四桩" + strong("条件") + "，非四句" + strong("卦辞") + "。今儿一一对账，本子拿来！", ZHANGGUI),
        dlg("老机", "（念账）一桩：量能守1.6万亿上方算企稳。今儿量在1.65万亿守住了，价却大跌——"
            "<b style=\"color:#B98727;\">⚠️ 半了</b>：量价背离，非企稳是缩量下杀。", LAOJI),
        dlg("证监爷", "二桩：硬件连上第二日。莫要乱来！今日硬件集体领跌，PCB那家超声电子直奔跌停，砸盘主力反是他——"
            f"<b style=\"color:{ACCENT2};\">❌ 反向下</b>。", YE),
        dlg("道长", f'三桩：节前跌停收敛至5家内。卦象显示——<b style="color:{ACCENT2};">❌ 未了</b>，跌停15家，不降反增。', DAO),
        dlg("小散", "四、四桩呢？俺最关心涨停数！", XIAOSAN),
        dlg("掌柜", f'四桩：涨停回60家、最高板回5板。今儿涨停52、最高4板——<b style="color:{ACCENT2};">❌ 未了</b>，皆未达标。', ZHANGGUI),
        dlg("老机", "四桩悬案，一桩未真破。二三四皆指情绪仍在退，第一桩也只量上勉强过关。", LAOJI),
        dlg("掌柜", "这正是——节前这一波避险，比昨日估的更决绝。", ZHANGGUI),
        ph("verify", "昨日四桩悬案对账：0应验 / 1半了（量达标价反向）/ 3未了（硬件反向、跌停15、情绪未止）"),
        h2("【正传三】银钱去向：避险的抱团，热门的散了"),
        dlg("掌柜", "把今日涨的跌的摆一处，门道便明。小散，你昨日抱的那几只呢？", ZHANGGUI),
        dlg("小散", "别提了……PCB、半导体，绿得俺眼晕。", XIAOSAN),
        dlg("老机", f'（拨算盘）说得清的抱团还在：风电设备全天最硬、减速器持续发酵、港口航运午后走高、煤炭凭业绩护盘，'
            f'林业、中船系、纺服、机场、出版也逆势翻红。风电吉鑫科技涨停、威力传动涨近10%；减速器宁波东力、中马传动、长华集团齐涨停。', LAOJI),
        dlg("证监爷", f'被砸最狠的，皆是前期热门：PCB、HBM、铜箔覆铜板、贵金属、半导体、房地产、CRO、有色金属。'
            f'PCB的超声电子跌停，房地产华丽家族跌停、华远控股跌超9%——{strong("跌停板上有名的，多是旧日主角")}。', YE),
        dlg("道长", f'贫道一言以蔽之：{strong("不是无差别崩，是高弹性、高拥挤、先前涨多的被人减；低估值、有业绩、防守型的还有人抱。")}', DAO),
        ph("money", "资金去向：左·避险抱团（风电/减速器/港口/煤炭）；右·前期热门领跌（PCB/HBM/半导体/贵金属/房地产/CRO）"),
        h2("【正传四】三条暗线，暗流涌动"),
        dlg("道长", "天象有变，三条暗线，听贫道道来。", DAO),
        lockbox("暗线一", "海外先递了刀，A股却自己多砍一刀",
                f'隔夜美股三指齐跌——道指{rt("-0.68%")}、纳指{rt("-1.13%")}、标普{rt("-0.75%")}，费半{rt("-1.23%")}，'
                f'美光{rt("-2.22%")}、SK海力士{rt("-3.12%")}、英伟达{rt("-1.47%")}。导火索是美债收益率飙到十年高位5.11%（单日加15个基点）。'
                f'{strong("全球风险资产皆承压，A股不过其中之一，却跌得比美股狠——可见自家还压着一份节前不想持筹码的抛压。")}'),
        lockbox("暗线二", "双节十三日长假，平白添了不确定性折价",
                f'自明日（9月25日）起，中秋连国庆休至10月7日，下个开市要等10月8日。中间十三天，海外利率、政策、财报全是未知数。'
                f'{strong("长假前，银子天生不愿扛高弹性头寸过夜——这不是看空，是不愿闭市时露了风险。")}今日跌相，与这日历暗合。'),
        lockbox("暗线三", "杠杆银子由加仓转净卖",
                f'截至昨日（9月23日）融资余额{strong("2.625万亿")}，当日融资净买入{rt("-10.43亿")}——这轮头一遭转负'
                f'（9月21日还净买141.88亿、22日净买29.25亿）。'
                f'{strong("真要夺门，杠杆必先动；今日这条线，已动了。")}'),
        ph("chain", "三条暗线：①海外risk-off但A股跌更多 ②双节13天不确定性折价 ③杠杆净卖出-10.43亿"),
        h2("【正传五】四条闲笔，补足说书"),
        dlg("小散", "掌柜的，闲笔俺爱听，您捡要紧的说！", XIAOSAN),
        dlg("掌柜", "好。四条闲笔，速速道来——", ZHANGGUI),
        p(f'{strong("闲笔一：下跌4306家，近日最不均衡之一。")}涨1120、跌4306，近乎1:4，非局部调整，是整体性减仓。', 14),
        p(f'{strong("闲笔二·接力再断档。")}昨日涨停62只，今日仅{strong("17只")}上涨（27.4%）、{strong("8只")}再涨停，'
          f'涨幅中位{rt("-2.78%")}、平均{rt("-1.59%")}。{strong("接力从四成能涨掉到不足三成，中位自-1.42%恶至-2.78%，短线情绪加速转冷。")}', 14),
        p(f'{strong("闲笔三：跌停15家，近十日偏高一档。")}涨停52、跌停15，多空已明显失衡。但最高连板仍停在4板（新华文轩、大亚圣象），非高位彻底崩，是中位于跌停在扩散。', 14),
        p(f'{strong("闲笔四·逆势抱团犹在，非系统性恐慌。")}风电、减速器、港口、煤炭仍有人抱，银行亦小幅护盘。'
          f'{strong("若真系统性恐慌，断无这般清晰的抱团——更像有选择地撤，非无差别地跑。")}', 14),
        ph("clues", "四条闲笔：①4306只下跌 ②接力中位-2.78% ③跌停15家 ④逆势抱团仍在"),
        ph("ebb", "退潮刻度：跌停13→15、接力中位-1.42%→-2.78%、两融净买入+29.25→-10.43"),
        h2("【插叙】老掌柜讲古：两年前的今天，同一个9月24"),
        dlg("掌柜", "（清清嗓子）说到这日期，老掌柜给列位讲段旧事。今儿是9月24日。两年前的同日（2024年9月24日），"
            "这江湖曾上演过改变后来两年叙事的一出戏。", ZHANGGUI),
        p(f'那日一早，国新办开台，央行、金融监管总局、证监会“一行一局一会”一把手同台，于{strong("开盘前")}甩出一套超预期的解数：'
          f'降准0.5个百分点（释长期流动性约1万亿）、政策利率自1.7%降至1.5%、存量房贷利率下调（惠及约5000万户、1.5亿人口）、'
          f'二套首付降至15%，更{strong("头一遭")}创设支持资本市场之器——证券基金保险公司互换便利（首期5000亿）、'
          f'股票回购增持专项再贷款（首期3000亿）。', 14),
        p(f'市道反应极快：沪指当日{gr(" +4.15% ")}收2863点，创四年余最大单日涨幅；深成指{gr(" +4.36% ")}、创业板{gr(" +5.54% ")}；'
          f'全市场{gr(" 5165只个股上涨、占比97% ")}，大金融掀涨停潮——即后来被频频提起的“924行情”。', 14),
        dlg("老机", f'（拨算盘对比）两年前后同一个9月24，颇堪玩味——', LAOJI),
        rowbox([
            '🟢 <b>两年前（2024）：开弓。</b>政策点火、预期反转，彼时亦是长假前，市道择了向上突破——沪指单日+4.15%、97%个股上涨。',
            '🟠 <b>两年后（2026）：收弓。</b>同样长假前，市道却将手中筹码先平一平——沪指-1.22%、4306只下跌、杠杆净卖出。',
        ]),
        dlg("掌柜", "同是9月24，一个是" + strong("不想错过") + "之起点，一个是" + strong("不想扛险") + "之出口。"
            "老掌柜不从此对比里卜一句“会涨回来”——那非说书人本分。只提醒一句："
            + strong("市道情绪之钟摆，自来从一个极端荡向另一个极端。") + "记下了便好。", ZHANGGUI),
        h2("【正传六】双节十三日，原是清账时"),
        dlg("掌柜", f'前两日已表：今年假期分两段，中秋（9月25日起）与国庆（10月1日至7日）之间，生生将交易日掐断至10月8日。'
            f'{strong("今日，便是这漫漫长休前最后一处出口。")}', ZHANGGUI),
        p(f'每年长假前，皆演同一出：{strong("把押的收一收，把说得清的留一留。")}今日盘面写的正是这个——', 14),
        rowbox([
            '· <b>说不清的、先前涨多的，先走。</b>PCB、HBM、半导体、贵金属、房地产、CRO这些昔日主角集体领跌。',
            '· <b>说得清的、有业绩的，留下。</b>风电、减速器、港口、煤炭仍在逆势抱团，共性是<b>有订单、有业绩、估值不贵</b>。',
            '· <b>杠杆先动。</b>融资净买入转负，是<b>不愿扛过假期</b>最直接的证。',
        ]),
        dlg("道长", f'贫道点破——今日这{strong("缩量下杀")}，读来更像一次长假前的清账：将带不确定性的筹码先平，将确定性留着。'
            f'{strong("清账与转弱之别，在于清账会留抱团之痕——今日所留之痕，便是风电与防守那头的逆势。")}', DAO),
        h2("【片尾·点化】欲知后事，且听下回分解"),
        vo("这正是——同是佳节前，有人开弓，有人收弓。"),
        dlg("掌柜", "昨儿俺写" + strong("节奏变了，方向没变") + "。今儿市道将这话推到了墙角。", ZHANGGUI),
        dlg("掌柜", "4306只下跌、缩量下杀、跌停扩散、接力中位-2.78%、杠杆净卖出——单看这些，极易得出行情坏了的断语。"
            "却也将另一条线摆上桌：" + gr("风电、减速器、港口、煤炭仍在逆势抱团，银行仍护盘，最高板未降。")
            + "这不像系统性转弱，更像一次长假前的集中清账。", ZHANGGUI),
        dlg("老机", "两边信号皆已摆上，信哪边，凭列位自断。", LAOJI),
        dlg("掌柜", "俺所能认的只有一件：今日之跌，主体非基本面突变，是日历——十三日不开盘，带来的是不确定性折价，非价值重估。"
            "至于节后涨落、该买该卖、何价进出——这三问俺不答，亦不当由俺答。俺只负责将这棋盘摆清。", ZHANGGUI),
        p("10月8日开市，且看这四桩观察如何了结：", 14),
        warnbox("9月25日到10月7日休市，下个交易日是10月8日。以下四条，节后回来逐条对账。"),
        rowbox([
            '1️⃣ 量能走向：节后首日成交能否回2万亿上方（避险回流）；还是续缩在1.6万亿下（确认离场）',
            '2️⃣ 跌停止血：跌停能否收敛至10家内；若仍＞15家，恐慌在续',
            '3️⃣ 硬件/科技止跌：半导体、PCB、HBM今日领跌，节后能否修复；不修复则转弱可能升',
            '4️⃣ 避险抱团延续：风电、减速器、港口、煤炭高标能否接着走；抱团加强＝防守共识，松散＝避险仅短线',
        ]),
        ph("outlook", "节后（10/8）四桩观察：量能回2万亿？跌停止血？硬件止跌？抱团延续？"),
        (f'<section style="background:{ACCENT};padding:16px 20px;margin:18px 0;text-align:center;color:#FFFFFF;'
         f'font-size:18px;font-weight:900;letter-spacing:2px;">欲知后事如何，且听下回分解</section>'),
        vo("欲知后事如何，且听下回分解。"),
        (f'<section style="background:{CARD};border:1.5px solid {LINE};padding:14px 18px;'
         f'margin:18px 0;font-size:14px;color:{INK};line-height:1.9;text-align:center;">'
         f'觉得有用？👍 点个<strong style="color:{ACCENT};">赞</strong>，↗️ <strong style="color:{ACCENT};">转发</strong>'
         f'给身边炒股的朋友，⭐ <strong style="color:{ACCENT};">星标</strong>不迷路</section>'),
        (f'<section style="background:#EDE8DC;padding:12px 14px;margin:18px 0;'
         f'color:#8b8f92;font-size:12px;line-height:1.8;">信息整理，不构成投资建议。股市有风险，入市需谨慎。</section>'),
        (f'<section style="background:{CARD};border:1.5px solid {LINE};padding:14px 16px;'
         f'margin:18px 0;font-size:14px;color:{INK};line-height:2;">'
         f'<b style="color:{ACCENT};">📚 前情回顾（点击回看）</b><br>'
         f'📅 9月23日｜成交缩了3700亿，方向没变（链接群发后补）<br>'
         f'📅 9月22日｜涨停砍半、钱多一千亿，方向没变（链接群发后补）<br>'
         f'📅 9月21日｜103家涨停，科技跌不到1%，涨多了歇口气（链接群发后补）<br>'
         f'📅 9月18日｜放量2.08万亿站上3900，剥掉所有热点只剩一个方向（链接群发后补）</section>'),
        (f'<section style="background:{CARD};border:1.5px solid {LINE};padding:14px 16px;'
         f'margin:18px 0;font-size:14px;color:{INK};line-height:1.9;">'
         f'<b style="color:{ACCENT};">双节十三天休市，你选择持股还是持币？评论区聊聊</b> 👇<br>'
         f'<span style="font-size:13px;color:{TEXT};">#A股复盘 #每日复盘 #上证指数 #板块轮动</span></section>'),
    ]
    return wrap_leaf("".join(parts))


def main():
    content = build_content()
    out = BASE / "公众号预览.html"
    out.write_text(content, encoding="utf-8")
    print(f"✅ 公众号预览.html 落盘: {out}（{len(content)} 字符）")


if __name__ == "__main__":
    main()
