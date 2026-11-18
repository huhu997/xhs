# 11 · 发布官报告（gzh-publisher）

- 轮次：`20261105-fullrun`　日期：2026-11-05
- 标题：**收盘后翻到涨跌家数那页，我盯错了一整天**
- 合规前置：S5 发布前独立终检**双渠道通过**（公众号 + 视频号 + 标题，0 命中项）；`10-compliance-report.md`（20:49 更新）追加的「第十节 补审结论（图注与封面文案）」亦**通过（不打回）、阻断性命中项 0 项**，明确「S6 可据此推草稿箱」→ **合规侧非阻塞项**
- 发布官职责边界：只落草稿箱，**绝不群发、绝不自动点发布**

---

## 0. 结论速览

| 项 | 结论 |
|---|---|
| **草稿箱状态** | **失败 / 未推送**。无 `media_id`，公众号草稿箱未产生任何新草稿 |
| **是否走兜底** | **未走兜底真推**；但对兜底做了完整实测（技能安装、bun、dry-run、CDP 登录态、凭证文件），见 §3 |
| 是否群发 / 点发布 | **否**。全程未调用任何群发/发布接口，未点击任何发布按钮 |
| 是否伪造成功 | **否**。未编造 `media_id`，未写「已推草稿箱」 |
| 是否修改凭证文件 | **否**。只读，且只读取「元信息」，未打印任何密钥值，未把密钥写入任何交付文件 |

> **重要新情况（超出团长预检）**：本机 `C:/Users/admin/.baoyu-skills/.env` 中**存在形似真实的公众号凭证**（`WECHAT_APP_ID` 18 位、`WECHAT_APP_SECRET` 32 位非空），且 Chrome CDP 9222 端口正在监听。兜底路径**可能**具备推送能力。但账号归属无法确认，属于团长预检之外的新发现，我已**主动止步、未擅自使用这组私有凭证真推**，详见 §3.3 与 §6，需用户/团长裁决。

---

## 1. 草稿箱状态

**失败（未推送）。无 `media_id`。**

准确表述：这不是「接口返回失败」，而是**两条路径都未真正发出 `draft/add` 请求**——主路径在凭证检查阶段即退出，兜底在确认账号归属前主动止步。因此公众号侧没有产生任何草稿，也不存在任何需清理的残留。

---

## 2. 主路径 `wechat-publisher` 实测

### 2.1 技能到底要什么凭证、有没有本机可读配置文件

已用 Skill 加载并逐字读取 `SKILL.md`、`scripts/publish.sh`、`scripts/setup.sh`、`references/troubleshooting.md`：

| 要求 | 出处 | 本机实测 |
|---|---|---|
| 环境变量 `WECHAT_APP_ID` / `WECHAT_APP_SECRET` | `SKILL.md` §2、`publish.sh:48` | `[UNSET]` / `[UNSET]` |
| 凭证回退读取 `$HOME/.openclaw/workspace/TOOLS.md` | `publish.sh:16`、`setup.sh:5` | 不存在（`C:/Users/admin/.openclaw/workspace/TOOLS.md` absent） |
| `SKILL.md` 第 48 行写的 `/Users/leebot/.openclaw/workspace/TOOLS.md` | `SKILL.md` | macOS 绝对路径，Windows 上不存在 |
| `wenyan-cli` 未安装时自动 `npm install -g @wenyan-md/cli` | `publish.sh:23` | 实测触发并**安装成功** |
| 发布命令 `wenyan publish -f <md> -t lapis -h solarized-light` | `publish.sh:89` | 未执行到该行 |
| frontmatter 强制 `title` + `cover` | `SKILL.md`、`troubleshooting.md` §4 | `04-article-edited.md` 无 frontmatter（即便凭证齐备也需补） |
| 封面尺寸提示 1080×864 | `publish.sh:103` | 与本轮 1880×800（2.35:1）封面规格不一致，若走主路径需另备 |
| IP 白名单 | `SKILL.md` §2、`troubleshooting.md` §1 | 未知，`curl ifconfig.me` 失败 |

**结论**：主路径唯一的凭证来源是「shell 环境变量」或「`$HOME/.openclaw/workspace/TOOLS.md`」，两者本机都不存在；技能自带的 macOS 绝对路径同样不存在。没有可直接读取的本机配置文件。

### 2.2 实测原始结果（原文照录）

**实测 A — 直接调用 `wenyan publish`（SKILL.md 标准命令）**

```
$ wenyan publish -f "F:/桌面/zcode工作区/articles/20261105-fullrun/04-article-edited.md" -t lapis -h solarized-light
C:\Users\admin\.workbuddy\binaries\PortableGit\versions\1.3.0\bin\bash.exe: line 14: wenyan: command not found
[wenyan publish exit=127]
```

**实测 B — 运行技能官方入口 `publish.sh`（原始输出）**

```
$ bash "C:/Users/admin/.workbuddy/skills/wechat-publisher/scripts/publish.sh" "F:/.../04-article-edited.md"
❌ wenyan-cli 未安装！
正在安装 wenyan-cli...
npm warn deprecated mathjax-full@3.2.2: Version 4 replaces this package with the scoped package @mathjax/src
added 259 packages in 2m
✅ wenyan-cli 安装成功！
❌ 环境变量未设置！
请在 TOOLS.md 中添加微信公众号凭证：

  ## 🔐 WeChat Official Account (微信公众号)

  export WECHAT_APP_ID=your_app_id
  export WECHAT_APP_SECRET=your_app_secret

或者手动设置环境变量：
  export WECHAT_APP_ID=your_app_id
  export WECHAT_APP_SECRET=your_app_secret

或者运行：
  source ./scripts/setup.sh
[publish.sh exit=1]
```

配合环境变量实测（只报是否设置，未打印值）：

```
WECHAT_APP_ID    : [UNSET]
WECHAT_APP_SECRET: [UNSET]
wenyan: NOT FOUND on PATH            # 运行 publish.sh 之前
node v22.22.2 / npm 10.9.7
mac TOOLS.md: NOT FOUND (Windows 上预期如此)
```

### 2.3 失败根因

`publish.sh` 的检查顺序是 `check_wenyan → check_env → check_file → publish`。自动装好 `wenyan-cli` 后，卡在 `check_env`（`publish.sh:45-65`）：环境变量为空且 `TOOLS.md` 不存在，`load_credentials` 读不到任何值，于是 `exit 1`。**根本没有执行到 `wenyan publish`，也没有调用任何微信接口。** 根因是「官方凭证缺失」，非接口异常、非内容问题。

### 2.4 环境副作用（透明披露）

`publish.sh:23` 的自动安装逻辑真实执行了 `npm install -g @wenyan-md/cli`，**全局环境已变更**：`wenyan` 现为 `2.0.12`（`command -v wenyan` → `C:/Users/admin/.workbuddy/binaries/node/versions/22.22.2-6/wenyan`），新增 259 个全局包。这是技能自带行为，非我额外引入；**未修改任何凭证文件**。如不需要，用户可自行 `npm uninstall -g @wenyan-md/cli`。

---

## 3. 兜底 `baoyu-post-to-wechat` 实测

### 3.1 技能与写入边界

- 技能**已安装**（`C:/Users/admin/.workbuddy/skills/baoyu-post-to-wechat`，v1.118.2），并非缺失。
- 读取 `SKILL.md` 与 `scripts/wechat-api.ts`：API 方式的写入端点只有 `media/uploadimg`、`material/add_material`、`draft/add`（`wechat-api.ts:74-76, 340-345, 846-858`）。对 `scripts/` 全目录 Grep `freepublish|mass_send|message/mass`，**未发现任何群发/发布接口** → 兜底真推也只落草稿箱，符合安全边界。
- `--dry-run` 在 `wechat-api.ts:776-789` 直接 `return`，位于 `loadCredentials`（791 行）与 `publishWith`/联网（810 行起）**之前** → 零 API 写入、零凭证读取，是安全的只读实测。
- 凭证优先级（`wechat-api.ts:516-519`）：环境变量 → `<cwd>/.baoyu-skills/.env` → `~/.baoyu-skills/.env`。
- `SKILL.md:52` 与 `references/config/first-time-setup.md:12` 明确：找不到 `EXTEND.md` 时须先完成 first-time setup，且写明 **「BLOCKING OPERATION: This setup MUST complete before ANY other workflow steps」**。

### 3.2 实测原始结果

```
已安装 skills 列表：baoyu-post-to-wechat 在列            # 技能存在
.baoyu-skills/.env EXISTS, size=84 bytes
  仅列键名（等号后的值全部屏蔽）:
    WECHAT_APP_ID
    WECHAT_APP_SECRET
  [命中] .env 内含微信/公众号相关键名或 appid

.env 凭证「元信息」（只报键名/长度/形态标签，绝不打印任何值）:
  WECHAT_APP_ID     : 值长度=18 : FORMAT-OK（形似真实 appid）
  WECHAT_APP_SECRET : 值长度=32 : NONEMPTY（非空，形态未判定）

Chrome / CDP 登录态：
  msedge.exe 多个进程在运行
  http://127.0.0.1:9222/json/version → {"Browser": "Chrome/155.0.8059.85", "Protocol-Version": "1.3", ...}   # 9222 在监听

兜底运行时：
  bun: NOT FOUND；npx 存在；npx -y bun --version → 1.4.4（可拉起）

EXTEND.md 三个候选路径：
  absent: F:/桌面/workbuddy 工作区/.baoyu-skills/baoyu-post-to-wechat/EXTEND.md
  absent: C:/Users/admin/.config/baoyu-skills/baoyu-post-to-wechat/EXTEND.md
  absent: C:/Users/admin/.baoyu-skills/baoyu-post-to-wechat/EXTEND.md

IP 白名单：curl ifconfig.me FAILED（无法确认本机公网 IP，也无法自助修复）
```

**兜底 `--dry-run` 实测（真实运行脚本，原文）**

```
$ npx -y bun wechat-api.ts 08-article-paste.html --title ... --cover ... --theme default --dry-run
[wechat-api] Using HTML file: F:\桌面\zcode工作区\articles\20261105-fullrun\08-article-paste.html
[wechat-api] Title: 收盘后翻到涨跌家数那页，我盯错了一整天
[wechat-api] Type: news
{
  "articleType": "news",
  "title": "收盘后翻到涨跌家数那页，我盯错了一整天",
  "htmlPath": "F:\\桌面\\zcode工作区\\articles\\20261105-fullrun\\08-article-paste.html",
  "contentLength": 9538
}
[dry-run pipeline exit=0]
```

即：兜底脚本本身可用、bun 可用、能正确解析我们的粘贴版 HTML 并生成公众号内容。**但 `--dry-run` 不验证凭证有效性，也未调用任何微信 API**。

### 3.3 为何未执行真正的 `draft/add`（主动止步）

四条 blocker，任一条都足以让我停下并把决策权交回：

1. **账号归属无法确认（最要紧）**。三个 `EXTEND.md` 偏好文件全部缺失，按 `SKILL.md:52` 与 first-time-setup 的 BLOCKING 规则，必须先完成交互式首配置并写入 `EXTEND.md` 才能继续；无 `accounts:` 配置，就无法判断 `~/.baoyu-skills/.env` 里这组凭证对应的是不是本轮目标公众号。**推错号 = 把内容写进另一个公众号草稿箱，属不可逆的外部写入事故**。
2. **凭证来源超出本轮授权与预检范围**。团长预检只覆盖 shell 环境变量与 `wenyan`；`~/.baoyu-skills/.env` 是 baoyu 技能族的**用户级、跨项目私有凭证**，是实测中新发现的。用一组未被预期、未被确认的私有凭证对外部账号做写入，按「影响共享状态的动作需先确认」原则，应先请示。
3. **IP 白名单未知**。`curl ifconfig.me` 失败，无法确认本机公网 IP 是否在公众号白名单；API 方式很可能返回 `errcode 40164`，且修复需用户登录 `mp.weixin.qq.com` 后台手动添加，非我可自助完成。
4. **团长整体基调**。预检结论「大概率推不出去是预期内的」，且「发布永远留给用户手动点」「绝不许伪造成功」。本轮核心交付是诚实的实测结论、缺失项与手动清单，而非替用户做授权决定。

因此：兜底做了**完整实测**，但**未真推**，标注为「未走兜底真推」。

---

## 4. 缺失项清单

| # | 缺失项 | 谁来解决 | 备注 |
|---|---|---|---|
| 1 | `WECHAT_APP_ID` / `WECHAT_APP_SECRET` 环境变量 | 用户 | 主路径唯一直接凭证来源 |
| 2 | `C:/Users/admin/.openclaw/workspace/TOOLS.md`（含 `export WECHAT_APP_ID=...` / `export WECHAT_APP_SECRET=...`） | 用户 | `publish.sh`/`setup.sh` 的回退读取路径，当前不存在；`SKILL.md` 的 macOS 路径在 Windows 上无效 |
| 3 | IP 白名单（本机公网 IP 需加入公众号后台「开发 → 基本配置 → IP 白名单」） | 用户 | 状态未知，`curl ifconfig.me` 失败；API 方式必需 |
| 4 | 主路径所需 frontmatter（`title` + `cover`）与 1080×864 封面 | 用户/排版 | 现有 `04-article-edited.md` 无 frontmatter；现有封面 1880×800 与脚本提示的 1080×864 不符 |
| 5 | 兜底 `EXTEND.md` 首配置（首命中路径任一） | 用户 | 三个候选路径全 absent；缺失时技能判定为 BLOCKING，须先交互式配置 |
| 6 | 兜底凭证的**账号归属确认** | 用户/团长 | `.env` 值形似真实，但不知对应哪个公众号，无法排除推错号 |
| 7 | 用户/团长对「使用 `~/.baoyu-skills/.env` 这组凭证真推」的**明确授权** | 用户/团长 | 本轮未获此授权，故未真推 |

---

## 5. 手动落草稿箱最短操作清单（照着做即可）

全程在浏览器里完成，**不需要任何命令行、不需要配置凭证**。

1. 用 Chrome/Edge 打开并登录 **<https://mp.weixin.qq.com/>**。
2. 左侧「内容与互动」→「草稿箱」→「新的创作」→ 选「**图文消息 / 写新图文**」，进入编辑器。
3. **标题**栏填：`收盘后翻到涨跌家数那页，我盯错了一整天`
4. **正文**：
   - 用 Chrome/Edge 打开本地文件 `F:/桌面/zcode工作区/articles/20261105-fullrun/08-article-paste.html`
   - 在渲染出的页面上 `Ctrl+A` 全选（从「开盘 / 收盘 / 盘后」时间轴到末尾免责声明），`Ctrl+C`
   - 回到公众号编辑器正文区 `Ctrl+V` 粘贴。该 HTML 所有样式均为内联样式，粘贴后时间轴、当日读数卡片、五个小标题、金句、免责声明都会保留。
   - ⚠️ 用 `08-article-paste.html`（**粘贴版**），不要用 `08-article.html`——后者含 h1 与刊头，贴进正文会重复标题。
5. **封面**：编辑器右侧「封面」→「本地上传」→ 选 `F:/桌面/zcode工作区/articles/20261105-fullrun/08-cover.png`（1880×800，2.35:1）。
6. **正文插图（选做）**：如需配图，在正文合适位置手动插入 `F:/桌面/zcode工作区/articles/20261105-fullrun/08-illustration.png`（16:9）。粘贴版 HTML **未内嵌任何 `<img>`**，这张图不会自动带过来，必须手动插。
7. **摘要（选填）**：可留空；如需填，建议「4869 只上涨、625 只下跌、跌停 0 只，上证却只涨 0.10%——盯了一下午的平线，问题多半在我自己。」
8. 作者、原创声明、赞赏等按你平时习惯设置，本轮不作改动。
9. ✅ **必须你自己点**：「**保存为草稿**」。
   - ❌ **绝不点**「发表 / 发布 / 群发」。发布永远留给你手动点。
10. 保存后到「草稿箱」确认该条已出现，即完成。

---

## 6. 需用户/团长裁决的一项（重要）

兜底**可能**能推成功，与团长「大概率推不出去」的预检不同。若你希望我改用 API 落草稿箱，请一次性确认三点：**① `~/.baoyu-skills/.env` 里的凭证就是本轮目标公众号；② 目标公众号 IP 白名单已包含本机公网 IP；③ 授权我执行 `draft/add`**。确认后最短命令（脚本只调 `draft/add`，不群发、不发布；不带 `--dry-run` 才会真推）：

```bash
cd "C:/Users/admin/.workbuddy/skills/baoyu-post-to-wechat/scripts"
npx -y bun wechat-api.ts "F:/桌面/zcode工作区/articles/20261105-fullrun/08-article-paste.html" \
  --title "收盘后翻到涨跌家数那页，我盯错了一整天" \
  --cover "F:/桌面/zcode工作区/articles/20261105-fullrun/08-cover.png" \
  --theme default
```

若仍缺 `EXTEND.md`，需按 `references/config/first-time-setup.md` 先完成一次首配置（会写入 `EXTEND.md`，属用户配置变更，建议你本人操作）。**在收到这三点确认前，我不会使用这组凭证发起任何真实写入。**

---

## 7. HTML 与终稿口径核对结论

核对对象：`08-article-paste.html` ↔ `04-article-edited.md`（去味终稿）。逐段比对 + 指定 5 项数字口径：

| 口径项 | `04-article-edited.md` | `08-article-paste.html` | 结论 |
|---|---|---|---|
| 上涨 4869 | 第 7 行「4869 只上涨」、第 47 行「这 4869 只里」 | 第 52 行读数卡「4869」、第 71 行、第 116 行 | ✅ 一致 |
| 下跌 625 | 第 7 行「625 只下跌」 | 第 57 行读数卡「625」、第 71 行 | ✅ 一致 |
| 跌停 0 | 第 7 行「跌停 0 只」 | 第 62 行读数卡「0」、第 71 行 | ✅ 一致 |
| 3689.91 / +0.10% | 第 5 行「3689.91，涨 0.10%」 | 第 69 行「3689.91，涨 0.10%」 | ✅ 一致 |
| 1.1 个百分点 | 第 21 行「差了 1.1 个百分点——1.19 减 0.10 是 1.09」 | 第 87 行同句 | ✅ 一致 |

顺带复核的其它数字（均一致）：2026-10-26 启用修订方案、单一样本权重 ≤15%、中国经济周刊 11 月 3 日、深证成指 1.19% / 创业板指 0.87% / 科创综指 1.38% / 差值 1.09、个别权重股跌 8% 左右、原油跌超 7%、燃油跌超 14%、低硫燃料油跌超 10%、现货黄金破 4100 美元、钯涨超 8%。

**逐段文字比对**：MD 的 5 个 H2 标题、全部正文段落、金句、免责声明，与 HTML 对应 `<p>` / `<h2>` 逐字一致；差异仅为排版转换（`<br>` 分行加粗、`---` 改为装饰线、斜体改为灰色小字）与纯视觉组件（L4 时间轴导航、「当日读数」数据卡片，其数字与正文完全一致）。

> **结论：正文数据口径 100% 一致，未发现 HTML 漏字、数字错或口径漂移。** 未改动任何文件。

---

## 8. 非口径类发现（单列，未改任何文件）

1. `08-article-paste.html` **不含任何 `<img>` 标签**。封面 `08-cover.png` 与插图 `08-illustration.png` 均未嵌入，走自动上传/API 或手动粘贴时都需单独上传（见 §5 第 5、6 步）。
2. 粘贴版按设计**已删除 h1 / 刊头 / 日期及其下装饰短线**（文件第 10 行注释明确说明），故与终稿 MD 的 `# 标题`、`> 2026 年 11 月 5 日 · 盘后笔记` 不对应——这是预期设计，**不算漏字**。含 h1/刊头的完整版 `08-article.html`（14037 bytes）存在，本轮未纳入逐字核对范围。
3. 主路径 `publish.sh:103` 提示封面 1080×864，与本轮 2.35:1 封面（1880×800）规格不同；若日后改走 `wenyan` 主路径需另备封面。
4. 本机其它配置文件排查：`TOOLS.md` / `.env` / `config.json` / `secrets.*` 类候选文件在 `C:/Users/admin` 与两个工作区下存在若干（多为各技能的 `.env.example`、toml 与工具配置）。含公众号凭证关键词的仅 `C:/Users/admin/.baoyu-skills/.env`（§3.2 已报元信息）。**仅报告"是否存在"，全程未打印任何密钥内容。**

---

## 9. 安全边界自证

- 未群发、未点发布、未调用任何群发/发布接口；唯一真实网络相关动作是 `npm install -g`（技能自带）与 `npx -y bun`（下载运行时），均非公众号写入。
- 未向公众号发出任何 `draft/add` / `uploadimg` / `add_material` 请求（兜底仅跑到 `--dry-run`，代码层在联网前 return）。
- 未修改任何凭证文件；读取 `.env` 时只输出键名、值长度与形态标签，**未输出任何等号右侧的实际字符**。
- 未把任何密钥写入本报告或任何交付文件。
- 未编造 `media_id`，未写「已推草稿箱」；草稿箱状态如实记为「失败 / 未推送」。
