# 公众号内容运营专家（gzh-content-ops）v2.0

你独用的公众号内容运营专家：AI 人设号（效率搞钱派）定位，团长调度 7 角色 Agent 流水线，从一句话方向跑到草稿箱 + 视频号脚本。继承墨稿卖点（终点=草稿箱、AI 味 ≤20 可量化），并新增排版多选（16 主题 × 8 版式）、**零积分 Gemini 生图**、**栏目化连载模板**、视频号适配、合规审查、发布后复盘闭环。

> **独用声明**：本专家及全部 `team/` 编排、`gzh-workflow/references/` 规范、`assets/` 资产、`output/` 产出，均位于用户个人 marketplace 目录（F:/Cache/.workbuddy/plugins/marketplaces/my-experts/），不外发、不同步到公共市场，仅该用户本机可见可用。
>
> **全合并已完成（2026-11-05）**：自建《公众号文章创作工作流》的**实物资产**已物理收编进包 —— `assets/scripts/gemini-gen.mjs`（零积分生图脚本）、`assets/workflow/公众号文章创作工作流-原文.md`（工作流原文）、`assets/templates/build_preview.py`（排版模板）；专家包内所有外部绝对路径已改为包内路径，统一由 `config/paths.md` 管理。产出统一落 `output/YYYYMMDD-<slug>/`，不再散落到 `zcode工作区/articles/`。源包与运行缓存必须同步，命令见 `config/paths.md` 第六节。

## 类型

Agent 型（团长 / 主编调度中枢）+ 多 Agent 团队编排（S1–S7 子代理）

## 团队编排（核心工作流）
- `team/TEAM.md` —— 角色表 + 流转图 + 合规铁律（总览）
- `team/ORCHESTRATOR.md` —— 团长调度模板（照它用 Agent 工具拉起角色）
- `team/roles/*.md` —— S1 选题侦察兵 / S2 去味编辑 / S3 视觉排版官 / S4 跨平台适配官 / S5 合规审查官 / S6 发布官 / S7 数据复盘师 的完整 prompt

## 七大角色
| 代号 | 角色 | 职责 | 挂载 skill |
|---|---|---|---|
| 团长 | 本专家 | 收方向 / 定主线 / 写稿 / 调度 | gzh-workflow + 公众号爆文写作 + wechat-article-writer |
| S1 | 选题侦察兵 | AI 人设选题（痛点 / 行业动态 / 人设连贯） | wechat-viral-topic + WebSearch |
| S2 | 去味编辑 | 去 AI 味终检 ≤20/100 | humanizer-zh-pro + lieflat-less-ai-tone + copy-editing |
| S3 | 视觉排版官 | 封面 + 多变排版（16 主题 × 8 版式，先出候选） | wechat-cover + baoyu-markdown-to-html + article-illustration-planner + gemini-gen.mjs |
| S4 | 跨平台适配官 | 长文 → 视频号口播脚本 / 分镜 / 文案 | article2video + self-media-platform-copywriting |
| S5 | 合规审查官 | AI 人设合规（不夸大 / 不割韭菜 / 不硬广） | 通用合规 |
| S6 | 发布官 | 推公众号草稿箱 | wechat-publisher + baoyu-post-to-wechat |
| S7 | 数据复盘师 | 双渠道复盘反哺选题 | WebSearch + 自有数据 |

## 功能
- 一句话出稿：吃一个 AI 方向（事件 / 话题 / 工具 / 痛点），自动跑出八段式结构稿
- 配图零积分：封面 / 插图走 Gemini 网页端 VIP 额度（`gemini-gen.mjs`），Opera 抓一次 Cookie 后免浏览器
- 封面 2.35:1 双比例：关键内容压中间 42% 安全区，一张图同时适配列表与朋友圈 1:1 裁切
- 排版多选：16 套配色主题 × 8 种版式，S3 先出 3 套候选让你挑，再渲染
- 去 AI 味工程：三条机制 + AI 疑似度检测 ≤20/100 才放行
- 栏目化连载：内置《A股江湖每日说书》群像模板（固定角色卡 + 连续回目 + 正传/外传规则）
- 视频号适配：长文一键转口播脚本 / 分镜 / 文案
- 草稿箱交付：官方接口推送，发布用户手动点；视频号上传也留手动

## 使用示例
- 用今天的一个 AI 话题，帮我跑一篇公众号草稿（含选题、封面、排版候选，进草稿箱，附视频号脚本）
- 这篇先给我出 3 套排版候选（主题 × 版式）再渲染
- 用《A股江湖每日说书》栏目，跑一篇今天的复盘，配图走 Gemini 零积分生图
- 把这篇长文适配成视频号口播脚本

## 账号身份（唯一真源）

`config/account.md` 存放当前公众号昵称、笔名、封面署名与禁用旧名。**所有图上的账号/署名文字只能从这里取**，禁止写死在 `cover.html` 或沿用旧封面模板。

- `python assets/tools/gzh.py account --live` —— 调微信后台核昵称是否与配置一致
- `python assets/tools/gzh.py brand output/<目录> --strict` —— 扫旧账号名，命中即阻断
- `publish` 推送前内置同一道拦截；账号改名 SOP 见 `config/account.md` 第 4 节

## 头像

头像在 `avatars/expert.png`（512×512 PNG）。如需替换，要求：PNG/JPG，512×512，单张 ≤500KB。

## 安装

专家已在个人 marketplace 目录下，运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r gzh-content-ops.zip gzh-content-ops/
```
（注意：默认仅个人使用，分享前请确认不泄露私有资产。）
