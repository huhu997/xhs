# 淘宝上架图交付专家团（Taobao Listing Image Delivery Team）

> 🔒 **个人专用版 v1.1.0 · Private / Personal Use Only** — 固化于 2026-11-06，保存在本机「我的专家」市场，仅当前账号可见可用；**不对外分发、不上传公共市场**。网页端登录态 profile 与本机绝对路径均属个人资产，禁止随包外传。

一站式淘宝上架图交付团队：从需求拆解、卖点文案、视觉设计，到本地出图、切片质检、合规上架全流程覆盖，支持**自用、接单代做、打包售卖**三种模式。

## 类型
Team 型（多角色协作团队）

## 团队角色
| 角色 | 花名 | 职责 |
|---|---|---|
| 主理人 / 交付操盘手 | 范成单 | 建团、调度、进度通报、汇编 |
| 接单拆解师 | 许析单 | 接单拆解、品类参数化、order.json |
| 卖点文案师 | 文点睛 | 卖点/标题/关键词/详情文案 |
| 视觉风格师 | 展图新 | 模板选型、风格锁、画廊规划 |
| 渲染执行师 | 柯出图 | 跑脚本出图：fill→render→slice |
| 合规交付师 | 严达标 | QA、合规扫描、拼长图、上架表单、交付SOP |

## 完整 SOP
见 `references/sop.md`（6 个 Phase 串行接力 + 三大使用模式 + 命令速查 + 规范速查 + 协作铁律 + **附录 A 真实 order.json schema** + **附录 B 个人专用约定**）。

## 执行引擎
内置技能 `skills/taobao-image-workflow/`：4 类 HTML 模板 + `fill_template.py` + `render_all.mjs`（系统 Chrome CDP）+ `slice_images.py`（Pillow）+ `stitch_long_image.py` + `gen_product.py` / `gen_product_web.py`（网页端生图，无需 API key）+ `run_all.py`（一键出全套）。中文文案图走 HTML 渲染不糊字，规格对齐 2026 淘宝。

一键：`python scripts/run_all.py order.json --out <out>`；加 `--web` 先走网页端自动生图。

> 该副本已与本机用户级 skill `C:/Users/admin/.workbuddy/skills/taobao-image-workflow/` 同步（v1.1.0）；旧版副本备份在 `电商图服务方案/_backup/`。

## 使用示例
- "我要接一个淘宝上架图订单，帮我走完整交付流程"
- "给我做一个虚拟品/服装/食品的淘宝主图+详情长图"
- "把这套上架图工作流打包成可售卖的技能包"

## 头像
7 张头像已生成在 `avatars/`（`team.png` + 6 位成员）。如需替换：PNG/JPG，512×512，≤500KB。

## 注册（使其在工作台可见）
```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享
```bash
python3 scripts/package_expert.py <expert-dir>
```
