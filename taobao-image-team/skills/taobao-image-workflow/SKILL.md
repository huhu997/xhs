---
name: taobao-image-workflow
description: 淘宝/天猫商品上架图全套生产工作流：主图(1440)、3:4导购图(1440x1920)、白底图(800)、详情长图切片(1440宽)，覆盖接单→出图→合规→上架→交付。支持 product_img 实拍/渲染图叠加（左图右文）与网页端自动生图（Playwright 持久 profile，无需 API key）。可自用、可接单代做、可白标卖给店主。触发词：淘宝上架图、淘宝主图、详情长图、导购图、商品图、上架素材、电商图工作流。
---

# 淘宝电商图工作流（生产级）

一套**参数化、可直接上架**的淘宝图生产流水线。融合了两套基因：
- 已验证可上架的爆款模板结构（深蓝科技风 + 橙红，见 `references/template-library/` 的 S1 样例）
- 本机 Chrome 渲染管线（不依赖云端、不挑本地模型、中文不糊字）

## 适用场景

- **自用**：把自己的虚拟品/实物品上架淘宝
- **接单代做**：帮别人出全套上架图（成本低、可报价赚毛利）
- **卖铲子**：把整套 skill 去署名打包，按 ¥199–499 卖给淘宝店主/代运营

## 前置依赖

| 依赖 | 用途 | 备注 |
|---|---|---|
| Node 22.x | 跑 `render_all.mjs` | 系统 `C:/Program Files/nodejs/node.exe` 或托管 `22.22.2-6` |
| 系统 Chrome | 渲染截图（CDP） | 自动探测 `C:/Program Files/Google/Chrome/Application/chrome.exe`，缺则用 puppeteer headless-shell |
| Python + Pillow | `fill_template.py` / `slice_images.py` | `pip install pillow` |
| Python Playwright + Chromium | 仅「档 B 网页端自动生图」需要 | 本机已装 1.64.1 + chromium；`pip install playwright && playwright install chromium` |

> 不依赖任何云端生图 API、不需要 API key。中文文案图走 HTML 渲染，彻底规避 AI 生图小字翻车。

## 三步出图（核心）

```bash
# 1) 填订单：直接复制 references/categories.md 里对应品类的 order.json 片段，
#    或改 examples/order_example_*.json（虚拟品/数码3C/手机壳三份真实样例）
#    可选：订单加 "product_img": "C:/绝对路径/图.png" 叠加产品图（见「补产品图」节）
# 2) 参数化出 4 类 HTML（主图/详情/导购3x4/白底）
python scripts/fill_template.py order.json --out 客户目录
# 3) 渲染 + 切片
node scripts/render_all.mjs 客户目录
python scripts/slice_images.py --root 客户目录
```

产出（自动按 2026 新版规格）：

| 文件 | 规格 |
|---|---|
| `主图_Sx.png` | 1440×1440（默认 1 张；多卖点变体可复制订单多次出） |
| `白底图_Sx.png` | 800×800 |
| `导购图_Sx_1~5.png` | 1440×1920 |
| `详情图_Sx_01~.png` | 1440 宽，按段切片 ≤2800 高 |

## 完整流程（接单到交付）

1. **接单** → `references/intake-form.md` 收需求
2. **出图** → 上面三步（订单可含 `product_img` 叠加产品图）
3. **QA** → 抽查主图/详情中文清晰、无裁切异常；规格自查见 `references/taobao-spec-2026.md`
4. **合规** → `references/compliance-check.md` 发布前过一遍
5. **上架** → `references/taobao-onboarding.md` 千牛 9 步
6. **交付** → `references/delivery-sop.md`（交付物清单 + 自动发货 + 售后）
7. **视频（可选）** → 见下

## 补产品图（可选）

工作流默认出「纯文案参数卡」（中文不糊字、可直接上架）。要更吸睛的「商品图」观感，可叠加一张产品实拍/渲染图：

- 主图改为**左图右文**布局：左侧白卡放产品图，右侧放文案
- 导购首图（第 1 张 card）同步叠加同一张产品图
- 无任何图时自动回退纯文案卡，**向后兼容**

### 三种给图方式（优先级从高到低）

| 方式 | 订单字段 | 适用 |
|---|---|---|
| ① 指定路径 | `"product_img": "C:/绝对路径/xxx.png"` | 已有实拍/渲染图 |
| ② 约定路径（推荐） | 图存为 `<out>/product_<sku>.png` | **Gemini/宿主生图**，零改单 |
| ③ 生图任务单 | `"product_prompt": "产品描述"` | 还没图，先让 AI 生 |

可选 `"product_crop": [x1,y1,x2,y2]`（比例数组）：只对带杂背景/水印的实拍图启用，裁掉脏区。**Gemini 生成的白底图不要加**，默认不裁剪。

### 档 A｜手动生图（零配置，最稳；网页端一直能走）

```bash
# 1) 订单只写 product_prompt，首跑生成「生图任务单_<sku>.txt」+ 标准 prompt
python scripts/fill_template.py order.json --out <out>
python scripts/gen_product.py order.json --out <out>       # 打印标准生图 prompt

# 2) 把 prompt 交给 Gemini（会话里的宿主生图工具）出图
#    注意：Gemini 是境外工具名，只用于内部生图，禁止写进上架物料

# 3) 把 Gemini 给的图落盘到约定路径（自动转 PNG / 白底合成 / 限长边 1600）
python scripts/gen_product.py order.json --save <Gemini图片路径> --out <out>

# 4) 重跑三步，脚本自动拾取产品图
python scripts/fill_template.py order.json --out <out>
node scripts/render_all.mjs <out>
python scripts/slice_images.py --root <out>
```

> **设计意图**：生图后端与排版解耦。脚本层不绑定任何 AI 服务、不需要 API key；AI 生完图只需做一次 `--save`，之后全自动。图从 Gemini、宿主工具还是实拍来都一样。
> **积分**：宿主生图按张扣积分（约 5–10/张）；纯 HTML 路线零成本。
> **合规**：`Gemini` 属境外 AI 工具名（硬违规词），只能出现在内部 SOP/任务单，绝不能进上架图、标题、详情文案。

现成自用样例：`examples/order_example_selfuse.json`（手机壳，仅 `product_prompt`，无 `product_img`）。

### 档 B｜网页端自动生图（无需 API key，推荐自用）

本机没有 Gemini API key，但**网页端能走**。脚本接管一个持久化 profile 的浏览器：第一次手动登录一次，之后登录态长期复用；脚本只做「贴 prompt → 发送 → 等生成 → 抓图 → 归一化落盘」，不碰账号、不碰网络配置、不需要 key。

```bash
# 0) 通道自检（无头、不弹窗、不碰登录态）—— 已实跑通过
python scripts/gen_product_web.py order.json --out <out> --probe

# 1) 正式跑：首次弹出浏览器，登录一次后脚本自动继续
python scripts/gen_product_web.py order.json --out <out>

# 2) 更省事：一键把「网页端生图 + 三步出图」全串起来
python scripts/run_all.py order.json --out <out> --web
```

- `--url` 可换任意网页生图入口（默认 Gemini 网页端）
- `--proxy http://127.0.0.1:xxxx`：网页需要代理时显式传回（脚本默认清掉 env 里失效的本地代理，避免拖累本地 CDP）
- `--headless`：已登录过 profile 后可无头跑
- 抓图双通道：优先点下载按钮取原图，失败则用 canvas 提取；页面改版/额度限制时打印兜底命令，不会卡死

**三个真实门槛**（都在浏览器侧，不在脚本）
1. 首次要在弹出窗口登录一次，登录态存 `~/.workbuddy/ecom-web-profile`，之后免登
2. 网页能否打开取决于本机网络/浏览器，脚本不处理可达性；打不开就退回档 A
3. 网页 DOM 会改版，selector 已做多重兜底但仍可能失效 → 明确提示「手动存图 + `--save`」

> **网页端从未被堵**：档 A 第 2 步「把 prompt 交给生图工具」直接贴进网页即可。此前说的「脚本层直连不了」仅指 **API 直连**，不是网页端。

### 一键出全套（不用记命令）

```bash
python scripts/run_all.py order.json --out <out>          # 已有 product_img / 约定路径图
python scripts/run_all.py order.json --out <out> --web     # 先走网页端自动生图
```

自动依次跑 `fill_template.py → render_all.mjs → slice_images.py`，末尾列出全部成品 PNG。已实跑验证：`[auto]` 自动拾取、渲染异常 0、9 张成品。

产品图要求：白底/纯色背景最佳；生活场景图需先去背景去水印——**本机当前无 rembg/cv2，无法 AI 抠图**，请给干净图或用生图工具直接生白底图。

## 主图视频（可选）

- 方案 A（自托管）：复用 HyperFrames `make_video.py`，用 `HF_WORKFLOW` / `PYTHON_BIN` 指定路径，出 1:1 / 3:4 / 9:16 三条
- 方案 B（云端）：极睿 / 字节 Seedream / GPT Image 出片后回灌
- 注意：9:16 只进公域推荐，详情页要用 1:1 或 3:4

## 文件结构

```
taobao-image-workflow/
├── SKILL.md
├── scripts/
│   ├── fill_template.py        # 订单 JSON → 4 类 HTML（含产品图内联/自动拾取/生图任务单）
│   ├── gen_product.py          # 生图 prompt 输出 + 产品图归一化落盘（解耦生图后端）
│   ├── gen_product_web.py      # 网页端自动生图 → 落盘（Playwright 持久 profile，无需 key）
│   ├── run_all.py              # 一键串起 生图(可选) → fill → render → slice
│   ├── template_main.html      # 主图模板（左图右文，含 {{HAS_IMG}}/{{LEFT}} 占位符）
│   ├── template_detail.html    # 详情模板（分段式）
│   ├── template_guide.html     # 导购3x4模板（5卡片，第1卡支持 has-img）
│   ├── template_whitebg.html   # 白底图模板
│   ├── render_all.mjs          # 系统 Chrome CDP 渲染 + 生成切片任务
│   ├── slice_images.py         # Pillow 切片（跨平台）
│   └── stitch_long_image.py    # 备用拼长图
├── references/
│   ├── taobao-spec-2026.md     # 2026 素材规格
│   ├── compliance-check.md     # 合规自查清单
│   ├── taobao-onboarding.md    # 千牛上架指南
│   ├── delivery-sop.md         # 交付 SOP
│   ├── intake-form.md           # 接单需求单
│   ├── pricing.md              # 报价模板
│   ├── categories.md           # 8 大品类预设（含 7 份可直接用的真实 schema order.json 片段）
│   └── template-library/       # S1 爆款样例（主图/详情/导购/白底）
├── examples/
│   ├── order_example_virtual.json    # 虚拟品样例（纯文案卡）
│   ├── order_example_iphone18pm.json # 数码3C样例（参数图解·非官方出品）
│   ├── order_example_case.json       # 手机壳样例（含 product_img 实拍图叠加 + product_crop）
│   └── order_example_selfuse.json    # 自用样例（仅 product_prompt，走生图链路）
└── _deprecated/                      # 旧版死文件（旧 schema 样例 / 1080 渲染脚本），勿用
```

> **全部文档已于 2026-11-06 校准对齐真实 schema 与 2026 规格**：`categories.md` 的 7 份品类片段均通过 `fill_template.py` 实跑 + 端到端三步出图验证（4 类 HTML、导购 5 张、0 异常）。照抄文档即可出图。

## order.json 字段（以 examples/ 为准，真实 schema）

| 字段 | 作用 |
|---|---|
| `sku` | 文件名后缀，必填 |
| `badge` / `title_line1` / `title_hl` / `sub` | 主图徽章/主标题/高亮/副标题 |
| `points[]` | 主图卖点（左图右文时显示在右侧） |
| `price` / `foot` | 价格 / 底部免责声明 |
| `detail[]` | 详情长图分段，每段 `type` 为 `ul` / `cards` / `steps` |
| `guide[]` | 导购图 5 张，每张 `badge`/`line1`/`hl` + `points`/`list`/`steps`/`tiers` 之一 |
| `whitebg_title` / `whitebg_sub` | 白底图文案 |
| `product_img`（可选） | 产品图绝对路径，叠加主图+导购首图 |
| `product_prompt`（可选） | 无图时写产品描述 → 生成生图任务单，交给 Gemini 出图 |
| `product_crop`（可选） | `[x1,y1,x2,y2]` 比例数组，仅对带脏背景的实拍图裁剪 |

## 改风格 / 加品类

- 模板在 `scripts/template_*.html`，纯 HTML+CSS，改完重跑 `render_all` 即可
- 新品类 = 新一份 `order.json`，模板不变，一键出图
- 想换配色（如食品用暖橙、美妆用粉）：复制模板改 CSS 变量后重出

## 为什么这套能接单/卖

- **中文不糊字**：文案图走 HTML 渲染，不是 AI 生图
- **成本近零**：本机渲染，报价即毛利
- **规格合规**：直接对齐 2026 新版，过审率高
- **可白标**：整个 skill 去署名打包，附 30 分钟陪跑
