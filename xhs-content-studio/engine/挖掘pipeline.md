# 需求挖掘 Pipeline（通用 · 可重跑 · 带时间戳）

> 与任何账号无关。输入 = 关键词列表，输出 = 带时间戳需求报告。约束 G-B：必须标采集日期，结果随平台 / 季节漂，pipeline 必须可重跑。

## 一、四步

1. **关键词列表**：按当前方向选 8-12 个词（覆盖主变现 / 流量入口 / 背书三块）。
2. **抓笔记**：登录态 Chrome(9222) + CDP 直采搜索列表页，提取 `noteId / title / author / liked / pubTime`（混合格式：`X天前` / `MM-DD`）。
3. **抓评论**：对 Top 高赞笔记进详情页抓 `.parent-comment`，提取 `content / liked / isSub`。
4. **聚类 + 报告**：赞数分桶、竞争度、时间分桶（新老对比）、评论诉求聚类、标题公式、不建议做清单 → 存 `state/demands/`。

## 二、已验证脚本（verified · 位于 `engine/scripts/`）

> 引擎自带、可独立重跑。运行前 `cd engine/scripts/`，数据 JSON 放同目录。

- `collect_tokens_v2.mjs`：多关键词抓笔记（10s 等待 + 滚动 + null 保护）。
- `collect_pubtime.mjs`：补发布时间字段（列表页 `.time`）。
- `comments_dir1.mjs`：抓 Top N 笔记评论。
- `analyze_with_time.mjs`：时间分桶 + 竞争度。
- `analyze_comments.mjs`：评论诉求聚类 + 高赞原话。
- `generate_actionables.mjs`：聚合选品参考 + 引流标题。
- `render_cards.cjs` / `render_D1.cjs`：Apple 风配图渲染（依赖 chrome-headless-shell + playwright-core）。

## 三、运行须知（已踩坑）

- **死代理**：`HTTP_PROXY=127.0.0.1:1080` 导致 node fetch 失败 → 运行前 `unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy`。
- **Chrome 端口**：先 `curl -sf --noproxy '*' http://127.0.0.1:9222/json/version` 探活；死了用标准路径 Chrome 带 `--remote-debugging-port=9222` 重启。
- **SPA 时序**：navigate 后等 10s + 滚动才能抓到 `section.note-item`。
- **搜索结果波动**：两次搜索重叠极低 → 重采数据不与旧数据硬匹配，以当次自洽数据集分析。
- **时间精度**：列表页只到天，拿不到小时级「几点发」；小时级需进详情页抓精确时间戳（按需）。

## 四、输出规范

- 报告必须含「采集日期」与「数据时效声明」。
- 评论层必须单列「真人原话金矿」（高赞长评），这是选题库的第一手素材。
