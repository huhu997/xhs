# 路径与资产归属（唯一权威表）

> 本专家团的**全部能力资产自包含在包内**。所有文档、角色 prompt、脚本引用一律以本表为准，不再散落到 `F:/桌面/zcode工作区/` 或 `F:/桌面/Gemini本地文件/`。

## 一、两个包根（内容必须一致）

| 用途 | 路径 |
|---|---|
| **源包**（编辑 / 维护 / 注册用） | `F:/Cache/.workbuddy/plugins/marketplaces/my-experts/plugins/gzh-content-ops` |
| **运行缓存**（会话实际加载） | `C:/Users/admin/.workbuddy/plugins/cache/my-experts/gzh-content-ops/2.0.0` |

解析规则：命令里先定义 `EXPERT_DIR`，再拼子路径。
- 编辑、注册、校验 → `EXPERT_DIR` 指向**源包**
- 会话运行时读文件 → `EXPERT_DIR` 指向**运行缓存**
- 两处 `assets/`、`config/`、`skills/`、`team/`、`output/` 内容必须保持一致；**改了源包必须同步缓存**，否则运行时读不到（历史上已漏过一次 `agushi-hongxian.md`）。

## 二、包内资产（2026-11-05 第三轮：脚本工具化）

> 详细说明见 `${EXPERT_DIR}/assets/README.md`。下表是速查。

### ★ 首选入口：工具库 `assets/tools/`

**凡是要执行机械动作，先查这里，不要自己写临时脚本、不要去 legacy 里翻。**

| 工具 | 命令 | 谁用 | 替代了什么 |
|---|---|---|---|
| `tools/gzh.py` | `creds` / `token` | 团长排障 | 手工查 .env |
| | `check <img> --ratio` | **S3** | `check_cover.py` |
| | `render <html> <png>` | **S3** | 手工调 Chrome |
| | `risk <path> [--json]` | **S5** | `audit_risk.py` |
| | `publish --html --title --cover` | **S6** | `upload_article.py` / `upload_preview.py` / `news_publish.publish()` |
| | `verify --date` | **S1 / 团长** | `verify_data.py` |
| `tools/market_verify.py` | 独立跑盘面核对 | S1 | 同上（被 vefiry 子命令调用） |
| `tools/README.md` | 用法与坑 | 全员 | — |

用法全文见 `${EXPERT_DIR}/assets/tools/README.md`。

### 其余资产

| 资产块 | 包内路径 | 来源 | 谁用 |
|---|---|---|---|
| **发布与风控库**（13 文件） | `${EXPERT_DIR}/assets/publish/` | `zcode工作区/_wx_read/` | **S6 / S5**（经 `gzh.py` 调用） |
| ├ `news_publish.py` | 同上 | 264 行，`load_creds()`/`get_token()`/`upload_img()`/`cover_A,B,C` 三款封面 | `gzh.py` 复用其实现 |
| ├ `riskcheck.py` + `riskcheck_extra.json` | 同上 | 23KB 风控扫描器 + 自定义词表 | `gzh.py risk` |
| └ 其余 11 个 | 同上 | `run_daily.py` / `generate.py` / `cover_variants.py` / `delete_drafts.py` / `freepublish.py` / `extract.py` / `fetch_news.py` / `fetch_us.py` / 2 个 test | S1/S3/S6/S7 |
| **写作工作台**（30 文件） | `${EXPERT_DIR}/assets/writer-app/` | `03_内容运营/公众号运营/wechat-writer/` | **S1 / S2** |
| ├ `workflow/` | 同上 | `topic.py`（选题）→ `outline.py`（大纲）→ `writing.py`（正文）→ `quality.py`（质检） | S1 / 团长 |
| ├ `tools/de_ai.py` | 同上 | 去 AI 味实现 | **S2** |
| ├ `tools/formatter.py` `image_gen.py` `web_fetcher.py` | 同上 | 排版 / 生图 / 抓取 | S3 / S1 |
| ├ `souls/` `memory/` | 同上 | 人设 soul + 长期记忆 + 写作规则 | S2 / S4 |
| └ 剔除项 | — | `.env`（真实 key）/ `archives/` / `*.log` 已删，只留 `.env.example` | — |
| **归藏排版工具** | `${EXPERT_DIR}/assets/typeset/server.py` | `公众号运营/归藏排版工具/` | **S3** |
| **历史脚本存档**（11 个，**勿直接跑**） | `${EXPERT_DIR}/assets/scripts/legacy/` | `articles/` 30+ 目录去重 | 只作参考；替代关系见其 `README.md` |
| Gemini 零积分生图脚本 | `${EXPERT_DIR}/assets/scripts/gemini-gen.mjs` | 自建 `article-tools/server/gemini-gen.mjs` | **S3** |
| 排版模板脚本 | `${EXPERT_DIR}/assets/templates/build_preview.py` | 历史最大版本 | 参考 |
| **策略与人设文档** | `${EXPERT_DIR}/assets/docs/` | `公众号项目/` + `articles/草稿记录.md` | 团长 / S4 |
| ├ `股票公众号系列_内容策略.md` `视频号矩阵引流公众号_全案策划.md` | 同上 | 内容策略 + 视频号引流全案 | 团长 / **S4** |
| ├ `公众号写作技能_完整版.md` | 同上 | 写作 skill 说明（刘润风格结构） | 团长 |
| └ `发布台账-草稿记录.md` | 同上 | **历史发布台账**，S6 发布后追加、S7 复盘取值 | S6 / S7 |
| **长盈客栈 IP 人设** | `${EXPERT_DIR}/assets/ip/` | `03_内容运营/` | S2 / S3 / S4 |
| ├ `长盈客栈角色卡.md` `人物设计探讨.md` `连环画设定.md` | 同上 | 人设核心设定 | **S2 语气校准 / S4 出镜人设** |
| └ `长盈客栈IP全景思维导图.html` | 同上 | IP 全景 | 团长 |
| **配色体系实物** | `${EXPERT_DIR}/assets/palette/` | `articles/_配色预览/` | **S3** |
| ├ `工厂样图/cover.yaml` `data.yaml` `gallery.html` | 同上 | 工厂式配色配置 + 样图 gallery | S3 与 `themes.md` 对照 |
| └ `文章配色/gallery.html` `image-prompts.md` | 同上 | 文章配色 gallery + 配图 prompt 库 | S3 |
| 自建工作流原文 | `${EXPERT_DIR}/assets/workflow/公众号文章创作工作流-原文.md` | `03_内容运营/公众号文章创作工作流.md` | 团长（方法层来源） |
| 方法规范（7 份） | `${EXPERT_DIR}/skills/gzh-workflow/references/*.md` | 自建工作流经验提炼 | 全员 |
| 团队编排与 7 角色 | `${EXPERT_DIR}/team/` | 专家团本体 | 全员 |

> 原位置文件**保留不动**（其他项目可能仍在引用），包内是权威副本。以后改脚本只改包内这份。
> `assets/` 总计约 600KB。

## 三、运行时数据（不是资产，不随包走）

这些是登录态 / 缓存 / 系统级安装，放进包里反而会被同步或失效，故只登记路径，不收编：

| 项 | 路径 | 说明 |
|---|---|---|
| Opera 可执行文件 | `F:/Programs 应用程序/O浏览器/opera.exe` | 系统安装，非包资产 |
| Opera 用户数据 | `F:/桌面/zcode工作区/.gemini-opera-profile` | 含 Google 登录态，**勿复制、勿进包** |
| Gemini Cookie 缓存 | `%APPDATA%/baoyu-skills/gemini-web/cookies.json` | 脚本自动读写 |
| bun 可执行文件 | `C:/Users/admin/.bun/bin/bun.exe` | **不在 PATH**，命令必须用绝对路径 |
| 代理 | `http://127.0.0.1:1080`（Linsoc） | 拨号型客户端，需在托盘点连接 |
| **公众号凭证** | `C:/Users/admin/.baoyu-skills/.env` | 键 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`；`news_publish.py:load_creds()` 直接读它。**勿复制进包、勿打印值** |

出网前必做 `unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy`，否则脚本跳过代理探测、误用沙箱 2233 出口。

## 四、产出归属（本轮补齐）

**专家团所有产出统一落 `${EXPERT_DIR}/output/YYYYMMDD-<slug>/`，不再落到 `zcode工作区/articles/`。**

- 本轮完整流程产出已归档：`${EXPERT_DIR}/output/20261105-fullrun/`（00–12 全部留痕 + 总表 + 封面/插图/HTML）
- 旧产出（`zcode工作区/articles/` 下 `20261007-liangbenzhang`、`20261008-duizhang`、`20261105-index-flat` 等）属**历史归档**，只登记不搬迁，避免破坏旧引用；如需调阅按原路径。
- 源包与运行缓存的 `output/` 同样需要同步。

## 五、标准命令模板

**先看这两组，99% 的机械动作都在里面：**

```bash
EXPERT_DIR="F:/Cache/.workbuddy/plugins/marketplaces/my-experts/plugins/gzh-content-ops"
GZH="python $EXPERT_DIR/assets/tools/gzh.py"

$GZH creds                                                    # 凭证体检
$GZH token                                                    # 连通性（40164=IP白名单）
$GZH verify --date 20261105 --out $EXPERT_DIR/output/x/verify.json   # 盘面核对
$GZH render a.html a.png --width 1880 --height 800            # HTML→PNG
$GZH check a.png --ratio 2.35                                 # 封面比例
$GZH risk 04.md 07.md                                         # 合规扫描
$GZH publish --html paste.html --title "标题" --cover c.png --dry-run
```

**Gemini 零积分生图（S3）**：

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
BUN="C:/Users/admin/.bun/bin/bun.exe"
GEMINI="$EXPERT_DIR/assets/scripts/gemini-gen.mjs"

"$BUN" "$GEMINI" --status
"$BUN" "$GEMINI" --login
"$BUN" "$GEMINI" -p "<prompt>" -i "$EXPERT_DIR/output/<YYYYMMDD-slug>/cover.png"
```

（脚本调用必须带 `timeout`，它有输出后不肯自行退出的毛病。）

## 六、同步命令（改完源包必跑）

```bash
P="F:/Cache/.workbuddy/plugins/marketplaces/my-experts/plugins/gzh-content-ops"
C="C:/Users/admin/.workbuddy/plugins/cache/my-experts/gzh-content-ops/2.0.0"
mkdir -p "$C/assets" "$C/config" "$C/output" "$C/avatars" "$C/skills/gzh-workflow/references" "$C/team/roles" "$C/agents" "$C/.codebuddy-plugin"
cp -r "$P/assets/." "$C/assets/"
cp -r "$P/config/." "$C/config/"
cp -r "$P/output/." "$C/output/"
cp -r "$P/avatars/." "$C/avatars/"
cp -r "$P/skills/gzh-workflow/references/." "$C/skills/gzh-workflow/references/"
cp "$P/skills/gzh-workflow/SKILL.md" "$C/skills/gzh-workflow/SKILL.md"
cp "$P"/team/roles/*.md "$C/team/roles/"
cp "$P/team/TEAM.md" "$P/team/ORCHESTRATOR.md" "$C/team/"
cp "$P/agents/gzh-content-ops.md" "$C/agents/"
cp "$P/.codebuddy-plugin/plugin.json" "$C/.codebuddy-plugin/"
cp "$P/README.md" "$C/README.md"
```

> ⚠️ **2026-11-07 实测漏同步**：连续数轮只改源包没跑本命令，缓存里 `visual.md` / `assets/tools/README.md` / `SKILL.md` / `gzh.py` / `publisher.md` 全是旧版——下次会话读的是缓存，等于白改。**改配置≠生效，同步+校验才算完。**

## 七、同步后校验（防漏，每次必跑）

```bash
P="F:/Cache/.workbuddy/plugins/marketplaces/my-experts/plugins/gzh-content-ops"
C="C:/Users/admin/.workbuddy/plugins/cache/my-experts/gzh-content-ops/2.0.0"
for f in \
  skills/gzh-workflow/references/themes.md \
  skills/gzh-workflow/references/cover-spec.md \
  skills/gzh-workflow/references/ai-taste.md \
  skills/gzh-workflow/references/zhangli.md \
  skills/gzh-workflow/SKILL.md \
  team/roles/visual.md team/roles/publisher.md team/roles/editor.md team/roles/scout.md team/TEAM.md team/ORCHESTRATOR.md \
  assets/tools/gzh.py assets/tools/README.md \
  agents/gzh-content-ops.md config/paths.md config/account.md README.md; do
  cmp -s "$P/$f" "$C/$f" || echo "❌ 未同步: $f"
done
echo "校验完成（上方无 ❌ 即全部一致）"
```

> 新增了 references 文件、配置或角色 prompt 时，把路径一并加进上面的清单；`assets/`、`skills/`、`team/roles/` 整目录同步可用 `diff -rq "$P/assets" "$C/assets"` 兜底。
> `config/account.md`（账号名/封面署名唯一真源）也在清单里：`gzh.py account` / `brand` / `publish` 都读它，漏同步会导致会话里跑的还是旧账号名。
