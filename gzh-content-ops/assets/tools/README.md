# tools/ — 专家团工具库（真能跑，不是说明文档）

两个入口，都在这个目录：

| 文件 | 作用 |
|---|---|
| `gzh.py` | 统一 CLI：凭证体检 / 图片检查 / HTML 截图 / 合规扫描 / 数据核对 / 推草稿箱 |
| `market_verify.py` | A 股盘面多源核对器（由 `gzh.py verify` 调用，也可单独跑） |

运行时依赖（本机已具备）：Python 3.13 + Pillow 13、Chrome、`~/.baoyu-skills/.env` 里的 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`。

```bash
# 统一约定：gzh.py 在任何目录都能跑，路径全部显式传
GZH="python <EXPERT_DIR>/assets/tools/gzh.py"
```

---

## 一、按角色查：谁该用哪条命令

| 角色 | 命令 | 干什么 |
|---|---|---|
| **S1 选题侦察** | `gzh.py verify --date 20261105` | 盘面数据一次核齐：涨跌家数、涨跌停池、昨日涨停今日表现、板块、资金流、美股。**别再让模型凭记忆写数字** |
| **S3 视觉** | `gzh.py render a.html b.png --width 1880 --height 800` | HTML → PNG，Chrome headless，独立 profile 不抢锁 |
| **S3 视觉** | `gzh.py check cover.png --ratio 2.35` | 尺寸 / 比例 / 体积，比例不符直接 RC=2 |
| **S5 合规** | `gzh.py risk <file...> [--json]` | 机械扫 BLOCK/WARN，比人工扫得细；`--json` 给程序化处理 |
| **S6 发布** | `gzh.py creds` → `gzh.py publish ... --dry-run` → 去掉 `--dry-run` | 先体检、再预演、最后真推 |
| **团长排障** | `gzh.py token` | 一行判定「凭证 / 网络 / IP 白名单」哪一层坏了 |

---

## 二、子命令逐个说

### `gzh.py creds` — 凭证体检
只报键名和长度，**不打印密钥值**。

```
凭证文件: C:\Users\admin\.baoyu-skills\.env ✓ 存在
  WECHAT_APP_ID: 已设置，长度 18
  WECHAT_APP_SECRET: 已设置，长度 32
结论: ✓ 凭证齐备，可尝试 publish
```
凭证来源：`~/.baoyu-skills/.env` 优先，缺失时回落环境变量。

### `gzh.py token` — 换 access_token
真正打一次微信接口，能区分三种失败：

| errcode | 含义 | 怎么办 |
|---|---|---|
| 40164 | **IP 白名单**没加本机公网 IP | 公众号后台 → 设置与开发 → 基本配置 → IP 白名单，把报错里那个 IP 加进去 |
| 40013 | appid 无效 | 核对 `.env` 里是不是这个号 |
| 40125 | secret 无效 | 重置 secret 后更新 `.env` |

> 2026-11-05 实测：凭证有效、网络通，卡在 40164（本机公网 IP `117.151.76.207` 不在白名单）。**这是推草稿箱唯一的真实阻塞点。**

### `gzh.py check <img> [--ratio 2.35]` — 图片检查
```
尺寸: 1880 × 800
比例: 2.350:1（目标 2.35:1，偏差 0.0%）
体积: 514.8 KB
```
比例偏差 >2% → RC=2（封面会被公众号裁切）。超 2MB 只警告，上传时自动压成 JPEG。

### `gzh.py render <a.html> <b.png> --width W --height H`
Chrome `--headless=new` 截图，用临时 `--user-data-dir`，**不会和正在运行的 Chrome / Opera 抢单例锁**。
截图后自动读 PNG 头校验真实尺寸，和 `--width/--height` 不符会警告（说明 HTML 里设了固定宽高）。
`--transparent` 出透明底。

### `gzh.py risk <path...> [--json] [--ignore-words "中国,看多"]`
委托 `assets/publish/riskcheck.py`（内置词表 + `riskcheck_extra.json` 自定义）。

**必须理解语义**：`BLOCK` ≠ 文章违规，`BLOCK` = **必须人工裁定**。

财经稿里 `中国` 几乎每条都中（「中国经济周刊」「中国市场」「中国石油」），这是词表级误伤。处理方式：
- 判定为误伤 → `--ignore-words "中国"` 显式跳过，**不要为了过扫描去改文章措辞**
- 真踩线 → 按报告给的替换建议改

`--json` 时 stdout 只留纯 JSON，人类可读报告走 stderr，可直接 `| jq`。

RC：0 通过 / 2 有 BLOCK 待裁定。

### `gzh.py verify [--date YYYYMMDD] [--prev YYYYMMDD] [--out x.json]`
盘面数据多源核对，跑完输出 JSON + 口径对照。

**两套口径必须分清（这是最容易出错的地方）**：

| 数据 | 来源 | 说明 |
|---|---|---|
| 涨跌家数 | 东财全市场逐股 `f3` 扫描 | 4869 涨 / 624 跌 这类数字用它 |
| 涨跌停只数 | 东财 `getTopicZTPool` / `getTopicDTPool` 的 `tc` 字段 | 涨停 84 / 跌停 0 这类数字用它 |

同一天两套能差 1~3 只（2026-11-05 实测：逐股扫描跌 624 / 池口径跌停 0）。**稿子里只用一套并注明来源**，不要一句话里混两个口径。
脚本末尾会自动打印口径对照，看到不一致就说明该复核。

### `gzh.py publish --html --title --cover [--digest] [--dry-run]`
推公众号草稿箱。**只写 `draft/add`，不群发、不发布，发表键永远人工点。**

流程：读 HTML → 正文内本地图上传换 URL → 封面上传拿 `thumb_media_id` → `draft/add` → 回 media_id。

- `--dry-run`：只做本地校验（文件存在、标题 ≤64 字、图片数量），**不联网**。正式推之前先跑它。
- HTML 里含 `<h1>` 会警告：公众号会自动再加一次标题，建议用去掉刊头的粘贴版。
- 正文图按 HTML 里的**相对路径**找，相对于 HTML 所在目录。
- `--save-id` 把 media_id 写进同目录 `draft_id.txt`。
- `--no-article-type` 不传 `article_type` 字段（旧接口兼容，默认传 `news`）。

---

## 三、典型调用链

**S3 出图后自检**
```bash
gzh.py render 08-cover.html 08-cover.png --width 1880 --height 800
gzh.py check 08-cover.png --ratio 2.35
```

**S5 合规终检**
```bash
gzh.py risk 04-article-edited.md 07-video-script.md
gzh.py risk 04-article-edited.md --json 2>/dev/null | jq '.[] | select(.level=="BLOCK")'
```

**S3 出图前 / S6 发布（最后一步才真写）**
```bash
gzh.py account --live                       # 当前账号名与封面署名，跟微信后台核一次
gzh.py brand output/<本轮目录> --strict     # 扫旧账号名，命中即 RC=1
gzh.py creds
gzh.py publish --html 08-article-paste.html --title "标题" --cover 08-cover.png --dry-run
gzh.py publish --html 08-article-paste.html --title "标题" --cover 08-cover.png --digest "摘要" --save-id
```

**S1 拿当日数据**
```bash
gzh.py verify --date 20261105 --out output/20261105-xxx/verify.json
```

---

## 四、坑（已写进代码，但要知道为什么）

1. **死代理**：本机 `HTTP_PROXY` 指向 `127.0.0.1:1080`，拨号型客户端常常没起。`gzh.py` 和 `market_verify.py` 都 `install_opener(ProxyHandler({}))` 全局清空。新增出网脚本必须照做，否则 502 / 超时。
2. **Chrome 单例**：本机常有 Opera 占着 9222 和固定 profile。`render` 用临时 `--user-data-dir` 绕开。
3. **标题长度**：公众号上限 64 字，`publish` 先卡。视频号标题是 22 字，那条规则在 S4。
4. **封面比例**：2.35:1 是公众号横版封面，`pic_crop` 裁剪靠 `thumb_media_id` 原图，所以封面图本身就得是 2.35:1，别指望接口裁。
5. **别自己实现发布**：`wenyan-cli` 需要额外装、凭证路径是 macOS 的、`publish.sh` 还会自动全局装包。这套 `gzh.py publish` 已经跑通到只剩 IP 白名单，没有理由再绕。
6. **微信只认内联 `style=""`**：`draft/add` 会整体剥掉 `<style>` 代码块和 `class` 选择器。S3 产出的排版 HTML 若用 `<style>`+class（含 `baoyu-markdown-to-html` 的默认产物），进草稿箱后会变成全黑无分隔。**修复**：`publish` 现在发送前自动把 `<style>`/class 内联成 `style=""`（颜色/边框/底色/分隔线可在微信存活）；已是内联或无 `<style>` 的 HTML 自动跳过，零副作用。多列布局请直接用 `<table>`，`display:flex`/`border-radius` 即便内联微信也会丢。
7. **正文图表别用栅格 PNG**：微信会对图片二次压缩，手机上栅格图里的文字必糊。承载精确数字 / 板块名的数据图表，一律写成文章内联 HTML（表格 / 条形 div），文字是 DOM 永不糊；只有装饰性封面 / 配图才用 PNG。
8. **封面色与裁切**：封面 PNG 带文字，微信二次压成 JPEG，且订阅流/分享卡取中心 1:1 方块。主标题必须用**高对比白字**，金色只当强调色（不当主标题色，否则压缩后发糊）；文字**居中落在中心安全区**，左对齐会被 1:1 裁切切掉左端。出图后务必模拟「~900 宽 JPEG q70 缩略 + 1:1 中心裁切」两版各看一眼再推。
9. **重推会堆一箱旧草稿**：`draft/add` 只新增不覆盖，迭代修稿每推一次多一条，用户在草稿箱看到一堆历史版本（旧封面、糊栅格插图、被 1:1 切掉标题的旧封面），会被误判成「图有很多问题」。**修复**：`publish` 推送前自动 `draft/batchget` + `draft/delete` 清掉同 `title` 旧草稿（`--keep-old` 可关闭）；交付前用 `draft/count` 确认只剩 1 条。审查草稿箱真实图片必须走 `draft/batchget` → `material/get_material` 下载封面 → 按 375×160 / 300×300 真机尺寸看，**不要只审本地文件**。
10. **`render` 移动端预览会假裁切**：本机 headless Chrome 无视 viewport meta，流动排版页默认按 980px 布局、再用 `--width` 截图会把右侧裁掉，看起来像「数据卡缺一列 / 正文行末切字」，其实真机不溢出。**修复**：`render` 对无固定宽度的页面自动注入 `html,body{width:目标宽}` 强制视口（固定画布的封面页跳过）。核对真机务必用 `--width 375`，别用 680 自嗨。
    - **2026-11-09 补丁（片段形态）**：公众号正文常是「只有一个 `<div>`、没有 `<html>/<body>/<head>`」的 HTML 片段，旧版注入靠 `replace("</head>", …)`，片段里没有 `</head>` 会**静默失效**，于是又变回 980px 布局 → 375 截图每行切字、表格右列整个看不见，极易被误判成「图块配色/字号问题」。现在 `render` 检测到无 `</head>` 会把样式**前置拼在片段开头**，Chrome 补全 html/body 后同样生效。判断标准：预览里若中文长句在行末被硬切、下一行接不上，先怀疑这里，别去改字号或配色。
11. **正文图块的「配色问题」不是字号问题**：用户说「内容里的图看不清、配色有问题」且封面正常时，指的是内联 HTML 数据卡 / 条形图。常见三宗罪：① 深蓝底 + 荧光红绿字（发闷，且背景一旦被编辑器改动就白底白字）；② 暗红 `#E0533D` / 暗绿 `#2F8F5B` 压米灰槽（脏、辨识度低）；③ 金色小字、13px 灰蓝小字（对比不足）。**修法**：数据卡改白底深字，数字用 `#C62828`/`#0E7A45`，条形用 `#E03127`/`#159A5B` + `#EDE9E0` 浅槽、高 ≥14px，小字 ≥14px 深色；同时清掉 `display:flex` / `border-radius` / `background` 简写。改完必须 `draft/batchget` 拉服务端 HTML 核对新色值已进箱，并 `draft/count` 确认只剩 1 条。
12. **账号改名后，图上的署名不会自己跟着变**：2026-11-09 用户「这个账号已经换名了，图片上相关的字也要跟着改」——`cover.html` 里署名是写死的，账号在后台改名不会通知出图环节，S3 沿用模板就把旧名一路印进草稿箱。根因是**账号名属于配置而非产出**。**修复**：新增 `config/account.md` 作唯一真源（`account_name` / `pen_name` / `cover_byline` / `old_names`），`gzh.py account --live` 调 `account/getaccountbasicinfo` 实时核微信后台昵称；`gzh.py brand <路径> --strict` 扫旧名；`publish` 推送前自动扫 `cover.html` + 正文 HTML，命中旧名直接拦下（`--allow-old-brand` 仅历史稿重推用）。
    - `brand` 扫的是**源码**，PNG 里的字扫不出来 → 封面必须由 HTML 渲染，禁止直接拿旧 PNG 改字。复盘 / 规范 / 合规报告里引用旧名只是「说明」，`brand` 默认跳过这类文档（`--include-docs` 可强制全扫审计），避免把写对了的文章记录误判成没改名。
    - 改名 SOP：改 account.md（旧名追加进 `old_names`，别删）→ 扫全包 → 重渲染所有含署名图并重出 900 宽 / 1:1 版 → 重推草稿（默认自动清同标题旧稿）→ `material/get_material` 回拉封面确认服务端已换新图。
