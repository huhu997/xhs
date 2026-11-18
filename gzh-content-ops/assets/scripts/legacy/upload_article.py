#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9/22 盘面长文 → 公众号 news 草稿箱（官方 API）

流程：token → 传 9 张永久素材 → 拼内联样式 HTML → draft/add
风格：swiss-blue（米白 #FAFAF8 底 / 深蓝 #002FA7 / 近黑 #0A0A0A / 零圆角 / 发丝线）
涨跌：正=深蓝 #002FA7，负=绿 #237A57（与当日配图同约定）
封面：1600x900 → 2.35:1 中心横带 / 1:1 中心方块
用法：
    python upload_article.py --dry-run   # 只拼 HTML 落盘（供校验）
    python upload_article.py             # 真投递
"""
import json, pathlib, re, sys, time

sys.path.insert(0, r"F:/桌面/zcode工作区/_wx_read")
from news_publish import http_json, load_creds, get_token

BASE = pathlib.Path(__file__).resolve().parent
API = "https://api.weixin.qq.com/cgi-bin"
TITLE = "A股每日复盘｜涨停砍半、钱多一千亿，方向没变（9.22）"
DIGEST = ("沪指微涨0.06%收3952.13，成交2.14万亿。涨停从103家砍到63家，成交反而多出约1040亿——"
          "节前在换手，不是在撤退。判断和昨天一样：方向没变，三个锚是排期、采购、合同。")
BG = "#FAFAF8"; INK = "#0A0A0A"; TEXT = "#4A4A48"; ACCENT = "#002FA7"; ACCENT2 = "#8C8C86"
LINE = "#D8D8D4"; CARD = "#F0F0EE"; PILL = "#E3E8F5"; MISS = "#8A8A85"
UP = "#002FA7"; DN = "#237A57"     # 本日约定：正=深蓝，负=绿
IMAGES = ["cover", "data", "verify", "money", "chain", "clues", "holiday", "outlook", "share"]
BODY = ["data", "verify", "money", "chain", "clues", "holiday", "outlook", "share"]
CROP_235 = [0, 0.119, 1, 0.881]
CROP_11 = [0.221, 0, 0.779, 1]


def upload_img_with_url(token, path):
    path = pathlib.Path(path)
    boundary = "----zcode" + str(int(time.time() * 1000)) + str(path.stem)
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="media"; filename="{path.name}"\r\n'.encode()
    body += b"Content-Type: image/png\r\n\r\n"
    body += path.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    r = http_json(f"{API}/material/add_material?access_token={token}&type=image",
                  data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    if "media_id" not in r:
        raise SystemExit(f"❌ 上传 {path.name} 失败: {r}")
    return r["media_id"], r.get("url", "")


def p(text, size=16, color=TEXT, bold=False):
    w = "font-weight:bold;" if bold else ""
    return f'<p style="font-size:{size}px;color:{color};{w}line-height:1.8;margin:0 0 14px;">{text}</p>'


def h2(t):
    return (f'<section style="font-size:17px;font-weight:bold;color:{INK};border-left:4px solid {ACCENT};'
            f'padding-left:10px;margin:28px 0 12px;line-height:1.5;">{t}</section>')


def img_tag(url):
    return (f'<section style="margin:18px 0;text-align:center;">'
            f'<img src="{url}" style="width:100%;display:block;" /></section>')


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


def askbox(html):
    return (f'<section style="background:{CARD};border:1.5px solid {LINE};'
            f'padding:14px 16px;margin:18px 0;font-size:15px;color:{INK};line-height:1.9;">{html}</section>')


def layerbox(no, title, html):
    return (f'<section style="background:{CARD};border:1.5px solid {LINE};border-left:4px solid {ACCENT};'
            f'padding:14px 16px;margin:0 0 14px;">'
            f'<p style="font-size:13px;font-weight:800;color:{ACCENT};margin:0 0 6px;letter-spacing:1px;">'
            f'{no} · {title}</p>'
            f'<p style="font-size:14px;color:{INK};margin:0;line-height:1.9;">{html}</p></section>')


def rowbox(rows):
    body = "<br>".join(rows)
    return (f'<section style="background:{CARD};border:1.5px solid {LINE};'
            f'padding:14px 16px;margin:0 0 14px;font-size:14px;color:{INK};line-height:2.0;">{body}</section>')


def warnbox(html):
    return (f'<section style="background:#EDF0F7;border:1.5px solid #C8D2E8;padding:13px 16px;'
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


def build_content(u):
    strong = lambda s: f'<strong style="color:{INK};">{s}</strong>'
    bl = lambda s: f'<strong style="color:{ACCENT};">{s}</strong>'
    dnn = lambda s: f'<strong style="color:{DN};">{s}</strong>'
    img = lambda n: img_tag(u[n])
    parts = [
        # 头部 hero
        (f'<section style="background:{ACCENT};padding:24px 20px;margin:0 0 16px;">'
         f'<p style="font-size:11px;letter-spacing:3px;color:#FFFFFF;font-weight:700;margin:0 0 6px;opacity:.92;">'
         f'A股每日复盘 · 2026.09.22 · swiss-blue</p>'
         f'<p style="font-size:22px;font-weight:900;color:#FFFFFF;margin:0;line-height:1.35;">'
         f'涨停砍半、钱多一千亿，方向没变</p>'
         f'<p style="font-size:12px;color:#FFFFFF;margin:8px 0 0;opacity:.88;">'
         f'⭐ 设为星标，每天18:30复盘准时送达</p></section>'),
        # 今日核心
        (f'<section style="background:{CARD};border-left:3px solid {ACCENT};'
         f'padding:12px 14px;margin:0 0 16px;border-top:1.5px solid {LINE};border-right:1.5px solid {LINE};'
         f'border-bottom:1.5px solid {LINE};">'
         f'<p style="font-size:12px;font-weight:800;color:{ACCENT};margin:0 0 4px;">⚠ 今日核心</p>'
         f'<p style="font-size:13px;color:{INK};margin:0;line-height:1.75;">'
         f'今天先说结论：{strong("节前这波换手，改的是报价，不是方向。")}'
         f'先看两个对不上的数字。涨停家数从昨天的{strong("103家")}掉到今天{strong("63家")}，几乎砍半；'
         f'可两市成交额不但没缩，反而从2.03万亿放大到{strong("2.14万亿")}，多出来约{strong("1040亿")}。'
         f'一边是“敢在高位继续往里冲的人在变少”，一边是“钱却变多了”。这两个数字同时出现，只指向一件事：'
         f'{strong("市场在换手，不是在撤退。")}'
         f'所以今天要回答的只有一个问题：{strong("节前的这笔换手，是避险，还是提前站位？")}</p></section>'),
        # KPI
        ('<section style="display:flex;gap:8px;margin:0 0 16px;">'
         + kpi("3952.13", "上证指数 +0.06%")
         + kpi("2.14万亿", "两市成交额", hl=True)
         + kpi("63家", "涨停 · 跌停3家")
         + '</section>'),
        img("data"),
        h2("📊 大盘表现：指数没动，里面很忙"),
        (f'<section style="font-size:13px;color:{INK};line-height:2.1;background:{CARD};'
         f'border:1.5px solid {LINE};padding:12px 16px;margin:0 0 14px;">'
         f'上证指数 <b>3952.13</b> <span style="color:{UP};font-weight:800;">+0.06%</span><br>'
         f'深证成指 <b>13723.74</b> <span style="color:{DN};font-weight:800;">-0.05%</span><br>'
         f'创业板指 <b>3399.93</b> <span style="color:{UP};font-weight:800;">+0.01%</span><br>'
         f'科创50 <b>1665.04</b> <span style="color:{UP};font-weight:800;">+0.46%</span><br>'
         f'北证50 <b>1046.80</b> <span style="color:{DN};font-weight:800;">-1.08%</span>'
         f'</section>'),
        p(strong("三个反常点："), 14, INK),
        p(f'① {strong("四条指数线几乎贴在昨天的收盘价上，但个股的位置动得很厉害。")}全市场5354只样本里，'
          f'{dnn("下跌2910家")}、{bl("上涨2310家")}——跌的比涨的多了约600家。指数原地不动，里面的座次换了一轮。', 14),
        p(f'② {strong("成交额放大到2.14万亿，是近期偏高的位置。")}一个值得记住的区别：'
          f'{strong("缩量才叫避险，放量说明钱在换手。")}今天属于后者。', 14),
        p(f'③ {strong("领涨的行业从“硬件”换成了“软件”。")}传媒{bl("+1.79%")}、计算机{bl("+1.41%")}排在行业前两位；'
          f'而交通运输{dnn("-1.17%")}、钢铁{dnn("-0.95%")}、建筑材料{dnn("-0.92%")}排在最后。', 14),
        p("一句话：" + strong("今天指数几乎没走，但内部完成了一次换仓。"), 14),
        h2("✅ 昨日观察点回看（3条应验，1条一半——而且又换了方向）"),
        p("老规矩：昨天给的是4个" + strong("条件") + "，不是4个" + strong("预测") + "。回看是看市场满足了哪些。", 14),
        rowbox([
            f'1️⃣ 量能能不能守住，2万亿上方＝钱还在场内 → <b style="color:{ACCENT};">✅ 应验</b>：两市成交约2.14万亿，不但守住，还比昨天多出约1040亿',
            f'2️⃣ 半导体设备、封测能否止跌回正；PCB、光模块能否连续第二天为正 → <b style="color:{ACCENT2};">⚠️ 一半</b>：PCB <b>+0.39%</b> 连续第二天为正 ✅；但半导体设备 -0.25%、先进封装 -0.30% 仍未回正，光模块那头（CPO -0.08%、光芯片 -1.21%）还转弱了',
            f'3️⃣ 云栖大会（9月22日开幕）有没有实质内容 → <b style="color:{ACCENT};">✅ 应验，而且是最硬的一条</b>：新芯片给了算力倍数、量产时间和客户数，不是只有概念',
            f'4️⃣ 情绪的高度：能否走出6板；跌停是否还在3家以内 → <b style="color:{ACCENT};">✅ 应验</b>：最高6板出现，梯队完整；跌停3家，刚好在3家以内',
        ]),
        p(f'第2条要展开说，因为它是今天全篇的钥匙。昨天我写“科技内部的钱分两路跑”。今天答案出来了，但'
          f'{strong("换了个方向")}：PCB确实连续第二天为正，可半导体设备和先进封装还是没回正，光模块那一头反而转弱。'
          f'与此同时，软件、云、大数据这一头全线走强。<br>'
          f'所以钱不是从科技里出来，是在科技内部又换了一次座位：'
          + strong("从硬件，搬到了软件。"), 14),
        img("verify"),
        h2("💰 资金去向：钱从哪来，到哪去"),
        p(f'{strong("今天走强的那一头：")}超级计算机{bl("+2.21%")}、聊天机器人概念+2.02%、云计算{bl("+1.54%")}、'
          f'智能音箱+1.50%、国产软件{bl("+1.41%")}、大数据+1.29%、网络安全+1.22%、人工智能+1.00%。', 14),
        p(f'{strong("今天走弱的那一头：")}交通运输{dnn("-1.17%")}、钢铁-0.95%、建筑材料-0.92%、国防军工-0.85%；'
          f'概念端是 航运-1.08%、超硬材料-1.26%、培育钻石-1.69%。', 14),
        p(f'看这组对照，钱的偏好变化很清楚：{strong("从“周期的、看得见产能的”地方，搬到“算力的、用得上的”地方。")}', 14),
        p(f'而昨天领涨的那几块硬件——半导体设备{dnn("-0.25%")}、材料-0.53%、光刻机-0.54%、存储器-0.35%——'
          f'跌幅依然{strong("没有超过1%")}。{strong("这个细节很重要：它们是被暂时放下，不是被扔掉。")}', 14),
        img("money"),
        h2("🔄 换座位的三段路：钱从哪来、到哪去"),
        layerbox("链条一", "全球这一头：AI 的算力需求从“回答”挪到了“执行任务”",
                 f'隔夜海外科技股集体走强：纳指涨{strong("2.26%")}创收盘新高，费城半导体指数涨{strong("4.29%")}。'
                 f'但涨得最猛的，是做CPU的那几家——英特尔{bl("+12.14%")}、Arm{bl("+17.16%")}、AMD{bl("+9.95%")}。<br>'
                 f'为什么是CPU而不是GPU？因为这一轮跑量的AI产品，是{strong("智能体（Agentic AI）")}：'
                 f'它要替你开网页、编译程序、跑定时任务、调度一屋子子任务。这些活在系统里来回倒腾，'
                 f'更吃CPU和调度能力，不是单纯堆GPU就够。<br>'
                 f'市场里被反复引用的一条估算是：AI的算力配比，'
                 f'{strong("训练阶段CPU:GPU约1:8，推理阶段约1:4，到了智能体阶段可能到1:1甚至更高。")}<br>'
                 f'这条链的性质：{strong("需求的结构在变，不只是总量在涨。")}'),
        img("chain"),
        layerbox("链条二", "国内这一头：今天的大会直接把“智能体”写成了主题",
                 f'云栖大会今天开幕，核心锚点就是智能体。落地的硬东西有几样：<br>'
                 f'· <b>一颗新芯片</b>：真武V900，算力是上一代的{strong("3倍")}，216GB大内存、1200GB/s互联带宽，'
                 f'原生支持低精度计算，{strong("单集群可扩到50万卡")}，2027年一季度量产，已服务650多家企业客户。<br>'
                 f'· <b>一个规模目标</b>：{strong("2032年数据中心规模超过20GW")}，约是2022年的10倍；'
                 f'未来三年投入{strong("3800亿")}。<br>'
                 f'· <b>一套架构</b>：芯片、云、模型、模型服务、智能体应用，五层打通。<br>'
                 f'· <b>一条需求侧</b>：超节点单节点可扩到{strong("4096卡")}、约8 EFLOPS、约1PB内存；'
                 f'有券商测算，某头部模型公司的国产加速器采购计划{strong("至少16万颗")}。<br>'
                 f'这条链的性质：{strong("从“概念发布”走到了“排产表、硬指标、客户数”。")}'),
        layerbox("链条三", "存储那条链没有断，只是今天没轮到它报价",
                 f'昨天写过的合同、库存不足10天、四季度续涨——今天存储器{dnn("-0.35%")}、'
                 f'高带宽存储器{bl("+0.31%")}，基本原地踏步。<br>'
                 f'{strong("合同不因为一天的换手而改写。")}'),
        h2("🔍 换个视角：四条辅助线索"),
        p(f'{strong("线索一：昨天涨停的101只，今天表现不差。")}{bl("60只上涨（59.4%）")}、{bl("25只再涨停")}，'
          f'涨幅中位数+1.31%、平均+2.47%。接力还在，只是不如前两天猛。', 14),
        p(f'{strong("线索二：高度还在往上走。")}63家涨停拆开看：首板{strong("39家")}、2板17家、3板4家、4板1家、'
          f'5板1家、{strong("6板1家")}——梯队是完整的，跌停只有3家。{strong("情绪没崩，只是不再拥挤。")}', 14),
        p(f'{strong("线索三：弱的是“老经济”那一头。")}交通运输{dnn("-1.17%")}、钢铁-0.95%、建筑材料-0.92%，'
          f'加上概念里的航运-1.08%、波罗的海干散货指数-2.70%。', 14),
        p(f'{strong("线索四：杠杆资金没走。")}截至昨天（9月21日）的融资余额{strong("2.62万亿")}，'
          f'当天净买入{bl("141.88亿")}；从9月14日的低点算起，五个交易日回升约{strong("252亿")}。', 14),
        img("clues"),
        h2("🧧 节前的那点心思"),
        p(f'今年的节前有点特别：{strong("假期不是一段，是两段，中间只夹着三个交易日。")}', 14),
        p(f'先是中秋——{strong("本周五（9月25日）起休市")}，下周一（9月28日）回来；紧接着是国庆——'
          f'{strong("10月1日到10月7日休市")}，10月8日才开市。', 14),
        p(f'算下来，从明天起到长假开始，{strong("中间只剩5个交易日")}（9/23、9/24、9/28、9/29、9/30），'
          f'其中长假前那一周{strong("只有3天")}。', 14),
        img("holiday"),
        p(f'这个时间表，把“持股还是持币”这道老题，拆成了三道小题：三天小长假怎么过、'
          f'夹在中间那三个交易日怎么办、七天大长假又怎么安排。而今天盘面把这个心思写得很直白：', 14),
        rowbox([
            f'· <b>愿意在高位继续往里冲的人，变少了。</b>涨停从103家掉到63家，最高只有6板，没有出现那种越涨越疯的梯队。',
            f'· <b>愿意彻底离场的人，也不多。</b>成交额放大到2.14万亿，融资余额截至昨天还在净增142亿——'
            f'真要是避险，这两根柱子应该一起往下走。',
            f'· <b>大家真正在做的是“挑位置”。</b>卖掉既没有事件、也没有涨价支撑的地方，留下看得懂的。',
        ]),
        p(f'所以节前最典型的心态，既不是贪婪，也不是恐慌，而是{strong("降低“猜”的比例，提高“等”的比例")}'
          f'——宁可少赚一点，也不愿意在假期里抱着一个说不清楚的东西。', 14),
        p(f'有意思的是：{strong("报价会被情绪推着走，但持有的人心里那杆秤，是自己调的。")}'
          f'而这杆秤，跟中长线方向没什么关系。{strong("假期能改变资金的节奏，改变不了产业的排期。")}', 14),
        h2("🎯 明日观察点（下篇验证）"),
        rowbox([
            '1️⃣ 量能的走向：2万亿上方＝换手继续；跌破2万亿＝节前真的开始缩量观望',
            '2️⃣ 软件、云这一头能不能接住：云计算、国产软件、大数据能否连续第二天为正；半导体设备、CPO、光芯片能否止跌',
            '3️⃣ 大会第二日（9月23日）：有没有新的产品或订单落地；只剩重复概念＝消息面提前用掉',
            '4️⃣ 节前情绪的高度：涨停家数能否回到80家上方；最高板能否走到7板；跌停是否还在3家以内',
        ]),
        img("outlook"),
        h2("⚖️ 写在最后"),
        p("先把话说清楚：" + strong("今天我的判断和昨天一样——方向不变。"), 14),
        p("昨天我写：" + strong("涨多了歇口气，不代表行情换了方向。"), 14),
        p("今天市场把这道题往前推了一步：" + strong("节前这笔换手，会不会把方向也换掉？"), 14),
        p("答案还是不变，理由不是“信心”，而是三个可以自己去查的东西：", 14),
        p(strong("一是供给端的排期") + "——芯片定在2027年一季度量产，数据中心定在2032年20GW，三年投入3800亿；", 14),
        p(strong("二是需求端的采购") + "——超节点单节点4096卡，头部模型公司的国产加速器采购计划至少16万颗；", 14),
        p(strong("三是价格端的合同") + "——存储签的是合同，不是情绪。", 14),
        p("这三样东西的排期，" + strong("不会因为长假少交易几天而改变。"), 14),
        spotlight("至于明天涨还是跌、该买还是该卖、什么价位——这三个问题我不回答，也不该由我回答。我只负责把棋盘摆清楚。"),
        p("明天收盘，上面四条观察点，逐条对账。", 14),
        img("share"),
        (f'<section style="background:{CARD};border:1.5px solid {LINE};padding:14px 18px;'
         f'margin:18px 0;font-size:14px;color:{INK};line-height:1.9;text-align:center;">'
         f'觉得有用？👍 点个<strong style="color:{ACCENT};">赞</strong>，↗️ <strong style="color:{ACCENT};">转发</strong>'
         f'给身边炒股的朋友，⭐ <strong style="color:{ACCENT};">星标</strong>不迷路</section>'),
        (f'<section style="background:#EFEFEC;padding:12px 14px;margin:18px 0;'
         f'color:#8b8f92;font-size:12px;line-height:1.8;">信息整理，不构成投资建议。股市有风险，入市需谨慎。</section>'),
        (f'<section style="background:{CARD};border:1.5px solid {LINE};padding:14px 16px;'
         f'margin:18px 0;font-size:14px;color:{INK};line-height:2;">'
         f'<b style="color:{ACCENT};">📚 往期复盘（点击回顾）</b><br>'
         f'📅 9月21日｜103家涨停，科技跌不到1%，涨多了歇口气（链接群发后补）<br>'
         f'📅 9月18日｜放量2.08万亿站上3900，剥掉所有热点只剩一个方向（链接群发后补）<br>'
         f'📅 9月17日｜一条运河通航了，钱也在换地方（链接群发后补）<br>'
         f'📅 9月16日｜放量大涨、89家涨停，很多人选择“满仓”（链接群发后补）</section>'),
        askbox(f'<b style="color:{ACCENT};">这个长假，你打算持股还是持币？评论区聊聊</b> 👇<br>'
               f'<span style="font-size:13px;color:{TEXT};">#A股复盘 #每日复盘 #上证指数 #板块轮动</span>'),
    ]
    return wrap_leaf("".join(parts))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv
    if dry:
        content = build_content({k: f"__{k}_URL__" for k in IMAGES})
        out = BASE / "_content_dryrun.html"
        out.write_text(content, encoding="utf-8")
        print(f"✅ dry-run 落盘: {out}（{len(content)} 字符）")
        return

    creds = load_creds()
    token = get_token(creds["WECHAT_APP_ID"], creds["WECHAT_APP_SECRET"])
    print("token OK")
    missing = [n for n in IMAGES if not (BASE / f"{n}.png").exists()]
    if missing:
        raise SystemExit(f"❌ 缺图: {missing}")

    urls, ids = {}, {}
    for name in IMAGES:
        mid, url = upload_img_with_url(token, BASE / f"{name}.png")
        urls[name], ids[name] = url, mid
        print(f"{name}: media_id={mid[:18]}… url={url[:46]}…")

    content = build_content(urls)
    (BASE / "article_body.html").write_text(content, encoding="utf-8")

    payload = {"articles": [{
        "title": TITLE, "author": "", "digest": DIGEST, "content": content,
        "content_source_url": "", "thumb_media_id": ids["cover"],
        "need_open_comment": 0, "only_fans_can_comment": 0,
        "pic_crop_235_1": CROP_235, "pic_crop_1_1": CROP_11,
    }]}
    print("正在创建草稿…")
    r = http_json(f"{API}/draft/add?access_token={token}",
                  data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                  headers={"Content-Type": "application/json; charset=utf-8"})
    print("draft/add 结果:", r)
    if r.get("media_id"):
        (BASE / "draft_id.txt").write_text(r["media_id"], encoding="utf-8")
        print("草稿 media_id 已存 draft_id.txt")


if __name__ == "__main__":
    main()
