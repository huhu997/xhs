# -*- coding: utf-8 -*-
"""合规风险检测引擎（公众号文章线 + 贴图线共用，单一词表来源）

设计目标（针对 2026-09-18 v1 被判违规那次暴露的三个真问题）：
  1. 信噪比：分级 BLOCK / WARN，不再让 77 条误伤淹没 2 个真触发点
  2. 覆盖面：涉政不靠硬编码清单，加「职位名 / 行程动词 / 政策动作」组合模式兜底
  3. 可挂链路：退出码 0/2，可直接当发布前硬闸门用（fail-closed）

分级：
  BLOCK = A 军事/冲突修辞 + B 涉政/地缘   → 必须改，会阻断发布
  WARN  = C 极限词 / D 荐股 / E 涨跌预测 / F 导流 / G 其他红线 → 人工判断，不阻断

误伤放行规则的两条铁律（踩过坑，别改回去）：
  · 行级规则（免责语境 / 资金流统计 / CSS）**只对 WARN 生效**，永不遮蔽 BLOCK
    ——否则「第一层：这是必争之地」会连真违规一起放行
  · 只有「命中位置局部」规则（序数词、引号包裹的禁令清单、否定表态）才能放行 BLOCK

用法（CLI）：
  python riskcheck.py 文章.md 脚本.py            # 扫指定文件
  python riskcheck.py <目录>                     # 扫目录下 .md/.py/.txt/.yaml/.json/.html
  python riskcheck.py --text "标题文字"          # 直接扫一段文本
  cat 正文.txt | python riskcheck.py --stdin     # 扫管道输入（用于扫最终产物）
  python riskcheck.py <目录> --strict            # WARN 也算失败
  python riskcheck.py <目录> --json              # 机器可读输出

退出码：0 无 BLOCK / 2 有 BLOCK

自定义词表：同目录 riskcheck_extra.json（可选）
  {"block_add": {"类别名": ["词1"]}, "warn_add": {...}, "allow": ["误伤词"], "drop": ["要去掉的词"]}
  ——用户报新违规词时改这个文件即可，不用动代码。
"""
import argparse
import glob
import io
import json
import pathlib
import re
import sys
import tokenize

BASE = pathlib.Path(__file__).resolve().parent

# ---------------------------------------------------------------- 规则数据

# BLOCK：会阻断发布的类别
BLOCK_WORDS = {
    "A 军事/冲突修辞": [
        "必争之地", "兵家", "制高点", "战场", "前线", "阵地", "军备", "武器",
        "开枪", "开火", "交火", "子弹", "弹药", "攻防", "攻打", "抢攻",
        "争夺", "抢占", "争夺战", "厮杀", "决战", "致命一击",
        "博弈", "加码", "卡住", "卡脖子", "封锁", "围堵", "对抗", "打压",
        "绞杀", "围剿", "突围", "血洗",
    ],
    "B 涉政/地缘": [
        # 地缘/政策敏感词
        "关税", "稀土", "出口管制", "出口许可", "实体清单", "制裁", "反制",
        "脱钩", "贸易战", "贸易休战", "休战", "会晤", "峰会", "地缘政治",
        "国家安全审查", "出口禁令", "进口申请", "两国", "双边", "中美",
        "中日", "中欧", "中俄", "中韩", "中方", "美方", "欧美",
        # 政要人名（历史高危）
        "特朗普", "拜登", "习近平", "普京", "泽连斯基", "哈里斯", "万斯",
        # 政治中心/机构（首都级，风险高于普通城市）
        "白宫", "华盛顿", "克里姆林宫", "唐宁街", "青瓦台", "国会山",
        "国务院", "外交部", "商务部", "财政部", "国会", "参议院",
        "众议院", "北约", "欧盟委员会",
        # 国名
        "美国", "中国", "日本", "韩国", "德国", "法国", "英国", "俄罗斯",
        "印度", "欧盟", "越南", "墨西哥",
        # 城市名
        "北京", "上海", "深圳", "纽约", "莫斯科", "东京", "首尔", "伦敦",
        "巴黎", "柏林", "新德里",
        # 央行/货币机构名（2026-09-18 用户拍板走严格标准：机构名一律 BLOCK）
        # 合规改法=泛称「海外主要央行」「货币当局」「货币政策会议」
        "美联储", "人民银行", "欧洲央行", "日本央行", "央行", "议息",
    ],
}

# BLOCK：组合模式（硬编码清单兜不住的高危写法，靠模式抓）
BLOCK_PATTERNS = {
    "B 涉政·职位名": r"(总统|主席|总理|首相|部长|外长|财长|国务卿|议长|防长|领导人|政要|官员)",
    "B 涉政·行程描述": r"(访问|会晤|会谈|出访|抵达|会见|通话|发表讲话|达成共识|签署协议|国事访问)",
    "B 涉政·政策动作": r"(管制与反制|出口管制|加征|征收关税|贸易谈判|谈判桌)",
}

# WARN：需人工判断，不阻断
WARN_WORDS = {
    "C 极限词/绝对化": [
        "最佳", "最好", "最强", "最优", "顶级", "极致", "唯一", "绝对",
        "必然", "百分百", "100%", "稳赚", "稳赢", "保本", "无风险", "零风险",
        "翻倍", "暴富", "躺赚", "包赚", "第一", "全国第一", "行业第一",
    ],
    "D 荐股/交易建议": [
        "买入", "卖出", "加仓", "减仓", "建仓", "清仓", "抄底", "追高",
        "目标价", "该买", "该卖", "值得买", "推荐买", "牛股", "黑马",
        "标的", "股票池", "选股公式", "仓位", "持仓", "止盈", "止损",
    ],
    "E 涨跌预测": [
        "必涨", "必跌", "会上涨", "将下跌", "一定涨", "一定跌", "预测涨",
        "预判涨", "明天涨", "看多", "看空", "牛市", "熊市",
    ],
    "F 导流/违规营销": [
        "加微信", "微信号", "微信群", "私聊", "私信我", "知识星球", "星球",
        "课程", "训练营", "付费", "会员", "内参", "领取资料", "扫码进群",
        "高手", "跟单", "带单", "分成",
    ],
    "G 其他红线": [
        "内幕", "庄家", "坐庄", "老鼠仓", "操纵", "主力动向揭秘", "赌",
        "保收益", "代客理财", "保证收益",
    ],
}

# --- 命中位置局部规则（唯一可以放行 BLOCK 的规则）---
QUOTE_L = "「『\"'“”"
QUOTE_R = "」』\"'“”"
BAN_DECL = r"(禁令|不要出现|禁止出现|不得出现|避免出现|勿用|禁用|不要写|不能用|不得使用|不要用)"
STANCE_DENY = r"(不是|并非|不代表|不等于|不构成|谈不上|拒绝|不会)"

# --- 行级规则（只对 WARN 生效，永不遮蔽 BLOCK）---
WARN_LINE_SAFE = [
    (r"(不构成.{0,8}建议|仅供参考|风险自担|自负盈亏|不推荐|不构成投资|不回答.{0,6}(买卖|价位|仓位)|只负责|不做.{0,4}建议)",
     "免责/风控语境"),
    (r"(净买入|净卖出|净流入|净流出|净额|主动买入|成交额|成交量|买入额|卖出额|换手率)",
     "资金流统计用语"),
    (r"(style=|width|height|flex|opacity|zoom|scale|font-size|line-height)",
     "代码/样式属性"),
]

REPLACE_HINT = {
    "必争之地": "绕不开的方向", "兵家": "绕不开的（统称）", "制高点": "最集中的环节",
    "战场": "主线", "前线": "主线", "开枪": "动手", "开火": "动手",
    "争夺": "聚焦", "抢占": "提前布局", "博弈": "分歧/反复", "加码": "投入",
    "卡住": "受制/瓶颈", "卡脖子": "瓶颈环节", "封锁": "限制", "围堵": "限制",
    "对抗": "分化", "打压": "承压", "武器": "工具", "军备": "投入竞赛",
    "中国": "国内/境内", "美国": "海外/全球", "中美": "全球主要经济体",
    # 央行/货币机构：机构名一律不点，改泛称
    "美联储": "海外主要央行 / 货币当局", "人民银行": "货币当局",
    "欧洲央行": "海外主要央行", "日本央行": "海外主要央行",
    "央行": "货币当局（泛称可用「海外主要央行」）", "议息": "货币政策会议",
    "白宫": "（删掉，改产业视角表述）", "国务院": "（删掉，改产业视角表述）",
    "商务部": "产业主管部门", "财政部": "财政主管部门",
}

POLITICAL_HINT = (
    "整体降到产业视角：把「某国/某人 + 动作」改写成"
    "「全球主要经济体都把 X 写进产业名单」+ 产业端连锁反应"
    "（产能排期、供应链选择、厂商排名）——保住原意，零涉政风险。"
)

TEXT_EXT = {".md", ".txt", ".py", ".yaml", ".yml", ".json", ".html"}

# 默认跳过的「记录/元文件」：CHANGELOG 要如实记录违规原文（改了就毁掉审计线索）、
# README 是说明、日志是过程产物 —— 都不是发布内容。要扫它们加 --include-meta。
META_NAME_HINTS = ("CHANGELOG", "README", "audit_images.json", "ocr_report",
                   "audit_images_log", "_log.txt", "gen_log", "ocr_log")

# 序数词量词表（「第一层」「第一个交易日」里的「第一」不是极限词）
ORDINAL_TAIL = (r"(层|天|次|步|个|款|页|条|周|月|期|盘|轮|阶段|时间|季度|交易日|"
                r"部分|种|类|批|档|位|名|只|项|点|张|句|遍|根|波|棒|回)")


def load_extra():
    """读取同目录 riskcheck_extra.json（用户可自行加词/放行，不用改代码）"""
    p = BASE / "riskcheck_extra.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ riskcheck_extra.json 解析失败（已忽略）：{e}", file=sys.stderr)
        return {}


def build_rules():
    """合并内置词表与用户自定义词表"""
    block = {k: list(v) for k, v in BLOCK_WORDS.items()}
    warn = {k: list(v) for k, v in WARN_WORDS.items()}
    allow, drop = set(), set()
    ex = load_extra()
    for k, v in (ex.get("block_add") or {}).items():
        block.setdefault(k, []).extend(v)
    for k, v in (ex.get("warn_add") or {}).items():
        warn.setdefault(k, []).extend(v)
    allow |= set(ex.get("allow") or [])
    drop |= set(ex.get("drop") or [])
    if drop:
        block = {k: [w for w in v if w not in drop] for k, v in block.items()}
        warn = {k: [w for w in v if w not in drop] for k, v in warn.items()}
    return block, warn, allow


class Hit:
    __slots__ = ("cat", "level", "word", "line_no", "context", "source", "safe", "safe_reason")

    def __init__(self, cat, level, word, line_no, context, source, safe=False, safe_reason=""):
        self.cat, self.level, self.word = cat, level, word
        self.line_no, self.context, self.source = line_no, context, source
        self.safe, self.safe_reason = safe, safe_reason

    def as_dict(self):
        return {"source": self.source, "line": self.line_no, "level": self.level,
                "cat": self.cat, "word": self.word, "context": self.context,
                "safe": self.safe, "safe_reason": self.safe_reason}


def occ_safe_reason(line: str, word: str):
    """命中位置局部判定 —— 唯一能放行 BLOCK 的规则；返回原因或 "" """
    for m in re.finditer(re.escape(word), line):
        i, j = m.start(), m.end()
        before, after = line[max(0, i - 18):i], line[j:j + 18]

        # ① 序数词：「第一层」「第一个交易日」的「第一」不是极限词
        if word == "第一" and re.match(ORDINAL_TAIL, after):
            return "序数词（非极限词）"
        if word in ("全国第一", "行业第一") and re.match(ORDINAL_TAIL, after):
            return "序数词（非极限词）"

        # ② 禁令声明行（提示词里的「不要出现军事、对抗类词汇，包括但不限于"必争之地"」）
        #    这类行是元描述、不是内容。判定从严：必须有引号包裹 或 有「包括但不限于」列举结构，
        #    避免被「不要出现X，但这是制高点」这种混写绕过。
        if re.search(BAN_DECL, line):
            quoted = (before and before[-1] in QUOTE_L) or (after and after[0] in QUOTE_R)
            if quoted or "包括但不限于" in line:
                return "禁令声明行（禁用词清单本身，非内容）"

        # ③ 否定表态：「不是从看空变成看多」——否认预测，属合规写法
        if re.search(r"(不是|并非|不代表|不等于|不构成|谈不上|拒绝)[^，。；：！？]{0,14}$", before):
            return "否定表态（否认预测，非看多看空）"

        # ④ 资金流统计：净买入/净卖出 贴在词前的「净/成交/主动」
        if word in ("买入", "卖出") and re.search(r"(净|成交|主动|被动|买入|卖出)$", before):
            return "资金流统计用语"

        # ⑤ 央行泛称：不点名具体机构（海外主要央行/全球央行/各国央行）—— 这是合规改法本身，
        #    不能拦，否则「美联储→泛称」这条路被堵死，闸门变成死结
        if word in ("央行", "议息") and re.search(
                r"(海外|全球|主要|各国|多国|境外|发达|新兴|多国)$", before):
            return "央行泛称（未点名具体机构，属合规改法）"

        # ⑥ 稀土作为板块/商品名（「稀土板块」「稀土永磁」「稀土-2.60%」）——
        #    这是普通 A股 板块用语/行情数据，与地缘语境的「稀土出口/管制」不是一回事
        if word == "稀土" and re.match(
                r"(永磁|板块|指数|价格|行业|概念|ETF|产业|股|矿|[+\-－—]?\s*[\d.]+%?)", after):
            return "板块/商品名或行情数据（非地缘出口管制语境）"
    return ""


def warn_line_safe_reason(line: str):
    """行级判定 —— 只用于 WARN，永不遮蔽 BLOCK"""
    for pat, why in WARN_LINE_SAFE:
        if re.search(pat, line):
            return why
    return ""


def scan_text(text: str, source: str = "<text>") -> list:
    """扫描一段文本，返回 Hit 列表（含被放行的，标记 safe=True）"""
    block, warn, allow = build_rules()
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        line_safe = warn_line_safe_reason(line)
        ctx = line.strip()[:120]
        for level, cats in (("BLOCK", block), ("WARN", warn)):
            for cat, words in cats.items():
                for w in words:
                    if w not in line:
                        continue
                    if w in allow:
                        hits.append(Hit(cat, level, w, i, ctx, source, True, "用户自定义放行"))
                        continue
                    why = occ_safe_reason(line, w)
                    if not why and level == "WARN":
                        why = line_safe
                    hits.append(Hit(cat, level, w, i, ctx, source, bool(why), why))
        for cat, pat in BLOCK_PATTERNS.items():
            for m in re.finditer(pat, line):
                w = m.group(0)
                why = occ_safe_reason(line, w) or ""
                hits.append(Hit(cat, "BLOCK", w, i, ctx, source, bool(why), why))
    return hits


def _strip_py_noise(text: str) -> str:
    """去掉 .py 的注释与模块 docstring。

    理由：注释/docstring 是写给人看的，不是发布内容——`audit_images.py` 的
    docstring 里就写着「必争之地」（在讲历史违规），扫它等于扫自己。
    但**字符串字面量必须保留**：upload_article.py 的正文就在 f-string 里。

    实现要点：按原始 (行,列) 位置把注释/docstring **挖成空格**，而不是重建源码——
    重建会让行号错位，而行号是用户定位违规的唯一线索，必须和源文件完全一致。
    """
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except Exception:
        return text

    lines = text.split("\n")
    spans, seen_code = [], False
    for t in toks:
        if t.type == tokenize.COMMENT:
            spans.append((t.start, t.end))
            continue                    # 注释不算「有效语句」，否则首行的 coding 注释
                                        # 会把 seen_code 提前置真、害 docstring 漏剥
        if t.type == tokenize.STRING and not seen_code:
            spans.append((t.start, t.end))          # 模块 docstring
            seen_code = True
            continue
        if t.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                          tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER):
            seen_code = True

    for (srow, scol), (erow, ecol) in spans:
        for r in range(srow, min(erow, len(lines)) + 1):
            ln = lines[r - 1]
            a = scol if r == srow else 0
            b = ecol if r == erow else len(ln)
            lines[r - 1] = ln[:a] + " " * max(0, b - a) + ln[b:]
    return "\n".join(lines)


def read_for_scan(path: pathlib.Path):
    """读取待扫文本；.py 去掉注释与 docstring"""
    for enc in ("utf-8", "gbk"):
        try:
            t = path.read_text(encoding=enc)
            return _strip_py_noise(t) if path.suffix == ".py" else t
        except UnicodeDecodeError:
            continue
        except Exception:
            return None
    return None


def scan_file(path: pathlib.Path) -> list:
    text = read_for_scan(path)
    if text is None:
        return []
    return scan_text(text, path.name)


def is_meta(p: pathlib.Path) -> bool:
    return any(h in p.name for h in META_NAME_HINTS)


def scan_paths(paths, exts=None, include_meta=False) -> list:
    """接受文件/目录/glob，返回全部命中。路径不存在只告警跳过，不崩。"""
    exts = exts or TEXT_EXT
    files, missing, skipped = [], [], 0
    for p in paths:
        pp = pathlib.Path(p)
        if pp.is_dir():
            cand = [f for f in sorted(pp.rglob("*")) if f.is_file() and f.suffix in exts]
            if not include_meta:
                keep = [f for f in cand if not is_meta(f)]
                skipped += len(cand) - len(keep)
                cand = keep
            files += cand
        elif pp.is_file():
            if is_meta(pp) and not include_meta:
                skipped += 1
            else:
                files.append(pp)
        elif any(c in str(p) for c in "*?["):
            files += [pathlib.Path(f) for f in sorted(glob.glob(str(p), recursive=True))
                      if pathlib.Path(f).is_file()]
        else:
            missing.append(str(p))
    if missing:
        print(f"⚠️ 路径不存在，已跳过：{', '.join(missing)}", file=sys.stderr)
    if skipped:
        print(f"（已跳过 {skipped} 个记录/元文件：CHANGELOG/README/日志 —— 它们要如实留存"
              f"违规原文，扫它们等于扫自己；要扫加 --include-meta）", file=sys.stderr)
    hits = []
    for f in files:
        hits += scan_file(f)
    return hits


def report(hits, stream=sys.stdout, strict=False, verbose_safe=False):
    """打印分级报告；返回 (block 数, warn 数)（已剔除误伤）"""
    real = [h for h in hits if not h.safe]
    block = [h for h in real if h.level == "BLOCK"]
    warn = [h for h in real if h.level == "WARN"]
    safe = [h for h in hits if h.safe]

    w = stream.write
    if not real:
        w("\n✅ 合规扫描通过：未发现禁用词\n")
    else:
        if block:
            w(f"\n{'='*74}\n⛔ BLOCK · 必须修改（{len(block)} 处）——会阻断发布\n{'='*74}\n")
            by_src = {}
            for h in block:
                by_src.setdefault((h.source, h.cat), []).append(h)
            for (src, cat), hs in by_src.items():
                w(f"\n  【{cat}】{src}\n")
                seen = set()
                for h in hs:
                    if (h.word, h.line_no) in seen:
                        continue
                    seen.add((h.word, h.line_no))
                    hint = REPLACE_HINT.get(h.word, "")
                    tip = f"  → 建议改：{hint}" if hint else ""
                    w(f"    L{h.line_no:<4} 「{h.word}」{tip}\n           {h.context}\n")
            if any(h.cat.startswith("B") for h in block):
                w(f"\n  💡 {POLITICAL_HINT}\n")
            w("  💡 若判定为误伤（正常用语被扫到）：把该词加进 "
              "_wx_read/riskcheck_extra.json 的 allow，不用改代码\n")
        if warn:
            w(f"\n{'-'*74}\n⚠️  WARN · 需人工判断（{len(warn)} 处）——不阻断，多为误伤\n{'-'*74}\n")
            by_src = {}
            for h in warn:
                by_src.setdefault((h.source, h.cat), []).append(h)
            for (src, cat), hs in by_src.items():
                w(f"\n  【{cat}】{src}\n")
                words = {}
                for h in hs:
                    words.setdefault(h.word, []).append(h.line_no)
                for word, lns in words.items():
                    lns_s = ", ".join(f"L{n}" for n in sorted(set(lns))[:8])
                    w(f"    「{word}」×{len(set(lns))}  {lns_s}\n")

    if safe:
        if verbose_safe:
            w(f"\n（{len(safe)} 处命中已按误伤规则放行，明细：）\n")
            for h in sorted(safe, key=lambda x: (x.source, x.line_no)):
                w(f"    {h.source}:L{h.line_no} 「{h.word}」 ← {h.safe_reason}\n")
        else:
            w(f"\n（{len(safe)} 处命中已按误伤规则放行，--verbose 看明细）\n")

    failed = bool(block) or (strict and bool(warn))
    w(f"\n{'='*74}\n")
    if failed:
        extra = f" + WARN {len(warn)} 处（--strict）" if strict and warn else ""
        w(f"❌ 未通过：BLOCK {len(block)} 处{extra}\n")
    else:
        tail = f"（WARN {len(warn)} 处待人工判断）" if warn else ""
        w(f"✅ 通过：无 BLOCK{tail}\n")
    w(f"{'='*74}\n")
    return len(block), len(warn)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="合规风险检测（BLOCK 阻断 / WARN 人工判断）")
    ap.add_argument("paths", nargs="*", help="文件/目录/glob")
    ap.add_argument("--text", default="", help="直接扫一段文本")
    ap.add_argument("--stdin", action="store_true", help="扫标准输入（用于扫最终产物）")
    ap.add_argument("--ext", default="", help="限定扩展名，如 .md,.py")
    ap.add_argument("--strict", action="store_true", help="WARN 也算失败")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--verbose", action="store_true", help="显示被放行的误伤明细")
    ap.add_argument("--include-meta", action="store_true",
                    help="也扫 CHANGELOG/README/日志等记录文件（默认跳过）")
    args = ap.parse_args()

    if not (args.text or args.stdin or args.paths):
        ap.error("需要 paths / --text / --stdin 之一")

    hits = []
    if args.text:
        hits += scan_text(args.text, "<--text>")
    if args.stdin:
        hits += scan_text(sys.stdin.read(), "<stdin>")
    if args.paths:
        exts = {e.strip() for e in args.ext.split(",")} if args.ext else None
        hits += scan_paths(args.paths, exts, include_meta=args.include_meta)

    if args.json:
        real = [h.as_dict() for h in hits if not h.safe]
        print(json.dumps({"block": [h for h in real if h["level"] == "BLOCK"],
                          "warn": [h for h in real if h["level"] == "WARN"]},
                         ensure_ascii=False, indent=1))
        return 2 if any(h["level"] == "BLOCK" for h in real) else 0

    nb, nw = report(hits, strict=args.strict, verbose_safe=args.verbose)
    return 2 if (nb or (args.strict and nw)) else 0


if __name__ == "__main__":
    sys.exit(main())
