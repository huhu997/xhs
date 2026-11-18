# S6 发布报告 · 20261105-stock2

> 角色：gzh-publisher
> 时间：2026-11-05 22:2x
> 主链路：`gzh.py publish`（未使用任何第三方 CLI，未全局安装任何包）

## 一、结论

**未推送成功。卡在 40164（本机公网 IP 不在公众号白名单），凭证本身有效。**

```
✗ 取 token 失败：{'errcode': 40164,
  'errmsg': 'invalid ip 117.151.76.207 ipv6 ::ffff:117.151.76.207,
             not in whitelist rid: 6aec8e97-7837257c-29521709'}
```

这是**纯网络白名单限制**，不是稿子的问题，也不是凭证的问题。同一台机器今天推两篇，两次都是同一个错误码、同一个 IP。

## 二、发布前检查（全部通过）

| 检查项 | 结果 |
|---|---|
| `gzh.py creds` | ✓ 凭证齐备（APP_ID 18 位 / SECRET 32 位，值未打印） |
| `gzh.py publish --dry-run` | ✓ 文件齐备，无警告 |
| 标题长度 | 14 字（未超 64 字节） |
| 封面 | `08-cover.png` 1880×800，2.350:1，偏差 0.0% |
| 正文图 | 1 张 `08-illustration.png` 本地相对路径，由 `gzh.py` 自动上传图床（本次未走到这步） |
| 粘贴版 h1 | 已移除（公众号会自动加标题，避免重复） |
| 外链 | 0 |
| 内联样式 | 全内联，无 `<style>` 外链 |

## 三、本次推送参数（用户加完 IP 白名单后可原样重跑）

```bash
EXPERT_DIR="C:/Users/admin/.workbuddy/plugins/cache/my-experts/gzh-content-ops/2.0.0"
cd "$EXPERT_DIR/output/20261105-stock2"
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

python "$EXPERT_DIR/assets/tools/gzh.py" publish \
  --html 08-article-paste.html \
  --title "昨天封板的票，今天八成还在涨" \
  --cover 08-cover.png \
  --digest "昨天封板 116 只，今天 95 只还在涨，81.9%。上证只涨 0.10%，红利在跌、光伏和 AI 在涨。" \
  --save-id
```

## 四、需要用户做的一件事

微信公众号后台 → 设置与开发 → 基本配置 → IP 白名单，把 **117.151.76.207** 加进去。
注意：家用宽带 IP 会变，如果明天又报 40164，重跑上面的命令看新 IP，再加一次。

## 五、没有做的事（明确声明）

- 没有群发、没有群控、没有用任何非官方接口。
- 没有生成 media_id（token 都没取到）。
- `draft_id.txt` 未生成。
- 没有尝试任何绕过手段。

## 六、如果重跑仍报 40164

1. 先在公众号后台确认 IP 是否加对（常见错误：加成了 IPv6 形式，或加了 `::ffff:` 前缀那串）。
2. 确认 `.env` 里的 APP_ID 和当前公众号是同一个（`gzh.py creds` 只验长度，不验归属）。
3. 不要在这时换工具——`wenyan-cli` / `publish.sh` 会走 macOS 凭证路径并自动全局装 259 个包，本机不适用。
