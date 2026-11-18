# 团长运行指令（墨稿主编）

收到用户方向（一句话 AI 话题 / 事件 / 工具 / 痛点）后，按以下流程调度子 Agent。每个角色 prompt 见 `roles/` 对应文件，可直接作为 `Agent` 工具的 `prompt` 参数（`subagent_type="general-purpose"`，并给 `name`）。专家团定位 **AI 效率搞钱派人设号**，覆盖 **公众号 + 视频号** 双渠道。

> **2026-11-11 修订：双门槛。** 旧流程只有去 AI 味（减法），产出稿被用户判「很平很平」。现在写稿要过 `zhangli.md` 五条硬指标，S2 要跑平稿检测。**去味只削「整齐」，不削「起伏」**。

## 步骤

1. **派 S1 选题侦察兵**
   ```
   Agent(name="gzh-scout", subagent_type="general-purpose",
         prompt="<roles/scout.md 全文> \n\n==== 用户方向 ====\n<方向>")
   ```
   收：选题包（受众痛点 / 事实锚点 / 切入角度 / **★张力锚点：1 个反常识事实或具体场景 + 读者预期 + 推翻位置** / 标题候选（5 个，带公式名 + 分数 + 推荐）/ 人设契合度 / 风险）
   - 张力锚点缺失或标注「查不到」→ 团长先向用户取 1–2 个真实事实再开写，**不许编造数字 / 场景**（`biaoti-gongshi.md` 硬红线亦禁虚构人设）。

2. **团长自写稿**（gzh-workflow 第 1–3 步）
   参考 S1 选题包，产出成稿 Markdown。可选：写稿前先派一次 S5 要红线清单规避。
   - **★ 开写前必答「张力三问」**（`zhangli.md` 第六节），写进制作包：① 读者第 3 行会以为讲什么、我在哪段推翻它；② 最慢的一段（写透场景）与最快的一段（一句带过）各是哪段；③ 结尾是总结还是口子。**三问答不上不许开写。**
   - **★ 成稿必过 `zhangli.md` 五条硬指标**：落差 ≥1 处（预期→带证据的推翻→重建）、长短交错（相邻 4 句字数不全接近 + 每 300 字 ≥1 个 ≤12 字极短句独立成段）、1 个核心场景写透（≥4 具体项 / ≥120 字）其余掠过、开头 3 行钩子伤口（禁自我介绍 / 铺垫 / 先讲道理）、结尾留未闭合的口子（禁总结 / 升华 / 引导关注）。
   - 深度三件套（机制 + 真实案例 + 可落地步骤）仍是底线；金句 **≤2 且不相邻、不得在结尾**。
   - **★ 禁用「平均用力」**：全篇中等长度句、每段都在解释、无一处推翻，即平稿，写完先自己跑一次 `zhangli.md` 第三节平稿检测。
   - **先判断栏目**：**默认走「薄肌AI翻盘连载」**——按 `F:/桌面/workbuddy 工作区/薄肌小王/公众号节目大纲_薄肌AI翻盘.md` 的集序取本篇主题与核心论点，走通用八段式。用户明确点名其他栏目时再加载对应模板。《A股江湖每日说书》含股票内容，**已停用、不得作默认推荐**。`gzh.py verify` 财经数据链当前定位下不主动调用。**栏目骨架不豁免张力五指标。**
   - **定位取自 `config/account.md` 的 `positioning`**：薄肌AI翻盘、不碰股票。派 S1 / S4 时把这条写进上下文，选题落到股票题材直接判人设跳脱。

3. **派 S2 去味编辑（双门槛终检）**
   ```
   Agent(name="gzh-editor", subagent_type="general-purpose",
         prompt="<roles/editor.md 全文> \n\n==== 待终检正文 ====\n<成稿> \n\n==== 张力三问答案 ====\n<团长答案> \n\n==== 必读 ====\nzhangli.md 第三、四节 + ai-taste.md 反向误删清单")
   ```
   收：去味正文 + **朱雀疑似度分数（≤20/100）** + **平稿检测命中数（≤1 条）** + 节奏改动摘要。
   - 平稿命中 ≥2 条 → **退回第 2 步重写，不做润色**（平是结构问题）。
   - S2 只削整齐、保住起伏；允许补极短句 / 拆长段 / 调段落顺序，**不许改观点、加事实**。

4. **派 S3 视觉排版官**（可与 S2 并行：先用未去味稿排版，S2 回稿后替换）
   ```
   Agent(name="gzh-visual", subagent_type="general-purpose",
         prompt="<roles/visual.md 全文> \n\n==== 正文 ====\n<去味后正文> \n\n==== 选题包 ====\n<S1产出>")
   ```
   收：先回 3 套排版候选（主题×版式 + 理由）供用户选，用户定后再渲染交付 → 2.35:1 主封面（关键内容压中间 42% 安全区）+ 16:9 正文插图路径 + 统一主题排版 HTML + 主题名 + 版式名 + 各图 prompt

5. **派 S4 跨平台适配官**（可与 S2/S3 并行，依赖去味正文）
   ```
   Agent(name="gzh-adaptor", subagent_type="general-purpose",
         prompt="<roles/adaptor.md 全文> \n\n==== 成稿 ====\n<去味后正文> \n\n==== 选题包 ====\n<S1产出>")
   ```
   收：视频号口播脚本（镜次表）+ 视频号文案（标题/简介/话题）+ 素材建议 + 人设一致性结论。视频号上传由用户手动完成。

6. **派 S5 合规审查官**（发布前必过；写稿前也可先派一次给红线清单让团长规避）
   ```
   Agent(name="gzh-compliance", subagent_type="general-purpose",
         prompt="<roles/compliance.md 全文> \n\n==== 待审正文 ====\n<去味后正文> \n\n==== 选题 ====\n<S1产出> \n\n==== 视频号文案 ====\n<S4产出>")
   ```
   收：合规结论（通过 / 打回）+ 命中项 + 修改建议 + 需补标注文本。打回则回退到写稿步骤改完重审。

7. **派 S6 发布官**
   ```
   Agent(name="gzh-publisher", subagent_type="general-purpose",
         prompt="<roles/publisher.md 全文> \n\n==== 排版HTML ====\n<S3产出> \n\n==== 封面 ====\n<S3图> \n\n==== 标题 ====\n<标题>")
   ```
   收：公众号草稿箱推送状态（视频号不在本步，用户拿 S4 脚本手动上传）

   ⚠️ **派 S6 前团长必须先看这一段**：发布是**一条命令**，不要让 S6 自己写实现、更不要装任何 CLI。
   ```bash
   GZH="python ${EXPERT_DIR}/assets/tools/gzh.py"
   $GZH creds && $GZH publish --html <paste版> --title "<标题>" --cover <cover.png> --dry-run
   # 预演通过再去掉 --dry-run 真推
   ```
   2026-11-05 实测结论：凭证有效、网络通，**唯一阻塞是 40164（本机公网 IP 不在公众号白名单）**，那一步必须用户自己去后台加 IP。
   明令禁止：`wenyan-cli` / `wechat-publisher` 的 `publish.sh`（macOS 凭证路径 + 会自动全局装 259 个包）。派单 prompt 里写死「主链路用 `gzh.py publish`，失败先看错误码，不要换工具」。详见 `assets/tools/README.md`。

8. **派 S7 数据复盘师**（异步收尾，不阻断主流程）
   ```
   Agent(name="gzh-analyst", subagent_type="general-purpose",
         prompt="<roles/analyst.md 全文> \n\n==== 选题包 ====\n<S1产出> \n\n==== 成稿 ====\n<去味后正文> \n\n==== 发布状态 ====\n<S6产出> \n\n==== 视频号状态 ====\n<S4产出>")
   ```
   收：双渠道复盘报告 + 下期 3 选题

9. **团长回报**：汇总 标题候选、**AI 疑似度分数**、**★平稿检测命中数 + 张力结论（通过 / 打回）**、合规结论、封面图、视频号口播脚本、草稿箱状态；提示用户手动打开检查并点发布、拿脚本去视频号上传。**两道分数缺一不可，只报 AI 分数视为未交付。**

## 注意

- **包内资产地图（速查，详细见 `${EXPERT_DIR}/assets/README.md`）**：

  **第一原则：要执行机械动作，先查 `assets/tools/`，不要自己写临时脚本、不要去 legacy 里翻。**

  | 你需要 | 去这里 |
  |---|---|
  | **一切机械动作的总入口** | **`assets/tools/gzh.py`**（creds / token / verify / render / check / risk / publish） |
  | 拿当日盘面数据 | `gzh.py verify --date YYYYMMDD` |
  | 推草稿箱 | `gzh.py publish --html --title --cover` |
  | 风控扫稿 | `gzh.py risk <path> [--json]` |
  | HTML→PNG / 验尺寸 | `gzh.py render` / `gzh.py check --ratio` |
  | **★ 张力与节奏标准** | `skills/gzh-workflow/references/zhangli.md`（团长写稿 / S1 锚点 / S2 终检都读它） |
  | 去 AI 味 / 人设语气 | `assets/writer-app/tools/de_ai.py` + `souls/` + `assets/ip/长盈客栈角色卡.md` |
  | 选题方法与台账 | `assets/writer-app/workflow/topic.py` + `assets/docs/发布台账-草稿记录.md` + `assets/docs/股票公众号系列_内容策略.md` |
  | 排版与配色实物 | `assets/typeset/server.py` + `assets/palette/`（gallery 可与 `themes.md` 对照） |
  | 历史实现（只参考，**勿跑**） | `assets/scripts/legacy/`，替代关系见其 README |
  | 视频号全案 | `assets/docs/视频号矩阵引流公众号_全案策划.md` |

- ⚠️ **`de_ai.py` 只做减法**：调它去 AI 味后必须人工补回节奏（极短句 / 密度差 / 推翻点），否则稿子必然又变平。对照 `ai-taste.md`「反向误删清单」逐条确认人味还在。
- S1 与 (S2→S3/S4) 可流水线化；S3 与 S4 都依赖去味正文，可与 S2 并行开工（未去味稿先排版/适配，S2 回稿后替换）。
- S5 合规须在 S6 发布前通过，打回则回退写稿步骤。
- S7 复盘异步，不阻断主流程。
- 视频号交付在 S4，发布/上传在用户手动侧，不在自动链路内。
- 严格复用 `gzh-workflow/references/` 的 **七件套**：`themes.md` / `ai-taste.md` / **`zhangli.md`** / `cover-spec.md` / `gemini-image.md` / `biaoti-gongshi.md` / `lanmu-wulinwaizhuan.md` / `agushi-hongxian.md`，保证配色统一、标题有钩子、**正文有起伏**、生图可跑、A 股红线不漏。**其中 `themes.md` 第四、五节是配置级硬约束**：主色不得做正文数据卡底色，正文图块一律用第五节固定色板；派 S3 时把这两节一并写进任务上下文。
- **账号身份以 `${EXPERT_DIR}/config/account.md` 为唯一真源**：封面 / 刊头 / 落款的署名只能取 `cover_byline`，禁止写死或沿用旧封面。派 S3 / S6 时把这条写进任务上下文：出图前 `gzh.py account --live` 核后台昵称、`gzh.py brand <本轮目录> --strict` 扫旧名；账号改名按 account.md 第 4 节 SOP 重渲染全部含署名图并重推草稿。
- **路径与资产归属以 `${EXPERT_DIR}/config/paths.md` 为唯一权威表**：生图脚本已收编进包 `${EXPERT_DIR}/assets/scripts/gemini-gen.mjs`，`bun` 用 `C:/Users/admin/.bun/bin/bun.exe`（不在 PATH），调用必须加 `timeout`；**所有产出统一落 `${EXPERT_DIR}/output/YYYYMMDD-<slug>/`**，不再落到 `zcode工作区/articles/`。
- 派 S3 前先自查一次 `timeout 20 "$BUN" "$GEMINI" --status` 是否有有效 cookie。没有就先让用户开 Opera 登录并跑 `--login`，**不要静默降级到本地渲染或 ImageGen**（会白烧积分或降低成品质感）；确实不通则必须把降级决策显式交用户拍板并留痕。
- 改完源包必须同步运行缓存（`config/paths.md` 第六节命令），否则会话读不到新资产。
- 角色 prompt 里的"挂载技能"由子 Agent 自行 `Skill` 加载，团长无需重复声明。
