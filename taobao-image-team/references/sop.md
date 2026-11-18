# 淘宝上架图交付专家团 · 完整 SOP

> 本 SOP 由「淘宝上架图交付专家团」执行，融合了你之前淘宝半工作流的全部生产级能力（系统 Chrome CDP 渲染、2026 规格、切片、合规、千牛上架、交付 SOP）与本地的参数化快速出图流水线。
> 执行引擎：`skills/taobao-image-workflow/`（4 类 HTML 模板 + fill_template.py + render_all.mjs + slice_images.py + stitch_long_image.py + gen_product.py / gen_product_web.py 网页端生图 + run_all.py 一键 + 8 大品类预设）。

---

## 〇、三大使用模式（开局先定）

| 模式 | 触发语 | 差异 |
|---|---|---|
| **A. 自用** | "我自己要做图" | 跳过报价/合同，Phase 1 直接进，出图入库 |
| **B. 接单代做** | "接个单/客户商品/代做" | Phase 0 先走《接单需求单》+ 报价，交付走云盘+交付SOP，收钱 |
| **C. 卖铲子** | "打包卖/技能包/去署名" | 全流程跑通后进入打包子流程，产出可售卖 skill 包（去署名+说明页+zip） |

---

## 一、团队角色与分工

| 角色 | 花名 | Agent ID | 负责 |
|---|---|---|---|
| 主理人 / 交付操盘手 | 范成单 | taobao-image-team-team-lead | 建团、调度、进度通报、最终汇编 |
| 接单拆解师 | 许析单 | intake-analyst | 接单拆解、品类参数化、产出 order.json |
| 卖点文案师 | 文点睛 | copywriter | 卖点提炼、上架标题/关键词/详情文案 |
| 视觉风格师 | 展图新 | visual-designer | 模板选型、风格锁、画廊规划 |
| 渲染执行师 | 柯出图 | render-engineer | 跑脚本出图：fill→render→slice→（视频） |
| 合规交付师 | 严达标 | qa-delivery | QA、切片校验、合规扫描、拼长图、上架表单、交付SOP |

---

## 二、标准交付流程（6 个 Phase，串行接力）

### Phase 0 · 建团 + 模式判定（主理人）
- 主理人 **TeamCreate** 建立团队。
- 判定模式 A / B / C。
- 模式 B：先由 `intake-analyst` 走《接单需求单》→ `visual-designer`+`copywriter` 给报价（参考 `references/pricing.md`）。
- 产物：模式确认 +（B 模式）报价单。

### Phase 1 · 需求拆解 → order.json（许析单 / intake-analyst）
- 把商品/客户资料拆成结构化订单参数：品类、卖点、价格、规格、平台、风格偏好、数量、截止时间。
- 套用 `references/intake-form.md`，缺关键信息只追问 3 项。
- 产出：`order.json`（**照抄 `references/categories.md` 的真实 schema 片段**，或改 `examples/order_example_*.json`；真实字段见本文附录）。
- 回传主理人 → Phase 2。

### Phase 2 · 卖点文案（文点睛 / copywriter）
- 基于 order.json 提炼 3-5 卖点金句 + 上架标题（≤30字）+ 搜索关键词（8-12）+ 详情分段文案。
- 规则：主图文案 ≤14 字/条，标题零极限词，虚拟品强调"网盘秒发/永久更新/即买即用"。
- 回填 order.json 的 `points / sub / foot / detail[] / guide[]`；上架标题与关键词另出《上架表单.md》。
- 回传主理人 → Phase 3。

### Phase 3 · 视觉设计与风格锁（展图新 / visual-designer）
- 按品类从 8 大预设选基调（深蓝科技风 / 橙红电商风 / Apple 简约风 / 食品暖色风 等）。
- 锁定风格系统（主色/辅助色/字体层级/圆角/留白）+ 画廊规划（主图/导购/白底/详情各几张）。
- 参考 `references/template-library/` 的 S1 爆款样例。
- 输出《风格锁定说明.md》（order.json 无 style/gallery 字段；换配色改 `template_*.html` 的 CSS 变量）。
- 回传主理人 → Phase 4。

### Phase 4 · 本地出图（柯出图 / render-engineer）
执行 `taobao-image-workflow` 流水线：
```bash
cd <team>/skills/taobao-image-workflow
python scripts/fill_template.py <order.json> --out <outDir>
"C:/Program Files/nodejs/node.exe" scripts/render_all.mjs <outDir>
python scripts/slice_images.py --root <outDir>
# 可选：python ../../hyperframes/make_video.py  <outDir>   # 主图视频
# 一键：python scripts/run_all.py <order.json> --out <outDir>    # 串起以上全部
# 加 --web：先走网页端自动生图（无需 API key，首次登录一次）
```
- 产出规格（2026 淘宝）：
  - 主图 `1440×1440`（白底/场景）
  - 3:4 导购图 `1440×1920` × N 张
  - 白底图 `800×800`
  - 详情长图 `1440` 宽，按段切 2-4 张（单张高/宽 ≤ 2）
- 异常显式报告（哪张没出、是否中文糊字），不藏着。
- 回传主理人 → Phase 5。

### Phase 5 · 质检与交付（严达标 / qa-delivery）
- **QA 清单**：主体不变形、中文无糊字乱码、规格达标、风格一致、图位齐全。
- **合规扫描**：极限词/违禁词/版权，对照 `references/compliance-check.md`。
- **长图合成**：`stitch_long_image.py --width 1440` 拼 1440 宽详情长图。
- **交付物生成**：上架表单（标题/关键词/价格/类目）+ 交付 SOP（含自动发货话术）+ 合规报告。
- 交付包结构：`主图/ 导购图/ 白底图/ 详情图/ 长图/ 上架表单.md 交付SOP.md 合规报告.md`。
- 回传主理人 → Phase 6。

### Phase 6 · 主理人汇编交付
- A 自用：入库 `电商图服务方案/demo/<SKU>/`
- B 接单：云盘链接 + 交付 SOP 发给客户，触发 1 次免费小改
- C 卖铲子：去署名 + 写售卖说明 + 产出可分享 zip（参考 package_expert 思路）

---

## 三、执行引擎命令速查（render-engineer 用）

| 步骤 | 命令 | 说明 |
|---|---|---|
| 填模板 | `python fill_template.py order.json --out out/` | 生成主图/详情/导购/白底 4 类 HTML |
| 渲染 | `"C:/Program Files/nodejs/node.exe" render_all.mjs out/` | 系统 Chrome CDP 截图成 PNG |
| 切片 | `python slice_images.py --root out/` | 详情长图按段切 2-4 张 |
| 拼长图 | `python stitch_long_image.py 详情图_*.png --width 1440 --out 长图.jpg` | 拼 1440 宽长图 |
| 一键全套 | `python run_all.py order.json --out out/` | 串起 fill→render→slice，加 `--web` 先生图 |
| 生图 prompt | `python gen_product.py order.json --out out/` | 输出标准 prompt + 落盘路径 |
| 网页端生图 | `python gen_product_web.py order.json --out out/` | 自动贴 prompt/生成/抓图/落盘；`--probe` 自检 |
| 视频(可选) | `python ../../hyperframes/make_video.py out/` | 主图视频 |

环境依赖：系统 Chrome `C:/Program Files/Google/Chrome/Application/chrome.exe`（脚本自动探测）；node 用系统版 `C:/Program Files/nodejs/node.exe`；Pillow 需已装（`pip install pillow`）。中文文案图走 HTML 渲染，**不糊字**，这是接单质量底线。产品图可走 `product_img` 实拍 / `product_prompt` 生图 / 网页端自动生图；三者最终都归一到 `<out>/product_<sku>.png`，`fill_template.py` 自动拾取，无需改订单。

---

## 四、关键规范速查

- **2026 淘宝规格**：主图 1440²、导购 1440×1920、白底 800²、详情 1440 宽切片（单张高/宽≤2）。详见 `references/taobao-spec-2026.md`。
- **合规红线**：极限词（最低/第一/绝对）、医疗功效、虚假承诺一律改掉。详见 `references/compliance-check.md`。
- **千牛上架**：手动上架操作路径见 `references/taobao-onboarding.md`。
- **交付 SOP**：自动发货话术、买家手册、1 次免费小改，见 `references/delivery-sop.md`。
- **报价模板**：基础 ¥29 / 标准 ¥99 / 高级 ¥299（自用零成本，毛利即利润）。详见 `references/pricing.md`。
- **品类预设**：服装/美妆/数码/食品/家居/母婴/虚拟品/图书，见 `references/categories.md`。

---

## 五、协作铁律（团队运行不可违反）
1. 团队只能由主理人 **TeamCreate**，严禁委派成员建团。
2. 每阶段由对应成员**独立产出**，主理人不代写。
3. 成员产出 **SendMessage 回传主理人**，经主理人中转，禁止成员互连。
4. 专业结论以成员产出为准，主理人只编排汇编。
5. 调度用 Agent ID（MD 文件名去 .md），不用中文名。

---

## 附录 A · 真实 order.json schema（**唯一准绳**）

> 以 `skills/taobao-image-workflow/examples/order_example_*.json` 与
> `references/categories.md` 的品类片段为准。**照抄即可出图**，自创字段必报错。

| 字段 | 作用 |
|---|---|
| `sku` | 文件名后缀，必填 |
| `badge` / `title_line1` / `title_hl` / `sub` | 主图徽章 / 主标题 / 高亮 / 副标题 |
| `points[]` | 主图卖点（左图右文时显示在右侧） |
| `price` / `foot` | 价格 / 底部免责声明 |
| `detail[]` | 详情长图分段，每段 `type` 为 `ul` / `cards` / `steps` |
| `guide[]` | 导购图 **5 张**，每张 `badge`/`line1`/`hl` + `points`/`list`/`steps`/`tiers` 之一 |
| `whitebg_title` / `whitebg_sub` | 白底图文案 |
| `product_img`（可选） | 产品图绝对路径 → 主图 + 导购首图左图右文 |
| `product_prompt`（可选） | 无图时写产品描述 → 先生图任务单，图落 `<out>/product_<sku>.png` 后自动拾取 |
| `product_crop`（可选） | `[x1,y1,x2,y2]` 比例数组，仅对带脏背景实拍图裁剪 |

**禁止出现的旧字段**（历史文档遗留，已全部清除）：
`main` / `pill` / `title` / `subtitle` / `price_big` / `price_tail` / `tags` /
`sellingPoints` / `detailSections` / `style` / `gallery` / `category` / `hasPhysicalProduct`。

**产出规格**：主图 1440×1440 ×1、白底 800×800 ×1、导购 1440×1920 ×5、详情 1440 宽切 2-4 张。
「主图 ×5」是平台上限，不是本工作流产出数；要多卖点变体就复制订单多次出。

---

## 附录 B · 个人专用约定

- 本专家团固化在本机 **「我的专家」** 市场（`my-experts`），仅当前账号可见可用，**不对外分发、不上传公共市场**。
- 执行引擎以本机 `C:/Users/admin/.workbuddy/skills/taobao-image-workflow/` 为准；专家团内 `skills/` 是同步副本，两者保持一致。
- 生图相关配置（网页端持久登录 profile）保存在本机 `~/.workbuddy/ecom-web-profile/`，**属个人登录态，禁止打包外传**。
- `Gemini` 等境外 AI 工具名属合规硬违规词，仅可出现在内部脚本 / 任务单 / 本 SOP，**绝不可写进上架图、标题、详情文案**。
- 品牌真机商品图须核验授权；无授权一律按「参数图解 · 非官方出品」交付。
