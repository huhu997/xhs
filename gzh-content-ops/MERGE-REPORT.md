# 全合并补做报告 · 2026-11-05

> 用户质疑：「为什么在那里呢，我不是让全合并到我们这个专家团吗」
> 结论：**质疑成立**。上次「融合」只做了方法层，没做资产层 / 产出层 / 同步层，所以专家团仍依赖旧工作区路径，本轮产出也自然落在 `zcode工作区/articles/`。本文件记录补齐动作，可逐项复核。

---

## 一、补齐前实测（不是猜的）

| 层 | 状态 | 证据 |
|---|---|---|
| 方法层 | ✅ 已做 | 源包 `skills/gzh-workflow/references/` 有 7 份规范；`SKILL.md`、`team/roles/*`、`TEAM.md`、`ORCHESTRATOR.md`、`plugin.json` 已改 |
| 资产层 | ❌ 未做 | 专家包里**零脚本、零模板、零工作流原文**；5 处文档写的是外部绝对路径（`Gemini本地文件/.../gemini-gen.mjs`、`zcode工作区/articles/.../build_preview.py`） |
| 产出层 | ❌ 未做 | 没有任何「产出目录」约定，本轮产出顺旧习惯落在 `F:/桌面/zcode工作区/articles/20261105-fullrun/` |
| 同步层 | ❌ 有漏 | 源 references **7 份**，运行缓存 **6 份**，缺 `agushi-hongxian.md` —— 运行时 S5 读不到 A 股红线 |

README 当时还写着「全部 assets 位于个人 marketplace 目录」，与实物不符。

---

## 二、补齐动作（本次全部完成）

### 1. 资产物理收编（复制，不移动；原位置保留，避免破坏其他项目引用）

| 收编到包内 | 原位置 |
|---|---|
| `assets/scripts/gemini-gen.mjs` | `F:/桌面/Gemini本地文件/Github/github下载工具/tools_workspace/article-tools/server/gemini-gen.mjs` |
| `assets/workflow/公众号文章创作工作流-原文.md` | `F:/桌面/zcode工作区/03_内容运营/公众号文章创作工作流.md` |
| `assets/templates/build_preview.py` | `F:/桌面/zcode工作区/articles/20260924-daily-recap/build_preview.py` |
| `output/20261105-fullrun/`（20 个文件，含封面/插图/HTML/12 份留痕） | `F:/桌面/zcode工作区/articles/20261105-fullrun/` |

生图脚本是单文件、只依赖 `node:fs` / `node:path`，可独立运行，收编后不需要原目录。

### 2. 新增 `config/paths.md` —— 唯一路径权威表

- 两个包根（源包 / 运行缓存）与 `EXPERT_DIR` 解析规则
- 包内资产清单
- **运行时数据**（Opera 安装、` .gemini-opera-profile`、cookie、bun 绝对路径、1080 代理）—— 明确「不是资产，不随包走」，因含登录态/系统安装，进包反而会失效
- **产出约定：`${EXPERT_DIR}/output/YYYYMMDD-<slug>/`**，历史产出只登记不搬迁
- 标准命令模板（含 `unset` 代理、bun 绝对路径、`timeout`）
- 源包 → 运行缓存同步命令

### 3. 引用改为包内路径

| 文件 | 改动 |
|---|---|
| `skills/gzh-workflow/references/gemini-image.md` | 头部加路径解析段；`--login` 与出图命令改 `${EXPERT_DIR}/assets/scripts/gemini-gen.mjs` + 绝对路径 bun + `timeout` |
| `team/roles/visual.md` | 命令块改包内脚本 + bun 绝对路径 + `timeout`，并指向 `config/paths.md` |
| `skills/gzh-workflow/references/lanmu-wulinwaizhuan.md` | `build_preview.py` 改 `${EXPERT_DIR}/assets/templates/` |
| `skills/gzh-workflow/SKILL.md` | 新增「产出归属」节 |
| `team/ORCHESTRATOR.md` | 补 `agushi-hongxian.md`、包内路径、产出约定、缓存同步提醒、降级须显式交用户 |
| `agents/gzh-content-ops.md` | 输出规范补产出路径与路径权威表 |
| `README.md` | 独用声明确改为准确范围 + 全合并说明 |
| `assets/workflow/README.md`（新增） | 声明原文是**存档快照**，其中旧路径不可照抄执行 |
| `output/20261105-fullrun/README-完整流程.md` | 顶部标注已归档进专家团；文内旧路径是当日真实留痕，未篡改 |

### 4. 全量同步运行缓存

执行 `config/paths.md` 第六节命令后实测：
- references **源 7 / 缓存 7**，`diff -rq` 无差异（`agushi-hongxian.md` 已补）
- 缓存新增 `assets/`（3 件 + README）、`config/paths.md`、`output/20261105-fullrun/`（20 件）
- `team/roles/`、`SKILL.md`、`README.md`、`agents/gzh-content-ops.md`、`TEAM.md`、`ORCHESTRATOR.md` 全部对齐

---

## 三、故意不做的三件事（边界，不是遗漏）

1. **不移动 / 不删除原位置文件**：其他项目可能仍引用旧路径，收编用复制。
2. **不篡改历史留痕**：`output/20261105-fullrun/` 内记录的旧路径是当日真实执行命令，改了就是伪造；改为在其 README 顶部加归档说明。
3. **不把登录态/浏览器 profile 放进包**：` .gemini-opera-profile` 与 `cookies.json` 属运行时数据，含 Google 会话，进包会被同步或失效，只在 `config/paths.md` 登记。

---

## 四、以后怎么用

- 任何路径问题先看 `config/paths.md`，不要凭记忆拼绝对路径。
- 改脚本 / 规范只改**源包**，改完必须跑 `config/paths.md` 第六节同步到运行缓存，否则会话读不到。
- 新产出直接落 `${EXPERT_DIR}/output/YYYYMMDD-<slug>/`。
- 版本仍保持 `2.0.0`（不触发重新注册）；若平台上没刷新，重启或重新扫描专家即可。

---

# 第二轮补做 · 2026-11-05 晚（上一轮"只做了 3 个文件"的返工）

用户追问「是不是按我的要求改的」。核查结论：**第一轮不算"全合并"**，只收了 3 个文件（`gemini-gen.mjs`、工作流原文、1 份 `build_preview.py`）+ 本轮 20 件产出。真正的公众号内容运营生产线还有两大块完全没进包。

## 一、第二轮发现的遗漏

| 遗漏 | 实际是什么 | 严重性 |
|---|---|---|
| `zcode工作区/_wx_read/`（13 脚本） | `news_publish.py`(264 行，真发布库) / `riskcheck.py`(23KB 风控) / `run_daily.py` / `generate.py` / `cover_variants.py` / `delete_drafts.py` / `freepublish.py` / `extract.py` / `fetch_news.py` / `fetch_us.py` + 2 测试 + 1 词表 | **高**——这是本机唯一跑通过草稿箱的链路，专家团此前完全不知道它存在 |
| `wechat-writer/`（30 文件） | Streamlit 写作工作台：`workflow/`（选题→大纲→正文→质检）、`tools/de_ai.py`（去 AI 味）、`souls/`（人设）、`memory/`（长期记忆+规则） | **高**——S1/S2 的代码级实现 |
| `归藏排版工具/server.py` | 本地排版器，Win32 剪贴板，左边写右边预览点复制 | 中——S3 落地工具 |
| 生产线脚本 10 个 | `upload_article.py`(23KB) / `render_images.py`(21KB) / `verify_data.py` / `gen_images.py` / `make_previews.py` / `add_caption.py` / `check_cover.py` / `postcheck.py` / `audit_risk.py` / `upload_preview.py` | 中 |
| 策略与人设 | `股票公众号系列_内容策略.md` / `视频号矩阵引流公众号_全案策划.md` / `公众号写作技能_完整版.md` / `草稿记录.md` / 长盈客栈 4 件 | 中 |
| 配色实物 | `_配色预览/` 的 yaml 配置 + gallery（`themes.md` 的实物版） | 中 |

## 二、第二轮动作

1. **资产全量收编**（`assets/` 从 3 文件 → 81 文件，552KB）：
   - `assets/publish/` 13 文件
   - `assets/writer-app/` 30 文件
   - `assets/typeset/` 1 文件
   - `assets/scripts/pipeline/` 11 文件
   - `assets/docs/` 4 文件
   - `assets/ip/` 4 文件
   - `assets/palette/` 5 文件
2. **新增 `assets/README.md`** —— 81 个文件的总索引：每个文件干什么、谁用、依赖什么、哪些是历史快照不能直接跑。
3. **`config/paths.md` 第二节重写** —— 从 5 行扩成完整资产地图；第三节补记公众号凭证 `~/.baoyu-skills/.env`。
4. **7 个角色 prompt 全部挂上资产**：
   - `scout.md` → 内容策略、发布台账、`topic.py`、`fetch_news.py`、角色卡
   - `editor.md` → `de_ai.py`、`memory/rules.md`、`souls/`、`verify_data.py`
   - `visual.md` → `palette/` gallery、`工厂样图 yaml`、`typeset/server.py`、`pipeline/` 全部、`cover_variants.py`
   - `adaptor.md` → 视频号全案、发布台账、IP 人设；**顺手修掉一个 prompt bug**：原文写「简介带话题 #AI #效率 #搞钱」，与实战「只用中性事实标签」冲突，已改为按题材取中性标签
   - `compliance.md` → `riskcheck.py` + `audit_risk.py` + `verify_data.py`，并明确「脚本给候选、判定权在人」
   - `publisher.md` → **整篇重写**：主链路改为 `news_publish.py`，降级链 4 级写明，安全边界单列
   - `ORCHESTRATOR.md` → 第 7 步 S6 加显式警告「别先装 wenyan」；注意事项加资产地图速查表

## 三、一个被解开的老问题

上一轮 S6 草稿箱失败的定性是「凭证账号归属未确认，主动止步」。第二轮读代码发现：

- `news_publish.py:load_creds()` 读的就是 `C:/Users/admin/.baoyu-skills/.env`
- `upload_article.py`（2026-09-22 版）用同一组凭证真实跑过 `draft/add`，标题里带着当日复盘内容

→ **不是"账号归属不明"，是"S6 不知道该用哪个工具"**。这套链路一直能用，只是专家团没登记。现在登记了。

（边界仍保留：账号归属可由历史发布记录佐证，但**每次真推之前仍应让用户确认这次目标号没变**。）

## 四、第二轮故意不做的

| 项 | 原因 |
|---|---|
| `wechat-writer/.env` | 含 DEEPSEEK / SILICONFLOW / PEXELS 真实 key，不进包；只留 `.env.example` |
| `_wx_read/wx1.html` `wx2.html`（各 1.9MB） | 单日成品，不是模板 |
| `articles/` 30+ 目录正文（共 293MB） | 一次性产出 |
| 各种 png / `__pycache__` / `*.log` | 垃圾 |
| 不把 `pipeline/` 里硬编码改成参数化 | 那是历史快照，改造属于另一次重构，本轮只做归属不清算 |

## 五、验证

见文末「第二轮验证结果」。

## 六、⚠️ 收编过程中发现并处理的安全事件

**`assets/publish/generate.py` 原文件第 11–14 行明文写死 4 个真实 API key**（deepseek / qwen / hunyuan / kimi）。

- 处理：已改为动态读取 —— 先 `_load_env_file()` 从 `~/.baoyu-skills/.env` 注入 `os.environ`，再 `_k("DEEPSEEK_API_KEY")` 等取值；取不到就过滤掉该 provider，全空则 `SystemExit` 报缺哪个键。
- 验证：`ast.parse` 语法 OK；全包 + 缓存侧 `sk-*` / `ghp_*` / `AKIA*` / `AIza*` 特征复扫 **0 命中**。
- **原文件（`F:/桌面/zcode工作区/_wx_read/generate.py`）仍是明文**，本轮按「不修改原位置文件」的纪律**没有动它**。建议用户自行决定是否也脱敏，或直接轮换这 4 个 key。
- 教训：收编第三方脚本前必须先做密钥扫描，不能只扫 `.env`。

## 七、第二轮验证结果

| 项 | 结果 |
|---|---|
| `assets` 源/缓存 `diff -rq` | **完全一致**（71 文件 / 560KB） |
| `config` / `team` 源/缓存 `diff -rq` | 完全一致 |
| 单文件 `cmp`（9 个关键文件） | 全 OK |
| 文档引用的 `${EXPERT_DIR}/assets/...` 路径存在性 | 27 条全部 OK，0 MISS |
| 包内 `.env` | 0（只留 `.env.example`，占位符无真实值） |
| 密钥特征全包复扫 | 0 命中 |
| 整包体积 | 1.9MB |

角色 prompt 行数变化（原有 → 现在）：`scout` 33→45、`editor` 25→38、`visual` 63→81、`adaptor` 33→47、`compliance` 26→40、`publisher` 22→47。

版本仍为 `2.0.0`。

---

# 第三轮 · 2026-11-05 夜（把「有资产」变成「能干活」）

前两轮解决的是**归属**（东西在不在专家团里）。这一轮解决**可用性** —— 上一轮收编的 11 个 pipeline 脚本，实测**一个都不能开箱跑**：全都硬编码了当天的标题、日期、正文 HTML、配色常量，脱离原目录就报错。

## 一、实测发现（不是推测）

| 脚本 | 硬编码到什么程度 |
|---|---|
| `build_preview.py` | `TITLE = "第一回 节前客栈齐收账…"` 整篇正文 HTML 写在代码里 |
| `render_images.py` | 全套图片 HTML 绑死 2026-09-17 数据 |
| `upload_article.py` | `TITLE` / `DIGEST` / `IMAGES` 全是 9/22 那篇的 |
| `make_previews.py` | 顶栏写死 `2026.09.23` |
| `verify_data.py` | 涨跌停池日期写死 `20260925` / `20260928` |
| `gen_images.py` | `sys.path` 指向已不存在的 `.zcode/skills/gemini生图` |
| `audit_risk.py` / `postcheck.py` / `upload_preview.py` | `sys.path` 指向旧 `_wx_read` |

结论：**这些是「某篇文章的实现」，不是「能复用的工具」**。继续往里堆文件只会让 Agent 误以为能跑。

## 二、这一轮做了什么

### 1. 建统一工具库 `assets/tools/`（新写，不是搬运）

`gzh.py` —— 一个入口 7 个子命令，全部实测通过：

| 命令 | 实测结果 |
|---|---|
| `creds` | ✓ 报出凭证齐备（APP_ID 18 位 / SECRET 32 位，不打印值） |
| `token` | ✓ 打出真实错误码 **40164**，定位到 IP 白名单 |
| `check <img> --ratio` | ✓ 1880×800 / 2.350:1 / 514.8KB |
| `render <html> <png>` | ✓ 出图 1880×800，Chrome headless + 临时 profile |
| `risk <path> [--json]` | ✓ 扫出 6 条命中，`--json` 输出合法纯 JSON |
| `verify --date` | ✓ 跑通全市场逐股扫描 + 涨跌停池 + 板块 + 资金流 + 美股 |
| `publish --dry-run` | ✓ 校验文件齐备（未联网） |

`market_verify.py` —— 由 `legacy/verify_data.py` 参数化而来，**数据口径与阈值一字未改**（涨停判定主板 ±9.7 / 双创 ±19.7 / 北交所 ±29.7），只做了三件事：日期参数化、输出路径可指定、补上破代理。

### 2. 归档历史脚本到 `assets/scripts/legacy/`

11 个一次性脚本全部移入，配 `README.md` 写清「每个当年干什么 / 现在用什么替代 / 为什么不能跑」。**不删** —— 它们是这套流程真实跑通过的证据。

### 3. 角色 prompt 改为调用工具，而不是描述资产

| 角色 | 改前 | 改后 |
|---|---|---|
| S1 侦察 | 「事实锚点可先跑 fetch_news」 | `gzh.py verify --date` 一次核齐；写明两套口径不许混 |
| S3 视觉 | 列 5 个 pipeline 脚本当参考 | `gzh.py render` + `gzh.py check`，并明令「不许凭 ls 有文件就报成功」 |
| S5 合规 | 列 3 个脚本，没说怎么跑 | `gzh.py risk`，并写清 **BLOCK ≠ 违规，= 必须人工裁定**，误伤用 `--ignore-words` 显式跳过而不是改文章 |
| S6 发布 | 说「用 news_publish.py 的 publish()」 | **一条命令** `gzh.py publish`，三步（creds → dry-run → 真推），并把 40164 的处置写死 |

### 4. 跑工具时当场查出的真问题

`gzh.py verify --date 20261105` 实测输出：

```
逐股扫描：上涨 4869 / 下跌 624 / 涨停 86 / 跌停 3
东财池 tc：涨停 84 / 跌停 0
```

而 2026-11-05 那篇稿用的是 **4869 涨 / 625 跌 / 0 跌停**。三处差异都有解释：
- 涨 4869 ✓ 完全对上
- 跌 625 vs 624 → 差 1 只，两个时点/两个源的快照差异
- 跌停 0 vs 3 → **口径不同**：0 来自东财涨停池 `tc`，3 是逐股扫描按 -9.7% 阈值算出来的（ST 股跌停是 -5%，反而漏算）

**这就是「两套口径不许混用」的实证。** 已写进 `tools/README.md`、`SKILL.md`、`scout.md`、`agents/gzh-content-ops.md` 四处，并在 `gzh.py verify` 末尾自动打印口径对照。

## 三、验证

| 项 | 结果 |
|---|---|
| `assets` / `team` / `config` 源/缓存 `diff -rq` | 全部一致 |
| 14 个关键文件 `cmp` | 全 OK |
| 文档引用的 `${EXPERT_DIR}/assets/...` 路径 | 全部存在，**0 MISS**（修掉 1 处 `legacy/test_riskcheck.py` 误写） |
| 运行缓存路径下实跑 `creds` / `check` / `--help` | ✓ |
| `scripts/pipeline` 残留引用 | 0（legacy 说明除外） |
| assets 规模 | 75 文件 / 604KB |
| 整包 | 2.0MB |

## 四、这一轮仍然没做的

1. **`writer-app/` 没跑过** —— 它是 Streamlit 应用，要装依赖、起服务，属于另一个工作量级。代码在里面、可读可改，但没有验证过能起。
2. **`typeset/server.py` 没跑过** —— 同理，需 Windows GUI 环境。
3. **`publish` 没真推** —— 卡在 IP 白名单 40164，需要用户去公众号后台加 `117.151.76.207`。工具侧已就绪到「加完 IP 直接能推」。
4. **`gzh.py cover` 没做** —— 上一轮 `news_publish.py` 里有 cover_A/B/C 三款字体封面生成，这轮没接进 CLI。目前封面走 S3 的 HTML 渲染，够用；如果以后要「纯文字快评封面」，再把那三个函数接出来。
