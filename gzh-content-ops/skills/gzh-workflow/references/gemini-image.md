# Gemini 生图执行手册（零积分路线）

> 本文件是 S3 视觉排版官的**默认生图后端**操作手册。核心：用 Opera 首次登录抓 Cookie，之后纯 API 出图，**不消耗任何积分、不需要常驻浏览器**。

> **路径已全量收编（2026-11-05）**：生图脚本现在**包内自带**，不再是外部引用。完整路径表见 `${EXPERT_DIR}/config/paths.md`。所有命令先定义：
> ```bash
> unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
> EXPERT_DIR="F:/Cache/.workbuddy/plugins/marketplaces/my-experts/plugins/gzh-content-ops"
> BUN="C:/Users/admin/.bun/bin/bun.exe"
> GEMINI="$EXPERT_DIR/assets/scripts/gemini-gen.mjs"
> ```
> `bun` 不在 PATH，必须用上面的绝对路径；脚本调用一律加 `timeout`（输出后不肯自行退出）。运行时若用的是缓存包，把 `EXPERT_DIR` 换成 `C:/Users/admin/.workbuddy/plugins/cache/my-experts/gzh-content-ops/2.0.0`。

## 一、为什么不用 `baoyu-danger-gemini-web`

包内 `skills/baoyu-danger-gemini-web` 走的是「启动 Chrome 抓 Cookie」。在 Chrome 127+ 上已实测走不通：

- Chrome 的 **App-Bound Encryption (ABE) v20** 把 cookie 加密绑死在当前安装实例上；
- 复制 profile 目录 → 副本里的 v20 cookie 被浏览器启动时剔除 → 副本没有会话令牌；
- 日常 profile 起不了调试端口（singleton 锁 + 体积过重），空白 profile 又没有登录态。

**结论：Chrome 这条路不要再试。** 改用 Opera + `gemini-gen.mjs`（自建脚本，绕开 ABE）。

## 二、一次性登录（只做一次）

### 2.1 启动 Opera（带调试端口 + 指定 profile）

```bash
"F:/Programs 应用程序/O浏览器/opera.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="F:/桌面/zcode工作区/.gemini-opera-profile"
```

- 端口必须是 **9222**（脚本默认值）
- `--user-data-dir` 是**登录态真正存在的地方**，不是 Opera 安装目录
- ⚠️ `F:/Programs 应用程序/O浏览器/` 下若还有一个旧的 `.gemini-opera-profile`，是废弃副本，别用

浏览器打开后访问 `https://gemini.google.com`，用**有 VIP 的那个 Google 账号**登录，确认能看到对话界面。

### 2.2 抓取并缓存 Cookie

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
EXPERT_DIR="F:/Cache/.workbuddy/plugins/marketplaces/my-experts/plugins/gzh-content-ops"
BUN="C:/Users/admin/.bun/bin/bun.exe"
timeout 60 "$BUN" "$EXPERT_DIR/assets/scripts/gemini-gen.mjs" --login
```

- Cookie 存到 `C:\Users\admin\AppData\Roaming\baoyu-skills\gemini-web\cookies.json`
- 格式 `{ version, updatedAt, cookieMap, source }`，关键字段 `__Secure-1PSID` / `__Secure-1PSIDTS`
- 看到「验证通过」即可**关闭 Opera**，之后出图不再需要浏览器

### 2.3 首次登录前的代理检查（必做）

脚本会 `detectAndSetProxy()`：探测 1080 / 7890 / 7891，都没有就尝试拉起 Linsoc。

**坑**：该函数开头有 `if (HTTPS_PROXY || HTTP_PROXY) return;` —— 若环境变量里残留了别的代理（例如沙箱代理 `127.0.0.1:2233`），它会直接跳过探测、误用错误出口，表现为 `502 Bad Gateway` 或返回登录落地页。

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
```

再确认路是通的：

```bash
curl -sI --proxy 127.0.0.1:1080 --max-time 15 -o /dev/null -w "%{http_code}\n" https://gemini.google.com/
# 期望 200
```

Linsoc 是**拨号型客户端**：进程在跑 ≠ 已连通。要用户在托盘里点「连接」并选节点（新加坡代理 1），1080 才会真正起来。

## 三、日常出图

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
EXPERT_DIR="F:/Cache/.workbuddy/plugins/marketplaces/my-experts/plugins/gzh-content-ops"
BUN="C:/Users/admin/.bun/bin/bun.exe"
GEMINI="$EXPERT_DIR/assets/scripts/gemini-gen.mjs"
timeout 120 "$BUN" "$GEMINI" -p "<prompt>" -i "$EXPERT_DIR/output/<YYYYMMDD-slug>/<图名>.png"
```

| 命令 | 作用 |
|---|---|
| `--status` | 查看 Cookie 缓存状态（含 updatedAt） |
| `--login` | 从 9222 端口重新抓 Cookie |
| `--rotate` | 手动轮换 `__Secure-1PSIDTS`（通常不用，脚本自动处理） |
| `-p <prompt> -i <path>` | 出图到指定路径 |

出图失败时脚本会自动轮换 Cookie 重试一次。仍失败再走 `--login`。

## 四、尺寸与安全区

| 用途 | 比例 | 说明 |
|---|---|---|
| **封面（首选）** | **2.35:1** + 中间 42% 安全区 | 一张图同时兼容订阅号列表（2.35:1）与朋友圈分享（1:1 裁切）；关键内容集中在中部，两侧只放背景装饰 |
| 方封面（需要独立首图时） | 1:1 | 草稿箱首图 |
| 正文插图 | 16:9 | 数据对比、机制拆解、展望 |
| 长图/竖版插图 | 3:4 | 移动端长阅读 |

> 2.35:1 是**成本最优解**：替代原来「21:9 + 1:1 + 3:4 三张」的方案，一次出图覆盖两处展示位。

## 五、Prompt 模板（实测有效）

### 封面（2.35:1）

```
Clean Swiss editorial 3D style, [画面描述].
Chinese labels: '[标签1]', '[标签2]'.
Color palette: [主色] (#hex), [强调色] (#hex), off-white background (#f5f5f0).
[A股: RED for UP/GAIN, GREEN for DOWN/LOSS — 红涨绿跌]
2.35:1 aspect ratio, safe for 1:1 center crop — keep all text and main subject centered within middle 42% of width, decorative background elements can extend to edges.
No logos, no watermarks, no decorative blobs, clean sans-serif style.
```

### 配图（16:9）

```
Clean Swiss editorial 3D style, [画面描述].
Chinese labels: '[标签1]', '[标签2]'.
Color palette: [主色] (#hex), [强调色] (#hex), off-white background (#f5f5f0).
[A股: RED for UP/GAIN, GREEN for DOWN/LOSS — 红涨绿跌]
16:9 aspect ratio, no logos, no watermarks, no decorative blobs, clean sans-serif style.
```

**要点**
- 配色取自 `themes.md` 选定的主题（主色 + 底纸色 + 强调色），禁止临时换色
- **A 股内容红涨绿跌；美股内容绿涨红跌**——写进 prompt，别指望模型自己懂
- 中文标签用单引号短词（2–6 字），长句必糊
- 数字尽量不交给模型渲染（扩散模型数字易错），数字放正文/表格，图只做场景与关系

## 六、降级链（按顺序）

1. **`gemini-gen.mjs`**（默认）——吃 VIP，零积分
2. **WorkBuddy `ImageGen` 工具**——`size="1536x1024"`、`quality="high"`，单张 5–10 信用分；图角带平台水印，正式发布前需处理
3. **本地 HTML/CSS 渲染**——`cover-spec.md` 的截图方案，中文最稳，配色绝对可控，但不适合写实场景

> 只要链路 1 可用，就不用 2。降级必须是显式决策，不是默认漂移。

## 七、故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `502 Bad Gateway` | 代理出口错（吃到沙箱 2233）或 cookie 失效 | 先 `unset` 代理变量；再用 curl 带 cookie 测 `/app` 是否返回登录落地页 |
| 返回登录落地页 / 无 `SNlM0e` | Cookie 已失效 | 开 Opera 确认登录态 → `--login` |
| `--login` 读到 1PSID 但令牌验证失败 | Opera 里的会话本身过期 | 在 Opera 窗口内重新登录 Google |
| 连 9222 失败 | Opera 没带 `--remote-debugging-port` 启动 | 用 2.1 的参数重开 |
| 出图慢/超时 | 代理节点拥塞 | 换 Linsoc 节点，或降级到本地渲染 |
| 中文糊成一团 | prompt 里中文太长 | 拆成 2–4 字短标签 |

## 八、给 S3 的硬约束

- 生图前先确认 `--status` 有 cookie；没有就走登录流程，不要静默降级
- 每张图生成后用 `Read` 确认文件存在且非 0 字节
- 所有 AI 生图必须在图注/文中标注「AI 生成」，并过 S5 合规
- 配色必须与选定主题同源，封面/插图/正文三处一致
