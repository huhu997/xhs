# -*- coding: utf-8 -*-
"""
D2B「一图看懂 · 跨 AI 共享个人档案」5 图设计源生成器。
基于 verified 的 guizang-card-render 瑞士风模板（本地 HTML→Playwright，零 key、离线）。
从原模板读取 → 换 accent / 去 CDN / 注入局部 CSS → 替换占位 poster 为 5 张真实卡 → 输出 index.html。
可反复运行，不依赖手工改动。
"""
import os

TPL = r"C:/Users/admin/.workbuddy/skills/guizang-card-render/assets/template-swiss-card.html"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "index.html")

EXTRA_CSS = r"""
    /* ---- D2B local additions (Swiss rules kept: square corners, no shadow, no gradient) ---- */
    .poster.xhs .p-title {
      font-family: var(--sans-zh); font-weight: 300; font-size: 76px;
      line-height: 1.16; letter-spacing: -.01em; margin: 0; color: var(--ink);
    }
    .poster.xhs .p-title.sm { font-size: 60px; }
    .p-sub {
      font-family: var(--sans-zh); font-weight: 400; font-size: 26px;
      line-height: 1.6; color: var(--grey-3); margin: 0;
    }
    .p-note {
      font-family: var(--sans-zh); font-weight: 400; font-size: 24px;
      line-height: 1.65; color: var(--grey-3); margin: 0;
    }
    .blist { display: flex; flex-direction: column; }
    .brow {
      display: grid; grid-template-columns: 104px 1fr; gap: 24px;
      align-items: center; padding: 26px 0; border-bottom: 1px solid var(--grey-2);
    }
    .brow:first-child { border-top: 1px solid var(--grey-2); }
    .brow .nb { font-family: var(--mono); font-size: 30px; color: var(--accent); margin: 0; }
    .brow .tx { font-family: var(--sans-zh); font-size: 32px; line-height: 1.4; margin: 0; }
    .brow .tx small {
      display: block; font-size: 22px; color: var(--grey-3); margin-top: 8px; font-weight: 400;
    }
    .code {
      font-family: var(--sans-zh); font-size: 23px; line-height: 1.72;
      background: var(--grey-1); padding: 32px 36px; margin: 0;
      white-space: pre-wrap; border-left: 3px solid var(--accent);
    }
    .chips { display: flex; flex-wrap: wrap; gap: 16px; }
    .chip {
      border: 1px solid var(--grey-2); padding: 12px 22px;
      font-family: var(--sans-zh); font-size: 22px; color: var(--ink);
    }
    .hl { color: var(--accent); }
    .cta { font-family: var(--sans-zh); font-weight: 500; font-size: 92px; line-height: 1.1; margin: 0; }
    .poster.xhs .matrix-fill .matrix-cell .cell-title { font-size: 26px; }
    .poster.xhs .matrix-fill .matrix-cell .cell-sub {
      font-family: var(--sans-zh); font-size: 20px; line-height: 1.45; color: var(--grey-3);
    }
    .poster.xhs .matrix-fill .matrix-cell.is-accent .cell-sub { color: var(--accent-on); opacity: .85; }
"""

POSTERS = r"""    <!-- ============ card1 封面 · S01 Accent Cover ============ -->
    <section class="poster xhs" id="card1">
      <div class="content stack gap-9">
        <div class="chrome-min">
          <span>Vol. 02 · 薄肌小王</span>
          <span>一图看懂</span>
        </div>
        <div class="stack gap-7">
          <p class="t-cat">个人档案 · Profile</p>
          <h1 class="h-statement">换 AI<br>不用重新<br><span class="hl">交代自己</span></h1>
        </div>
        <div class="grow"></div>
        <hr class="hr-accent">
        <p class="lead">把反复要讲的话，整理成一份能复制的 4 栏档案。</p>
        <div class="row gap-6">
          <p class="t-meta">04 栏 · 纯文字</p>
          <p class="t-meta">/ 开新对话贴一次</p>
        </div>
      </div>
    </section>

    <!-- ============ card2 场景 · 重复交代的三句话 ============ -->
    <section class="poster xhs" id="card2">
      <div class="content stack gap-8">
        <div class="chrome-min">
          <span>01 / 场景</span>
          <span>Problem</span>
        </div>
        <p class="t-cat">每次换个 AI，都要重讲</p>
        <h2 class="p-title">重复交代的<br>三句话</h2>
        <div class="blist">
          <div class="brow">
            <p class="nb">01</p>
            <p class="tx">「我是谁、在做什么」<small>身份、在忙的事、怎么称呼</small></p>
          </div>
          <div class="brow">
            <p class="nb">02</p>
            <p class="tx">「这次要什么」<small>产出长什么样、给谁看、多长</small></p>
          </div>
          <div class="brow">
            <p class="nb">03</p>
            <p class="tx">「别用套话」<small>要不要分点、口吻、别替我补内容</small></p>
          </div>
        </div>
        <div class="grow"></div>
        <hr class="hr-accent">
        <p class="p-note">写作、画图、整理资料，各讲一遍；来回重复，挺费劲。</p>
      </div>
    </section>

    <!-- ============ card3 结构 · 4 栏矩阵 ============ -->
    <section class="poster xhs" id="card3">
      <div class="content stack gap-8">
        <div class="chrome-min">
          <span>02 / 结构</span>
          <span>Structure</span>
        </div>
        <p class="t-cat">一份档案，就这 4 栏</p>
        <h2 class="p-title sm">只写「稳定不变」的</h2>
        <div class="matrix-fill">
          <div class="matrix-cell">
            <p class="cell-nb">01 / WHO</p>
            <p class="cell-title">我是谁</p>
            <p class="cell-sub">怎么称呼、在做什么、别假装懂我</p>
          </div>
          <div class="matrix-cell">
            <p class="cell-nb">02 / WHAT</p>
            <p class="cell-title">我要什么</p>
            <p class="cell-sub">产出形态、给谁看、篇幅上限</p>
          </div>
          <div class="matrix-cell">
            <p class="cell-nb">03 / HOW</p>
            <p class="cell-title">怎么说话</p>
            <p class="cell-sub">分点、口吻、不套话、不确定就标出来</p>
          </div>
          <div class="matrix-cell is-accent">
            <p class="cell-nb">04 / SOURCE</p>
            <p class="cell-title">资料在哪</p>
            <p class="cell-sub">贴进来的算依据、不能改写、缺的标出来</p>
          </div>
        </div>
        <div class="grow"></div>
        <hr class="hr-accent">
        <p class="p-note">会变的（这次要写什么、贴了哪份材料）留在对话里说，别写进档案。</p>
      </div>
    </section>

    <!-- ============ card4 示例 · 可复制文本 ============ -->
    <section class="poster xhs" id="card4">
      <div class="content stack gap-7">
        <div class="chrome-min">
          <span>03 / 示例</span>
          <span>Copy &amp; Paste</span>
        </div>
        <p class="t-cat">可以直接复制的一段</p>
        <h2 class="p-title sm">长这样</h2>
        <pre class="code">【我是谁】
称呼我小王；在做内容整理与选题研究；
不用替我补全没给的信息。

【我要什么】
产出：要点清单；给普通读者看；不超过 8 条。

【怎么说话】
分点、口语、不用套话；
不确定的地方标「待确认」。

【资料在哪】
下面贴的材料只作依据，不要改写原意；
缺的标出来，不要补。</pre>
        <div class="grow"></div>
        <hr class="hr-accent">
        <p class="p-note">开新对话时整段贴进去，再补这次的具体任务。</p>
      </div>
    </section>

    <!-- ============ card5 钩子 · 扣【档案】 ============ -->
    <section class="poster xhs" id="card5">
      <div class="content stack gap-8">
        <div class="chrome-min">
          <span>04 / 领取</span>
          <span>Takeaway</span>
        </div>
        <p class="t-cat">完整版整理好了</p>
        <h2 class="p-title sm">4 栏字段模板<br>＋ 一段可复制示例</h2>
        <div class="chips">
          <span class="chip">纯文字</span>
          <span class="chip">不用装东西</span>
          <span class="chip">纯分享不卖课</span>
        </div>
        <div class="grow"></div>
        <hr class="hr-accent">
        <p class="cta hl">扣【档案】</p>
        <p class="lead">评论区扣【档案】，我看到了发你。</p>
        <p class="p-note">你每次换 AI 最烦重新交代哪一句？评论区说说，我看看要不要补进模板。</p>
      </div>
    </section>
"""


def main():
    with open(TPL, encoding="utf-8") as f:
        s = f.read()

    s = s.replace('<html lang="zh-CN" data-accent="ikb">',
                  '<html lang="zh-CN" data-accent="safety-orange">')
    s = s.replace("[必填] 替换为社交卡组标题 · Social Card Set",
                  "薄肌小王 D2B · 一图看懂跨 AI 共享个人档案")

    # 离线渲染：移除外部 CDN 引用（render.cjs 本身也会 abort，这里从源头去掉更干净）
    drop = ("fonts.googleapis.com", "fonts.gstatic.com", "unpkg.com/lucide", "preconnect")
    s = "\n".join(line for line in s.split("\n")
                  if not any(k in line for k in drop))

    s = s.replace("  </style>", EXTRA_CSS + "\n  </style>")

    start = s.index('    <section class="poster xhs" id="xhs-01">')
    end = s.index("    </section>", start) + len("    </section>")
    s = s[:start] + POSTERS.rstrip() + s[end:]

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(s)

    print("written:", OUT)
    print("posters:", s.count('class="poster xhs"'), "| accent safety-orange:",
          'data-accent="safety-orange"' in s)


if __name__ == "__main__":
    main()
