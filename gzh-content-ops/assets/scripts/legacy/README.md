# legacy/ — 历史一次性脚本（只作参考，不要直接跑）

这里的 11 个脚本来自 2026-09 ~ 10 月的实际稿件目录，**它们各自绑死某一篇稿**（硬编码标题、日期、正文 HTML、配色常量），当年能跑是因为文章就在同一个目录里。

**为什么留在这里**：它们是这套工作流真实跑通过的证据，遇到「当年这一步怎么做的」可以查。
**为什么不能直接跑**：日期/标题/正文都写死在代码里，脱离原目录就报错；部分脚本 `sys.path` 指向已不存在的 `_wx_read`。

## 替代关系（新工具 → 见 `assets/tools/`）

| 历史脚本 | 当年干什么 | 现在用什么 |
|---|---|---|
| `build_preview.py` (24KB) | 把某篇文章排成公众号预览 HTML | 不再需要脚本：S3 直接产出 HTML（`08-article-paste.html`），或 `baoyu-markdown-to-html` |
| `render_images.py` (21KB) | 9/17 那篇的 10 张图 HTML 直出 | 同上，S3 按 themes.md 现场写 HTML |
| `make_previews.py` | 生成配图一览 + 手机预览 | — |
| `add_caption.py` | 给候选封面上加配文 | — |
| `check_cover.py` | 检查封面尺寸/亮度 | **`gzh.py check <img> --ratio 2.35`** |
| `upload_article.py` (23KB) | 9/22 那篇推草稿箱 | **`gzh.py publish`** |
| `upload_preview.py` | 通用投递（dir + title + digest） | **`gzh.py publish --html --title --cover`** |
| `postcheck.py` | 推完查询草稿状态 | `gzh.py publish` 已回 media_id |
| `audit_risk.py` | 包装 riskcheck 扫目录 | **`gzh.py risk <path>`** |
| `gen_images.py` | 即梦 Seedream 网页自动化出图 | **`gemini-gen.mjs`**（见 `skills/gzh-workflow/references/gemini-image.md`）；即梦 skill 已不存在 |
| `verify_data.py` (209 行) | 9/28 盘面数据多源核对 | **`gzh.py verify --date YYYYMMDD`**（已参数化，口径一字未改） |

## 两条仍值得记住的经验（已固化进新工具）

1. **涨跌家数 ≠ 涨跌停数，两套口径不能混用**（2026-11-05 实测）
   - 逐股扫描（东财 clist，全市场 f3）：4869 涨 / 624 跌 / 按阈值算出的涨跌停会偏
   - 东财涨跌停池 tc：涨停 84 / 跌停 0
   - 同一天两套口径能差 1~3 只。**稿子里只用一套，并且写明是哪套**。
2. **`urllib` 必须清空 ProxyHandler**：本机 `HTTP_PROXY` 指向 `127.0.0.1:1080`（拨号型，常没起），不清就 502。新工具已内置。

## 想复用哪个

读它、把里面的常量提成参数、放进 `assets/tools/`，不要原地改这里 —— 这里是存档，改了就失去「当时怎么做的」这个价值。
