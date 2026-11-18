# assets 资产索引（专家团自包含资产）

> 本目录是本专家包的**实物资产层**。原则：能跑的东西物理放在包里，不靠外部绝对路径。
> 路径权威表见 `../config/paths.md`。所有命令模板统一用 `${EXPERT_DIR}` 解析。

## 目录速查

| 目录 | 是什么 | 能直接跑吗 |
|---|---|---|
| **`tools/`** | **★ 工具库：`gzh.py` 统一 CLI + `market_verify.py`** | **能，首选入口** |
| `publish/` | 发布与风控**库**（被 `gzh.py` 调用） | 当库用，不当脚本跑 |
| `writer-app/` | Streamlit 写作工作台（选题→大纲→正文→质检） | 需依赖，代码可读写 |
| `typeset/` | 归藏排版器（本地可视化粘贴） | 能，双击启动 |
| `scripts/gemini-gen.mjs` | Gemini 零积分出图 | 能，看 `references/gemini-image.md` |
| `scripts/legacy/` | 11 个历史一次性脚本 | **不能**，只参考 |
| `docs/` `ip/` `palette/` `workflow/` `templates/` | 策略 / 人设 / 配色 / 方法原文 / 模板 | 读取参考 |

---

## 1. `publish/` — 发布与风控引擎（S6 / S5 的底层库）

来源：`F:/桌面/zcode工作区/_wx_read/`（原位置保留）

| 文件 | 作用 | 谁用 |
|---|---|---|
| `news_publish.py` | **核心发布库**（264 行）：`load_creds()` 读 `~/.baoyu-skills/.env` → `get_token()` → `upload_img()` 传封面 → `to_html()` 拼内联样式 → `add_news_draft()` 落草稿箱 → `publish()`；另含 `cover_A/B/C` 三款封面生成、`pick_style()` 轮换、`record_style()` 记台账 | 被 `gzh.py publish` 复用 |
| `riskcheck.py` | **风控检查器**（23KB）：违禁词、绝对化用语、数据口径、合规红线扫描 | 被 `gzh.py risk` 调用 |
| `riskcheck_extra.json` | 风控补充词表 | S5 |
| `run_daily.py` | 日更主流程编排 | S6 / 团长 |
| `generate.py` | 内容生成（多模型：deepseek / qwen / hunyuan / kimi）。**密钥已脱敏**：从 `~/.baoyu-skills/.env` 或环境变量读 `DEEPSEEK_API_KEY` / `QWEN_API_KEY` / `HUNYUAN_API_KEY` / `MOONSHOT_API_KEY`，取不到自动跳过该 provider | 团长 |
| `cover_variants.py` | 封面多版变体 | S3 视觉 |
| `delete_drafts.py` | 草稿清理 | S6 |
| `freepublish.py` | 发布状态查询 | S6 / S7 |
| `extract.py` / `fetch_news.py` / `fetch_us.py` | 新闻与行情抓取 | S1 选题 |
| `test_riskcheck.py` / `test_text.py` | 自测 | S5 |

**关键事实（2026-11-05 核实）**：`load_creds()` 读的是 `~/.baoyu-skills/.env`；`upload_article.py` 曾在 2026-09-22 用它真实跑过 `draft/add`。
→ **发布走 `gzh.py publish` 一条命令**，不要再去试 `wenyan` / `baoyu-post-to-wechat`。

---

## 2. `writer-app/` — 公众号写作工作台（Streamlit）

来源：`F:/桌面/zcode工作区/03_内容运营/公众号运营/wechat-writer/`

结构化写作流程：**选题 → 大纲 → 写作 → 质检**。是 S1/S2 的代码实现，比 prompt 更硬。

| 目录 | 内容 |
|---|---|
| `app.py` | Streamlit 主入口 |
| `core/` | `config.py` / `llm.py` / `memory.py`（长期记忆+短期日志）/ `thoughts.py` |
| `workflow/` | `topic.py`（选题角度）· `outline.py`（大纲）· `writing.py`（正文）· `quality.py`（质检） |
| `tools/` | **`de_ai.py`（去 AI 味 → 对应 S2）** · `formatter.py`（排版）· `image_gen.py`（生图）· `web_fetcher.py` |
| `souls/` | `default.md` / `marketing.md`（人设 soul，可作 S2 语气基准） |
| `memory/` | `long_term.md`（长期记忆）/ `rules.md`（写作规则） |
| `requirements.txt` / `start.bat` / `start.sh` | 启动 |

**已剔除**：`.env`（含 DEEPSEEK / SILICONFLOW / PEXELS 真实 key）、`archives/`（历史文章）、`memory/short_term.log`、`__pycache__`。
仅保留 `.env.example`（占位符，无真实值）。运行前需按 `.env.example` 自建 `.env`。

---

## 3. `typeset/` — 归藏排版工具

来源：`03_内容运营/公众号运营/归藏排版工具/server.py`

本地排版器：双击启动 → 浏览器打开 → 左边写 → 右边预览 → 点复制 → 公众号 Ctrl+V。
用 Win32 剪贴板 API（`ctypes.windll`），**仅 Windows 可用**。
→ S3 交付 HTML 后，可用它做「所见即所得粘贴」，比手搓 innerHTML 稳。

---

## 4. `tools/` — ★ 工具库（真能跑，首选入口）

**要执行机械动作，先来这里。** 完整用法见 `tools/README.md`。

| 文件 | 作用 |
|---|---|
| `gzh.py` | 统一 CLI：`creds` / `token` / `verify` / `render` / `check` / `risk` / `publish` |
| `market_verify.py` | A 股盘面多源核对器（`gzh.py verify` 调用，也可单独跑） |

已实测通过（2026-11-05）：`creds` ✓、`token` ✓（报 40164 IP 白名单）、`check` ✓、`render` ✓ 1880×800、`risk` ✓（含 `--json`）、`verify` ✓、`publish --dry-run` ✓。

---

## 4b. `scripts/legacy/` — 历史脚本存档（只参考，勿直接跑）

11 个来自 2026-09~10 月的实际稿件脚本，各自绑死某一篇（硬编码标题/日期/正文 HTML）。当年能跑是因为文章就在同目录。

**全部已被 `tools/` 取代**，替代关系见 `scripts/legacy/README.md` 的对照表。留在这里是因为它们记录了「当年这一步怎么做的」，改这里等于毁掉存档价值 —— 要复用就提参数放进 `tools/`。

两条从里面提炼出的经验已固化：
1. 涨跌家数 ≠ 涨跌停数，两套口径不能混（详见 `tools/README.md`）
2. `urllib` 必须清空 ProxyHandler（本机 1080 死代理）

---

## 5. `docs/` — 策略与人设文档

| 文件 | 内容 |
|---|---|
| `股票公众号系列_内容策略.md` | 账号内容策略（选题方向、栏目、节奏） |
| `视频号矩阵引流公众号_全案策划.md` | 视频号 → 公众号引流全案（S4 参考） |
| `公众号写作技能_完整版.md` | 写作 skill 说明（刘润风格结构模板） |
| `发布台账-草稿记录.md` | **历史发布台账**，S6 发布后应追加，S7 复盘取值参考 |

---

## 6. `ip/` — 长盈客栈 IP 人设资产

| 文件 | 内容 |
|---|---|
| `长盈客栈角色卡.md` | 角色卡（人设核心设定） |
| `长盈客栈人物设计探讨.md` | 人物设计推演 |
| `长盈客栈连环画设定.md` | 连环画视觉设定 |
| `长盈客栈IP全景思维导图.html` | IP 全景导图 |

→ S2 语气校准、S4 出镜人设、S3 插画风格，都应先读这里，避免每次重造人设。

---

## 7. `palette/` — 配色体系实物

| 文件 | 内容 |
|---|---|
| `工厂样图/cover.yaml` / `data.yaml` | 封面/数据图配色配置（工厂式） |
| `工厂样图/gallery.html` | 样图 gallery（可视化对照） |
| `文章配色/gallery.html` | 文章配色 gallery |
| `image-prompts.md` | 配图 prompt 库 |

→ `references/themes.md` 的 16 套主题是**文字版**，这里是**实物版**。S3 挑主题时应两边对照。

---

## 8. `workflow/` — 用户自建工作流原文

| 文件 | 内容 |
|---|---|
| `公众号文章创作工作流-原文.md` | 用户自建的完整工作流（2026-09-24 版），专家团方法层即由此提炼 |
| `README.md` | 该文件的归档说明 |

---

## 9. `scripts/gemini-gen.mjs`

零积分 Gemini 出图脚本（单文件，仅依赖 node 内置模块）。
详见 `../skills/gzh-workflow/references/gemini-image.md`。

---

## 没进包的东西（明确边界）

| 排除项 | 原因 |
|---|---|
| `wechat-writer/.env` | 含真实 API key |
| `wechat-writer/archives/` | 历史文章，非能力 |
| `_wx_read/wx1.html` `wx2.html`（各 1.9MB） | 单日成品，非模板 |
| `articles/` 下 30+ 历史文章目录正文 | 一次性产出，共 293MB |
| 各种 png/jpg | 体积大且不可复用 |
| `__pycache__` / `*.log` | 运行时垃圾 |
| `.gemini-opera-profile` / `cookies.json` | 含登录态，进包会失效或泄漏 |

历史产出如需追溯，去 `../output/` 或原 `articles/` 目录。
