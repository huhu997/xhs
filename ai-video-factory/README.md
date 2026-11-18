# AI视频工厂专家团（AI Video Factory Team）

云端 / 零算力路线的一站式 AI 视频生产专家团：从选题策划一路编排到多平台发布。**不使用本地部署的视频生成模型**（Wan、Hunyuan、CogVideo 等）。

## 类型

Team 型（多角色协作团队）

## 团队构成（12 角色，每个绑定已审顶级 Skill）

| 角色 | 名字 | 职责 | 真实 Skill / Connector |
|------|------|------|------|
| 总制片人（主理人） | 傅映桥 | 编排调度、汇总交付 | — |
| 选题策划师 | 苏透点 | 选题挖掘、人群/卖点拆解、爆款文案 | `viral-video-copy` · `article2video` · `video` |
| 脚本分镜师 | 文幕白 | 脚本撰写、分镜提示词、节奏卡点 | `video-shotcraft` · `html-video` · `AI带货短视频流水线` |
| AI生成导演 | 范像生 | 文生/图生视频、商品视频、复刻爆款 | `hypit` · `pixelle-video` · VideoGen/picset/infimind |
| 数字人口播师 | 郎映人 | 口播/数字人视频、一张照片出片 | `lanshu-create-ai-presenter-video` · `digital-human-koubo` · `finance-explainer` |
| 剪辑后期师 | 严过剪 | 自动剪辑、字幕、配乐、调色、长转短 | `video-use` · `html-video`/`hyperframes` · ffmpeg |
| 发布增长官 | 霍推手 | 多平台矩阵、封面标题、发布节奏 | `RED-Skill` · `video-workflow` |
| 素材猎手 | 季猎手 | 抓参考/对标视频、B-roll 采集 | `douyin-video-download` · `wechat-video-downloader` · `video-downloader` |
| 动效设计师 | 董效实 | 动态文字、数据动效、转场、信息图动画 | `hyperframes-animation` · `hyperframes-creative` · `video-use` 动画 |
| 数据可视化师 | 涂画图 | 数据/对比/进度 → 视频图表（财经 crossover） | `stock-dataviz-video` · `knowledge-video-director` · `a2e-explain-video` |
| 封面品牌师 | 赵封面 | 封面图、品牌视觉、视觉锤 | `gaoding`(稿定AI) · `picset-commerce-images` |
| 成片审片官 | 审片官 | 发布前 QA 闸门：有声/钩子在画面/CTA/AI标识/人设真实度 | 6 项清单（纯审查权，无 Skill） |

渲染底座：`hyperframes` + `hyperframes-animation` + `hyperframes-creative`（本地零成本 HTML→MP4），已被 `video-use` / `html-video` 复用。

## 预设 Workflow

1. **完整出片流水线**：选题 → 脚本 →（AI生成 ∥ 数字人） → 剪辑 → **审片** → 发布
   - **闸门 0 · 取材（强制）**：开工前主理人采集真实素材；缺数据整片标「虚构示意」，禁止编造具体断言（练了 X 年 / 每周 X 次 / 体脂 X% 等）
   - **音频闸门（强制）**：剪辑必须补配音 / BGM，不得交付静音成片（用 `tools/tts_mix.py`）
   - **审片闸门（强制）**：qa-reviewer 按 6 项清单过检，不通过打回对应负责人
2. **文章/干货转视频**：零云算力走 hyperframes / html-video 渲染
3. **克隆爆款**：素材猎手抓对标 → 拆解爆点 → picset 复刻 / hypit 思路
4. **数字人口播**：avatar-presenter 用 lanshu / digital-human-koubo 出片（须授权 + 标 AI 生成）

## 内置工具（让能力真实可调用）

- `tools/render.sh`：一键渲染封装。已内置 `HYPERFRAMES_FFMPEG_PATH` / `HYPERFRAMES_FFPROBE_PATH` 与本机 ffmpeg/ffprobe 绝对路径 + 本地 `node_modules` 查找，剪辑角色直接调，免新人撞 ffmpeg 墙。
- `tools/tts_mix.py`：本地零成本 TTS（edge-tts，微软免费语音）+ 混音入轨。静音成片必须过这道补声音。用法见文件头注释。

## 使用示例

- 我要做一条AI视频，从选题到发布帮我全流程跑一遍。
- 把这篇干货文章转成一条短视频。
- 帮我拆解并克隆一个爆款视频的拍摄思路。

## 头像

头像暂未生成（可在 WorkBuddy 内一键用 ImageGen 补齐，或手动替换为 512×512 PNG/JPG，≤500KB）。
未生成头像不影响专家团正常使用。

## 安装

专家包已在专家目录下：

```
F:\Cache\.workbuddy\plugins\marketplaces\my-experts\plugins\ai-video-factory/
```

如需重新注册使其可见：

```bash
python scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r ai-video-factory.zip ai-video-factory/
```
