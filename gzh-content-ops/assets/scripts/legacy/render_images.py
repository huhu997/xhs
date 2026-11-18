#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9/17 盘面长文 · 9张配图 HTML→PNG（swiss-blue 瑞士国际主义 · 1600x900 @2x）
规则：A股红涨绿跌（红=涨 #C0392B，绿=跌 #1E7A4C）；主题色 #002FA7 只做品牌/结构色；零圆角 + 发丝线。
所有数字均为 2026-09-17 收盘、多源核实值。
封面安全区：2.35:1 中心横带 y107-793 / 1:1 中心方块 x354-1246 → 内容全部锁在 x354-1246、y107-793 内。
"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1600px;height:900px;overflow:hidden}
body{background:#FAFAF8;font-family:"Microsoft YaHei UI","Microsoft YaHei",sans-serif;color:#0A0A0A;
     position:relative;padding:52px 68px;}
.tag{font-size:20px;color:#5A5A5A;letter-spacing:4px}
.tag b{color:#002FA7}
h2{font-size:38px;font-weight:800;margin:8px 0 26px;letter-spacing:1px}
.card{background:#FFFFFF;border:1.5px solid #D4D4D2}
.up{color:#C0392B;font-weight:800}
.dn{color:#1E7A4C;font-weight:800}
.flat{color:#5A5A5A;font-weight:800}
.foot{position:absolute;left:68px;right:68px;bottom:32px;font-size:19px;color:#8A8A8A;
      border-top:1.5px solid #D4D4D2;padding-top:14px;display:flex;justify-content:space-between}
.foot b{color:#002FA7}
"""

# ---------- 1. 封面（1600x900；内容锁在 x354-1246 / y107-793）----------
COVER = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><style>{CSS}
body{{display:flex;align-items:center;justify-content:center;padding:0}}
.box{{width:860px;text-align:left}}
.lab{{font-size:21px;letter-spacing:5px;color:#002FA7;font-weight:800;margin-bottom:20px}}
.big{{font-size:96px;font-weight:900;color:#0A0A0A;line-height:1.18;letter-spacing:1px}}
.big em{{font-style:normal;color:#002FA7}}
.sub{{font-size:40px;font-weight:800;color:#0A0A0A;margin-top:6px;letter-spacing:2px}}
.rule{{height:6px;background:#002FA7;width:132px;margin:22px 0 18px}}
.line{{font-size:25px;color:#2E2E2E;letter-spacing:1px;font-weight:700}}
.chips{{margin-top:26px;display:flex;gap:10px}}
.chip{{border:1.5px solid #D4D4D2;background:#FFFFFF;padding:10px 14px;min-width:0}}
.chip .n{{font-size:17px;color:#5A5A5A;font-weight:700}}
.chip .v{{font-size:24px;font-weight:900;margin-top:3px;color:#0A0A0A}}
.chip .v.dn{{color:#1E7A4C}}
.chip .v.up{{color:#C0392B}}
</style></head><body>
<div class="box">
  <div class="lab">A 股 每 日 复 盘 · 2 0 2 6 . 0 9 . 1 7</div>
  <div class="big">一条运河<em>通航了</em></div>
  <div class="sub">钱，也在换地方</div>
  <div class="rule"></div>
  <div class="line">134.2 公里 · 5000 吨级 · 总投资约 727 亿</div>
  <div class="chips">
    <div class="chip"><div class="n">涨停家数</div><div class="v">89 <span style="color:#5A5A5A;">→</span> 47</div></div>
    <div class="chip"><div class="n">两市成交</div><div class="v">1.82万亿</div></div>
    <div class="chip"><div class="n">贵金属</div><div class="v dn">-5.35%</div></div>
  </div>
</div>
</body></html>"""

# ---------- 2. 数据总览 ----------
DATA = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><style>{CSS}
.idx{{display:flex;gap:10px;margin-bottom:18px}}
.idx .c{{flex:1;padding:14px 10px;text-align:center}}
.idx .c .n{{font-size:19px;color:#5A5A5A;font-weight:700}}
.idx .c .p{{font-size:32px;font-weight:900;margin:5px 0 2px;color:#0A0A0A}}
.idx .c .v{{font-size:22px;font-weight:800}}
.chips{{display:flex;gap:10px;margin-bottom:18px}}
.chips .c{{flex:1;padding:12px 10px;text-align:center;background:#F0F0EE;border:1.5px solid #D4D4D2}}
.chips .c .v{{font-size:29px;font-weight:900;color:#0A0A0A}}
.chips .c .k{{font-size:17px;color:#002FA7;margin-top:3px;font-weight:700}}
.pts{{display:flex;gap:12px}}
.pts .c{{flex:1;padding:14px 16px;font-size:19px;line-height:1.7;color:#0A0A0A}}
.pts .c b{{color:#002FA7}}
</style></head><body>
<div class="tag">9/17 收盘 · <b>多源核实</b></div>
<h2>指数小跌，内部换人</h2>
<div class="idx">
  <div class="card c"><div class="n">上证指数</div><div class="p">3875.60</div><div class="v dn">-0.41%</div></div>
  <div class="card c"><div class="n">深证成指</div><div class="p">13409.91</div><div class="v dn">-0.33%</div></div>
  <div class="card c"><div class="n">创业板指</div><div class="p">3298.31</div><div class="v dn">-0.40%</div></div>
  <div class="card c" style="border:2.5px solid #002FA7;"><div class="n">科创50</div><div class="p">1606.29</div><div class="v dn">-0.61%</div></div>
  <div class="card c"><div class="n">北证50</div><div class="p">1026.00</div><div class="v dn">-1.37%</div></div>
</div>
<div class="chips">
  <div class="card c"><div class="v">1.82万亿</div><div class="k">成交 · 守住1.8万亿（缩160亿）</div></div>
  <div class="card c"><div class="v">2576 / 2820</div><div class="k">上涨 / 下跌（跌多涨少）</div></div>
  <div class="card c"><div class="v">47 / 1</div><div class="k">涨停 / 跌停（昨日 89/4）</div></div>
</div>
<div class="pts">
  <div class="card c"><b>① 量守住了 但没放大</b><br>1.82万亿，是"修复继续"的最低要求</div>
  <div class="card c"><b>② 涨停接近腰斩</b><br>89家 → 47家，情绪退潮看得见</div>
  <div class="card c"><b>③ 涨的换了人</b><br>种子+7.86%、汽车、医药在涨；贵金属-5.35%、科技硬件回调</div>
</div>
<div class="foot"><span>数据：沪深两市收盘 · 2026-09-17</span><span><b>A股每日复盘</b></span></div>
</body></html>"""

# ---------- 3. 昨日观察点回看 ----------
VERIFY = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><style>{CSS}
h2{{margin-bottom:6px}}
.sub{{font-size:21px;color:#5A5A5A;margin-bottom:18px}}
.row{{display:flex;align-items:center;gap:16px;padding:15px 20px;margin-bottom:10px}}
.row .num{{font-size:26px;font-weight:900;color:#002FA7;width:44px}}
.row .cond{{flex:1;font-size:22px;font-weight:700;color:#0A0A0A;line-height:1.5}}
.row .res{{width:520px;font-size:20px;line-height:1.55;color:#2E2E2E}}
.badge{{display:inline-block;font-size:18px;font-weight:900;padding:3px 10px;margin-right:8px;color:#FFFFFF;background:#002FA7}}
.badge.half{{background:#7A7A7A}}
.sum{{margin-top:14px;padding:16px 20px;font-size:23px;line-height:1.7;background:#002FA7;color:#FFFFFF}}
.sum b{{color:#FFFFFF;border-bottom:2.5px solid #FFFFFF}}
</style></head><body>
<div class="tag">观察点回看 · <b>条件不是预测</b></div>
<h2>昨日观察点回看：1条应验，3条只对了一半</h2>
<div class="sub">昨天给的是 4 个条件，不是 4 个预测——回看是看市场满足了哪些</div>
<div class="card row"><div class="num">01</div>
  <div class="cond">量能：能否守住 1.8 万亿</div>
  <div class="res"><span class="badge">应验</span>1.82万亿守住了（比昨天缩160亿）</div></div>
<div class="card row"><div class="num">02</div>
  <div class="cond">电子/半导体净流入连续为正</div>
  <div class="res"><span class="badge half">一半</span>科创50收1606站住了，但电子净流出126.68亿</div></div>
<div class="card row"><div class="num">03</div>
  <div class="cond">涨停维持 50 家以上</div>
  <div class="res"><span class="badge half">打折</span>跌停1家达标，但涨停只有47家，差3家</div></div>
<div class="card row"><div class="num">04</div>
  <div class="cond">议息的"不重要"测试</div>
  <div class="res"><span class="badge half">分地方</span>指数跌0.41%抗住了，贵金属被砸超5%</div></div>
<div class="sum">指数的修复还在，但<b>资金的进攻退潮了</b>——这条，比任何观点都实在。</div>
</body></html>"""

# ---------- 4. 资金去向 ----------
MONEY = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><style>{CSS}
h2{{margin-bottom:20px}}
.flow{{display:flex;align-items:stretch;gap:14px}}
.col{{flex:1;padding:18px 20px}}
.col h3{{font-size:24px;margin-bottom:12px;letter-spacing:1px}}
.row2{{display:flex;justify-content:space-between;font-size:22px;padding:9px 0;border-bottom:1px dashed #D4D4D2}}
.row2:last-child{{border-bottom:none}}
.row2 .nm{{color:#0A0A0A;font-weight:700}}
.mid{{width:110px;display:flex;flex-direction:column;justify-content:center;align-items:center;color:#002FA7}}
.mid .ar{{font-size:50px;line-height:1.18}}
.mid .t{{font-size:19px;font-weight:800;margin-top:8px;letter-spacing:2px}}
.lead{{background:#F0F0EE;border:2.5px solid #002FA7}}
.sum{{margin-top:20px;padding:16px 20px;font-size:23px;line-height:1.7;color:#0A0A0A;background:#FFFFFF;border:1.5px solid #D4D4D2}}
.sum b{{color:#002FA7}}
</style></head><body>
<div class="tag">资金动向 · <b>行业主力净流入</b></div>
<h2>不是撤退，是换仓</h2>
<div class="flow">
  <div class="card col">
    <h3 style="color:#1E7A4C;">▼ 流出：涨多了的</h3>
    <div class="row2"><span class="nm">电子</span><span class="dn">-126.68亿</span></div>
    <div class="row2"><span class="nm">元件</span><span class="dn">-80.96亿</span></div>
    <div class="row2"><span class="nm">有色金属</span><span class="dn">-65.73亿</span></div>
    <div class="row2"><span class="nm">印制电路板</span><span class="dn">-62.98亿</span></div>
    <div class="row2"><span class="nm">贵金属</span><span class="dn">-16.57亿</span></div>
  </div>
  <div class="mid"><div class="ar">→</div><div class="t">换 仓</div></div>
  <div class="card col lead">
    <h3 style="color:#C0392B;">▲ 流入：还没涨的</h3>
    <div class="row2"><span class="nm">汽车</span><span class="up">+37.08亿</span></div>
    <div class="row2"><span class="nm">汽车零部件</span><span class="up">+30.40亿</span></div>
    <div class="row2"><span class="nm">面板</span><span class="up">+23.09亿</span></div>
    <div class="row2"><span class="nm">医药生物</span><span class="up">+15.76亿</span></div>
    <div class="row2"><span class="nm">航运</span><span class="up">+7.15亿</span></div>
  </div>
</div>
<div class="sum">从涨多了的地方（贵金属、科技硬件），搬到没怎么涨、有涨价逻辑或低位修复的地方——<b>弱市里，钱比人先求安全边际</b>。</div>
<div class="foot"><span>数据：行业主力净流入（收盘口径）</span><span><b>A股每日复盘</b></span></div>
</body></html>"""

# ---------- 5. 平陆运河 ----------
CANAL = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><style>{CSS}
h2{{margin-bottom:8px}}
.sub{{font-size:22px;color:#5A5A5A;margin-bottom:20px;font-weight:700}}
.diagram{{position:relative;height:150px;border:1.5px solid #D4D4D2;background:#FFFFFF;margin-bottom:18px;
         display:flex;align-items:center;padding:0 30px}}
.arrowline{{position:absolute;left:60px;right:60px;top:74px;height:6px;background:#002FA7}}
.dot{{position:absolute;top:64px;width:26px;height:26px;background:#002FA7;border:4px solid #FAFAF8}}
.ship{{position:absolute;top:44px;left:52%;font-size:30px;color:#0A0A0A}}
.p1{{left:44px}} .p2{{right:44px}}
.lab1{{position:absolute;top:104px;left:40px;font-size:19px;color:#2E2E2E;font-weight:700}}
.lab2{{position:absolute;top:104px;right:36px;font-size:19px;color:#2E2E2E;font-weight:700}}
.stats{{display:flex;gap:12px;margin-bottom:16px}}
.stats .c{{flex:1;padding:13px 14px;text-align:center}}
.stats .v{{font-size:32px;font-weight:900;color:#002FA7}}
.stats .k{{font-size:18px;color:#2E2E2E;margin-top:3px;font-weight:700}}
.hl{{padding:15px 20px;background:#002FA7;color:#FFFFFF;font-size:24px;font-weight:800;letter-spacing:1px}}
</style></head><body>
<div class="tag">意义 · <b>不只是一条河</b></div>
<h2>平陆运河：2026年9月16日正式通航</h2>
<div class="sub">新中国成立以来，第一条国家层面统筹建设的通江达海运河</div>
<div class="diagram">
  <div class="arrowline"></div>
  <div class="dot p1"></div><div class="dot p2"></div>
  <div class="ship">🚢</div>
  <div class="lab1">南宁横州 · 平塘江口</div>
  <div class="lab2">钦州 · 北部湾入海</div>
</div>
<div class="stats">
  <div class="card c"><div class="v">134.2<span style="font-size:20px;">公里</span></div><div class="k">全长</div></div>
  <div class="card c"><div class="v">5000<span style="font-size:20px;">吨级</span></div><div class="k">通航能力</div></div>
  <div class="card c"><div class="v">727<span style="font-size:20px;">亿元</span></div><div class="k">总投资</div></div>
  <div class="card c"><div class="v">4<span style="font-size:20px;">年多</span></div><div class="k">建设周期</div></div>
</div>
<div class="hl">航程缩短 560 公里以上 · 物流成本降 18%-30% · 年省超 50 亿元</div>
<div class="foot"><span>货走得更便宜，产业就会往哪里落——这笔账要用十年来算</span><span><b>A股每日复盘</b></span></div>
</body></html>"""

# ---------- 6. 文旅双节 ----------
CULTURE = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><style>{CSS}
h2{{margin-bottom:20px}}
.wrap{{display:flex;gap:16px;align-items:stretch}}
.left{{width:560px;padding:20px 22px}}
.left .hd{{font-size:20px;color:#5A5A5A;font-weight:700;letter-spacing:2px;margin-bottom:12px}}
.date{{display:flex;justify-content:space-between;align-items:center;font-size:24px;font-weight:800;color:#0A0A0A;
      padding:14px 16px;margin-bottom:10px;background:#002FA7;color:#FFFFFF}}
.date .d{{font-size:20px}}
.right{{flex:1;display:flex;flex-direction:column;gap:10px}}
.item{{padding:14px 18px;font-size:21px;line-height:1.55;color:#0A0A0A}}
.item b{{color:#002FA7}}
.item .n{{font-size:28px;font-weight:900;color:#002FA7}}
.strip{{margin-top:18px;padding:16px 22px;background:#002FA7;color:#FFFFFF;font-size:26px;font-weight:800;
        letter-spacing:1px;text-align:center}}
</style></head><body>
<div class="tag">双节 · <b>全国文旅在拼</b></div>
<h2>新运河在运货，千年大运河在迎客</h2>
<div class="wrap">
  <div class="card left">
    <div class="hd">假期日历</div>
    <div class="date"><span>中秋</span><span class="d">9月25-27日 · 3天</span></div>
    <div class="date"><span>国庆</span><span class="d">10月1-7日 · 7天</span></div>
    <div style="font-size:19px;color:#5A5A5A;line-height:1.7;margin-top:6px;">
      铁路双节运输 9月23日启动，日均开行约 1.3 万列</div>
  </div>
  <div class="right">
    <div class="card item"><span class="n">8亿+</span>　全国微短剧用户<br><span style="font-size:18px;color:#5A5A5A;">2025年市场规模突破千亿</span></div>
    <div class="card item"><span class="n">43万部</span>　前8个月上线微短剧<br><span style="font-size:18px;color:#5A5A5A;">是去年全年的13倍，其中AI剧超九成</span></div>
    <div class="card item"><span class="n">一天之内</span>　云南/宁夏/江苏/甘肃/湖北都在办推介<br><span style="font-size:18px;color:#5A5A5A;">江苏高邮：读千年邮驿往事，赏运河二分明月</span></div>
  </div>
</div>
<div class="strip">内容是文旅，文旅也是消费——人先动，钱才动</div>
</body></html>"""

# ---------- 7. 四条辅助线索 ----------
CLUES = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><style>{CSS}
h2{{margin-bottom:6px}}
.sub{{font-size:21px;color:#5A5A5A;margin-bottom:20px}}
.grid{{display:flex;flex-wrap:wrap;gap:12px}}
.g{{width:calc(50% - 6px);padding:17px 20px;min-height:158px}}
.g .no{{font-size:30px;font-weight:900;color:#002FA7;line-height:1.18}}
.g .t{{font-size:23px;font-weight:800;color:#0A0A0A;margin:6px 0 7px}}
.g .d{{font-size:19px;color:#2E2E2E;line-height:1.68}}
.g .d b{{color:#0A0A0A}}
</style></head><body>
<div class="tag">换个视角 · <b>四条辅助线索</b></div>
<h2>画面更完整的四个提醒</h2>
<div class="sub">不推翻结论，只是把另外几个视角也摆出来：</div>
<div class="grid">
  <div class="card g"><div class="no">01</div><div class="t">接力情绪明显降温</div>
    <div class="d">昨涨停89家，今仅 <b>36家上涨</b>（40.4%）、10家再涨停，<b>涨幅中位数-0.99%</b>；跌幅前列有昨天的热门面孔</div></div>
  <div class="card g"><div class="no">02</div><div class="t">黄金这次没"避险"</div>
    <div class="d">白银 <b>-6.00%</b>、贵金属 -5.35%、黄金 -5.15%——美联储加息25bp，美元回100、美债破5%</div></div>
  <div class="card g"><div class="no">03</div><div class="t">量还在，进攻退了</div>
    <div class="d">成交1.82万亿守住了，但电子净流出 <b>126.68亿</b>——同一笔钱，昨天买科技，今天买汽车和医药</div></div>
  <div class="card g"><div class="no">04</div><div class="t">涨的，都是"便宜的"</div>
    <div class="d">汽车+37.08亿、医药+15.76亿、航运+7.15亿、农业领涨——前期没涨、有涨价逻辑或低位修复</div></div>
</div>
<div class="foot"><span>口径：以上为市场观察线索，不构成投资建议</span><span><b>A股每日复盘</b></span></div>
</body></html>"""

# ---------- 8. 明日观察点 ----------
OUTLOOK = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><style>{CSS}
h2{{margin-bottom:6px}}
.sub{{font-size:21px;color:#5A5A5A;margin-bottom:20px}}
.grid{{display:flex;flex-wrap:wrap;gap:14px}}
.g{{width:calc(50% - 7px);padding:18px 20px;min-height:170px}}
.g .no{{font-size:34px;font-weight:900;color:#002FA7;line-height:1.18}}
.g .t{{font-size:24px;font-weight:800;color:#0A0A0A;margin:8px 0 8px}}
.g .d{{font-size:20px;color:#2E2E2E;line-height:1.7}}
.g .d b{{color:#0A0A0A}}
</style></head><body>
<div class="tag">观察点 · <b>下篇验证</b></div>
<h2>明天收盘，逐条对账</h2>
<div class="sub">不猜涨跌，只列可验证的量化条件：</div>
<div class="grid">
  <div class="card g"><div class="no">01</div><div class="t">量能能否继续守住</div>
    <div class="d">守住 <b>1.8万亿</b>＝震荡消化；跌破 <b>1.7万亿</b>＝退潮确认</div></div>
  <div class="card g"><div class="no">02</div><div class="t">新方向能不能接力</div>
    <div class="d">汽车/医药净流入能否<b>连续两天为正</b>——今天新进的方向，明天看是一日游还是接力</div></div>
  <div class="card g"><div class="no">03</div><div class="t">情绪的底在哪</div>
    <div class="d">涨停家数（今天 <b>47</b> 家）能否回到 <b>50家</b> 上方；跌停是否仍是1家上下</div></div>
  <div class="card g"><div class="no">04</div><div class="t">双节"节前效应"</div>
    <div class="d">距中秋只剩 <b>5个交易日</b>：旅游/传媒能否在指数震荡时继续逆势走强</div></div>
</div>
<div class="foot"><span>口径：以上为市场观察条件，不构成投资建议</span><span><b>A股每日复盘</b></span></div>
</body></html>"""

# ---------- 9. 赞转引导 ----------
SHARE = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><style>{CSS}
body{{display:flex;flex-direction:column;justify-content:center;align-items:center;padding:0}}
.t{{font-size:44px;font-weight:900;color:#0A0A0A;letter-spacing:2px}}
.s{{font-size:24px;color:#5A5A5A;margin-top:14px;letter-spacing:1px}}
.btns{{display:flex;gap:0;margin-top:44px;border:1.5px solid #002FA7}}
.b{{width:250px;height:220px;background:#002FA7;color:#FFFFFF;
   display:flex;flex-direction:column;justify-content:center;align-items:center;border-right:1.5px solid #FAFAF8}}
.b:last-child{{border-right:none}}
.b .i{{font-size:76px;line-height:1.18}}
.b .w{{font-size:30px;font-weight:800;margin-top:8px;letter-spacing:4px}}
.tagline{{margin-top:40px;font-size:22px;color:#002FA7;font-weight:800;letter-spacing:1px}}
</style></head><body>
<div class="t">盘面上是换人，盘面外是修路</div>
<div class="s">明天收盘，四条观察点逐条对账</div>
<div class="btns">
  <div class="b"><div class="i">👍</div><div class="w">点赞</div></div>
  <div class="b"><div class="i">↗</div><div class="w">转发</div></div>
  <div class="b"><div class="i">⭐</div><div class="w">星标</div></div>
</div>
<div class="tagline">A股每日复盘 · 每天18:30 · 设为星标不迷路</div>
</body></html>"""

PAGES = {"cover": COVER, "data": DATA, "verify": VERIFY, "money": MONEY,
         "canal": CANAL, "culture": CULTURE, "clues": CLUES, "outlook": OUTLOOK, "share": SHARE}

if __name__ == "__main__":
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
        for name, html in PAGES.items():
            htmlfile = BASE / f"_{name}.html"
            htmlfile.write_text(html, encoding="utf-8")
            page.goto(htmlfile.as_uri())
            page.wait_for_timeout(350)
            out = BASE / f"{name}.png"
            page.screenshot(path=str(out))
            print(f"OK {name}.png  {out.stat().st_size // 1024} KB")
        browser.close()
