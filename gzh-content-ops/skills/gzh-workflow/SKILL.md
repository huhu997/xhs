---
name: gzh-workflow
description: 公众号写作全流程工作流：一句话选题 → 主线/分节/张力 → 16主题×8版式排版 → 零积分Gemini配图 → 去AI味≤20分 + 平稿检测双门槛 → 草稿箱交付；含栏目化连载模板。
---

# 公众号内容工作流（gzh-workflow）

本 skill 是「墨稿」专家跑通的真实流水线资产。当需要实际产出一篇公众号稿、选型排版主题、做去 AI 味改写、或生成封面配图时加载本 skill，并按下方 references 执行。

> **2026-11-11 修订**：新增第 7 份规范 `references/zhangli.md`（张力与节奏）。
> 旧版只有"减法"标准（去 AI 味），产出稿信息齐、逻辑顺却**很平**。现改为**双门槛**：朱雀 ≤20/100 管"像不像人"，平稿检测 ≤1 条管"想不想读"。任一不过不得进 S3/S6。

## 何时用
- 把一句话方向变成排好版、可进草稿箱的成稿
- 选排版主题 / 配色
- 去 AI 味改写与质检
- 生成 2.35:1 / 1:1 / 16:9 / 3:4 封面与插图（Gemini 零积分或本地渲染）
- 栏目化连载（如《A股每日复盘》群像体）需要固定角色与章节骨架

## 流水线（8 步，没有第 9 步）
1. **收方向**：一句话（事件 / 话题 / 痛点），不写大纲、不教提示词
2. **定主线**：悬念式主线 + 4–6 分节；**悬念必须落成 `zhangli.md` 第六节「张力三问」的书面答案**（在哪一段推翻读者预期 / 最慢与最快各是哪段 / 结尾是口子还是总结），答不上不许开写。金句 ≤2 且不相邻、不得在结尾；标题按 `references/biaoti-gongshi.md` 出 **5 选 1**（带公式名 + 分数）
3. **写正文**：八段式只是容器，**逻辑骨架必须立住**——按「现象 → 外因 → 内因 → 定性 → 框架」推进；因果链要摆证据（跌的是同一批、顺序对应）而非断言。**同时必须过 `zhangli.md` 第二节五条硬指标**：落差 ≥1 处、长短交错、1 个核心场景写透其余掠过、开头 3 行钩子伤口、结尾留口子。金句须从上文逻辑挣出，不得空泛升华；结尾刻度须从本文结构长出，不套通用模板。本地化人话，规避去 AI 味三条机制，**但去味只削"整齐"不削"起伏"**（边界见 `zhangli.md` 第四节）。
   - 若指定栏目（如「A股江湖每日说书」），先加载 `references/lanmu-wulinwaizhuan.md` 用其角色卡与章节骨架；栏目骨架不豁免张力五指标
4. **定视觉**：16 主题 × 8 版式先出 **3 套候选**，用户挑定 1 套再渲染（`references/themes.md`）
5. **配图**：2.35:1 双比例主封面 + 16:9 正文插图；默认走 Gemini 零积分（`references/gemini-image.md`），尺寸见 `references/cover-spec.md`。**铁律：正文内的数据图表一律用内联 HTML（表格 / 条形 `<div>`），文字是 DOM 文字，微信里永不糊；禁止把数据图表栅格化成 PNG 当插图塞进正文——微信会二次压缩，手机上文字必看不清。**配色同样有铁律：数据卡浅底深字、红涨绿跌用高对比深字+亮条、金色只做装饰、小字 ≥14px 深色，并禁用 `display:flex` / `border-radius` / `background` 简写（详见 `team/roles/visual.md` 的「正文图块配色铁律」）。出稿前按 375 宽逐段审图块，推完从草稿箱 API 回拉核对色值已生效。**署名铁律：图上的账号/署名文字只能取 `config/account.md` 的 `cover_byline`，出图前 `gzh.py account --live` 核对微信后台昵称、出图后 `gzh.py brand <本轮目录> --strict` 扫旧名；账号改名按该文件第 4 节 SOP 重渲染全部含署名图并重推草稿，封面必须从 HTML 渲染（PNG 里的字扫不出来）。**
6. **双门槛终检**：① 朱雀 AI 疑似度 ≤20/100（`references/ai-taste.md`）；② **平稿检测命中 ≤1 条（`references/zhangli.md` 第三节）**。任一不过都打回；平稿命中 ≥2 条**必须回第 3 步重写，不是润色能救的**。S2 去味时只削整齐、不削起伏，允许补极短句 / 拆长段 / 调段落顺序制造落差。两道分数都写进交付物。
7. **合规**：AI 人设红线审查，推工具/课程须标「推广」
8. **交付**：推公众号草稿箱，发布用户手动点

## 差异化四根支柱
- **终点不同**：别人交文字，你交草稿箱（省 4 个纯手活：找图/配图/排版/复制粘贴）
- **双门槛可量化**：AI 味 ≤20/100 **+ 平稿检测 ≤1 条**，都是硬指标不是形容词；只过第一道会产出"干净但平"的废稿
- **配图零积分**：Gemini 网页端 VIP 额度出图，Opera 抓一次 Cookie 后免浏览器；不是每张图烧积分
- **栏目可连载**：群像角色卡 + 连续回目，把单篇文章做成追更栏目

## 工具库（★ 机械动作全部走这里，别写临时脚本）

一个入口覆盖流水线里所有「跑命令」的环节：

```bash
GZH="python ${EXPERT_DIR}/assets/tools/gzh.py"

$GZH verify --date 20261105                     # 第 1–3 步：盘面数据一次核齐（涨跌家数/涨跌停池/板块/资金流/美股）
$GZH render a.html a.png --width 1880 --height 800   # 第 5 步：HTML→PNG（Chrome headless）
$GZH check cover.png --ratio 2.35               # 第 5 步：封面比例校验
$GZH account --live                             # 第 5 步：当前账号名/封面署名，核微信后台昵称
$GZH brand output/<本轮目录> --strict           # 第 5 步：扫旧账号名（署名改干净没）
$GZH risk 04.md 07.md                           # 第 7 步：合规扫 BLOCK/WARN
$GZH creds && $GZH publish --html --title --cover --dry-run   # 第 8 步：体检 → 预演
$GZH publish --html --title --cover --digest "…"              # 第 8 步：真推草稿箱
```

用法与坑见 `${EXPERT_DIR}/assets/tools/README.md`。
`assets/scripts/legacy/` 是历史一次性脚本，**只作参考不要跑**。

## 产出归属（全合并后统一约定）
- **所有产出统一落 `${EXPERT_DIR}/output/YYYYMMDD-<slug>/`**，不再落到 `zcode工作区/articles/`。
- 包根、`EXPERT_DIR` 解析、包内资产清单、运行时数据（Opera profile / cookie / bun 绝对路径）与同步命令，全部以 `${EXPERT_DIR}/config/paths.md` 为唯一权威表。
- 生图脚本用包内 `${EXPERT_DIR}/assets/scripts/gemini-gen.mjs`，`bun` 用 `C:/Users/admin/.bun/bin/bun.exe`（不在 PATH），调用必须加 `timeout`。
- 改完源包必须同步运行缓存，否则会话读不到（曾漏同步 `agushi-hongxian.md`）。

## 合规
- 只走官方草稿箱接口，不群发、不群控
- 不承诺涨粉/收益，标题不写"保证""最"
- AI 生图须标注；配图配色必须与正文同源
- 财经稿数字必须跑 `gzh.py verify` 得出，**涨跌家数用逐股扫描、涨跌停只数用东财池 tc，两套口径不许混**

## References（七件套）
- `references/themes.md` — 16 套配色主题 × 8 种版式的精确色值与适用题材
- `references/ai-taste.md` — 去 AI 味机制 + 检测门槛 + 反向误删清单 + A/B 双组自检
- `references/zhangli.md` — **★ 张力与节奏：落差 / 长短交错 / 密度差 / 钩子伤口 / 结尾留口子 / 平稿检测 / 与去味机制的边界 / 改写示范 / 张力三问**（2026-11-11 新增，双门槛之一）
- `references/cover-spec.md` — 封面/插图尺寸、2.35:1 双比例安全区、两条出图路线
- `references/gemini-image.md` — Gemini 零积分生图：登录、Cookie、prompt 模板、排障、降级链
- `references/biaoti-gongshi.md` — 标题情绪张力公式：8 个可套句式 + 5 维打分卡 + 红线词 + 5 选 1 交付格式
- `references/lanmu-wulinwaizhuan.md` — 栏目模板：A股江湖每日说书（群像角色卡 + 章节骨架 + 外传规则）
- `config/account.md` — **账号名 / 封面署名唯一真源**（`account --live`、`brand`、`publish` 旧名拦截都读它；账号改名 SOP 在第 4 节）
