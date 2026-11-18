# -*- coding: utf-8 -*-
"""riskcheck.py 回归测试 —— 固化 2026-09-18 v1 违规 / v2 过审 两套样本

跑法：python test_riskcheck.py
全过退出码 0，有失败退出码 1。
改词表/改规则后必须跑这个，防止「把真违规放行」或「误报回潮」。
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from riskcheck import scan_text  # noqa: E402

# ---------------------------------------------------------------- 样本

# v1 真实违规原文（按 CHANGELOG 记录的触发点还原）
V1 = """
标题：A股每日复盘｜分歧最大的地方才是必争之地（9.18）

## 第二层：桌上的牌 —— 9月24日，白宫
特朗普与习近平将于9月24日在白宫会晤，这是十年来第一次白宫访问。
美方将抽取中国营收25%，关税休战即将到期，稀土出口与管制与反制成为核心变量。
中方与美方在谈判桌上的博弈，决定了全球供应链的走向。

科技是产业周期、国家竞争、全球定价三重叠加的制高点。
这也是全场分歧最大的战场，谁先开枪谁就抢占先机。
资金还在持续加码，而先进产能被卡住，封锁与对抗成为常态。

收尾：不败的前提，是知道战场在哪；不需要每天开枪。
"""

# 实际触发的禁用词（v1 被判违规的真正原因）
V1_MUST_CATCH = [
    "必争之地", "制高点", "战场", "开枪", "加码", "卡住", "博弈", "封锁", "对抗",
    "特朗普", "习近平", "白宫", "会晤", "关税", "稀土", "管制与反制", "中方", "美方",
]

# v2 过审后的合规写法 + 历史误伤样本（一个都不该 BLOCK）
V2_CLEAN = """
标题：A股每日复盘｜放量2.08万亿站上3900，剥掉所有热点只剩一个方向（9.18）

第二层：政策的钱 —— 全球都在往同一个方向投。
主要经济体都把它写进产业名单，先进产能排期已到后年。
国内存储厂商进全球前四，下游整机厂在重新评估供应商结构。

第一层：产业周期。第一个交易日的资金流向说明了一切。
电子净流入 198.54 亿，半导体净卖出 50.83 亿（讲的是资金流统计）。
我的观点变了，但不是从看空变成看多，而是从"看不清"变成"看得清"。
（免责：以上不构成投资建议，仓位请自行控制，风险自担。）

收尾：不败的前提，是先看清主线在哪；不需要每天动手。

<img src="{url}" style="width:100%;display:block;" />
"""

# 曾经的漏洞样本：行级白名单差点把真违规一起放行
TRAP = "第一层：这是产业周期里真正的必争之地。"


def hits_of(text):
    return scan_text(text, "<test>")


def blocking(text):
    return sorted({h.word for h in hits_of(text) if h.level == "BLOCK" and not h.safe})


def warns(text):
    return sorted({h.word for h in hits_of(text) if h.level == "WARN" and not h.safe})


def safe_words(text):
    return sorted({h.word for h in hits_of(text) if h.safe})


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    fails = []

    def check(name, cond, detail=""):
        print(f"{'✅' if cond else '❌'} {name}" + (f"\n     {detail}" if detail and not cond else ""))
        if not cond:
            fails.append(name)

    # ---- 测试 A：v1 违规原文必须全部拦住 ----
    print("\n【A】v1 违规原文 → 必须 BLOCK")
    got = set(blocking(V1))
    missed = [w for w in V1_MUST_CATCH if w not in got]
    check(f"v1 的 {len(V1_MUST_CATCH)} 个真触发点全部命中", not missed,
          f"漏掉: {missed}")

    # ---- 测试 B：v2 合规写法 + 历史误伤 → 一个都不该 BLOCK ----
    print("\n【B】v2 合规写法 + 历史误伤样本 → 必须 0 BLOCK")
    v2_block = blocking(V2_CLEAN)
    check("v2 合规文本零 BLOCK", not v2_block, f"误报: {v2_block}")

    # 逐条验证关键误伤项确实被放行（而不是碰巧没命中）
    print("\n【B2】误伤项必须被「显式放行」而不是碰巧没扫到")
    for word, expect_reason in [
        ("第一", "序数词"),
        ("卖出", "资金流"),      # 原文是「净卖出」，词表条目是「卖出」
        ("100%", "样式/代码"),
        ("看空", "否定表态"),
    ]:
        hits = [h for h in hits_of(V2_CLEAN) if h.word == word]
        if not hits:
            check(f"「{word}」被扫描到且已放行", False, "根本没扫到这个词，测试样本失效")
            continue
        all_safe = all(h.safe for h in hits)
        reasons = {h.safe_reason for h in hits}
        check(f"「{word}」已放行（{list(reasons)[0] if reasons else '-'}）", all_safe,
              f"未放行，原因: {reasons}")

    # ---- 测试 C：fail-closed 铁律——行级白名单不得遮蔽 BLOCK ----
    print("\n【C】fail-closed 铁律：同一行有误伤词时，真违规仍须 BLOCK")
    trap_block = blocking(TRAP)
    check("「第一层：这是必争之地」仍拦得住", "必争之地" in trap_block,
          f"被放行了！违规词漏网: {trap_block}")

    # ---- 测试 D：否定表态不能变成万能免死金牌 ----
    print("\n【D】否定表态规则不得被滥用")
    d_block = blocking("这不是看空，而是必争之地。")
    check("同句里的真违规不受否定表态影响", "必争之地" in d_block, f"结果: {d_block}")

    # ---- 测试 E：提示词里的「禁用词清单」应放行 ----
    print("\n【E】提示词里的禁令清单 → 应放行（不扫自己）")
    prompt = '措辞禁令：画面里不要出现"必争之地""制高点""战场"；不要出现任何国家名。'
    p_block = blocking(prompt)
    check("禁令声明行零 BLOCK", not p_block, f"误报: {p_block}")

    # 列举式禁令语句（真实 gemini-prompts.md 的写法）
    prompt2 = ('措辞禁令：画面里不要出现军事、对抗、地缘政治类词汇与意象'
               '——包括但不限于"必争之地""制高点""战场""博弈""卡住"。')
    p2_block = blocking(prompt2)
    check("列举式禁令语句零 BLOCK", not p2_block, f"误报: {p2_block}")

    # 混写绕过防护：禁令词 + 真违规同句，仍须 BLOCK
    p3_block = blocking("不要出现这些词，但这是制高点。")
    check("禁令混写不得成为免死金牌", "制高点" in p3_block, f"被绕过！结果: {p3_block}")

    # ---- 测试 F：央行机构名走严格标准（2026-09-18 用户拍板「全改」）----
    print("\n【F】央行机构名 → 严格 BLOCK；泛称改法 → 放行")
    f_block = blocking("这是美联储加息落地后第一个完整的交易日，央行后续动作待观察。")
    check("美联储/央行 点具体机构名时 BLOCK", "美联储" in f_block and "央行" in f_block,
          f"未拦：{f_block}")
    generic = "海外主要央行的货币政策转向，是全场定价的起点。"
    g_block = blocking(generic)
    check("泛称「海外主要央行」不拦（合规改法本身不能被堵死）", not g_block,
          f"把合规改法也拦了，闸门成死结：{g_block}")
    g_safe = safe_words(generic)
    check("「海外主要央行」是被「显式放行」而非碰巧没扫到",
          "央行" in g_safe, f"未显式放行：{g_safe}")

    # ---- 测试 G：9/18 v2 真残留必须能拦住 ----
    print("\n【G】9/18 v2 真残留（正文写「中国厂商」）→ 必须 BLOCK")
    residual = "有头部消费电子厂商正在推进采用中国厂商的内存芯片——供应链上的选择。"
    r_block = blocking(residual)
    check("「中国厂商」拦得住", "中国" in r_block, f"未拦：{r_block}")
    fixed = "有头部消费电子厂商正在推进采用国内厂商的内存芯片——供应链上的选择。"
    check("改成「国内厂商」后放行", not blocking(fixed), f"改法仍被拦：{blocking(fixed)}")

    # ---- 测试 H：.py 注释被忽略，但行号必须与源文件一致 ----
    print("\n【H】.py 扫字符串、忽略注释，且行号必须准")
    import tempfile, os
    from riskcheck import scan_file
    src = '''# -*- coding: utf-8 -*-
"""模块 docstring 里写必争之地、制高点（是说明，不该扫）"""

# 这是注释，里面写战场、开枪（也不该扫）
CONTENT = "正文第一行，干净"
CONTENT2 = "这一行有必争之地"          # 行内注释还写制高点
TAIL = "结束"
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(src)
        tmp = f.name
    try:
        hits = [h for h in scan_file(pathlib.Path(tmp)) if not h.safe]
        words = {h.word: h.line_no for h in hits}
        check("注释与 docstring 里的词不报（战场/开枪/制高点全不报）",
              not ({"战场", "开枪", "制高点"} & set(words)),
              f"误报: {sorted(set(words) & {'战场','开枪','制高点'})}")
        check("字符串里的违规照报", "必争之地" in words, f"漏报，结果: {words}")
        check("行号与源文件一致（应为第 6 行）", words.get("必争之地") == 6,
              f"报的是 L{words.get('必争之地')}，实际在第 6 行 —— 行号错位会让用户找不到位置")
    finally:
        os.unlink(tmp)

    # ---- 测试 I：记录/元文件默认跳过 ----
    print("\n【I】CHANGELOG/README/日志默认跳过（要如实留存违规原文）")
    from riskcheck import is_meta
    for name, want in [("CHANGELOG.md", True), ("README.md", True),
                       ("upload_article.py", False), ("01-cover.yaml", False)]:
        check(f"{name} → {'跳过' if want else '扫描'}", is_meta(pathlib.Path(name)) == want)

    # ---- 汇总 ----
    print("\n" + "=" * 66)
    if fails:
        print(f"❌ {len(fails)} 项失败：")
        for f in fails:
            print(f"   - {f}")
        return 1
    print("🎉 全部通过：违规必拦、误伤必放、fail-closed 未被绕过")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
