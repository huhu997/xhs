"""公众号排版格式化：Markdown → 适配公众号的 HTML"""

import re


def to_wechat_html(markdown_text: str) -> str:
    """将 Markdown 转换为适配微信公众号的 HTML 排版"""
    html = _convert_markdown(markdown_text)
    return _wrap_html(html)


def _convert_markdown(text: str) -> str:
    lines = text.split("\n")
    html_parts = []
    in_list = False
    list_type = None

    for line in lines:
        stripped = line.strip()

        # 空行
        if not stripped:
            if in_list:
                html_parts.append(f"</{list_type}>")
                in_list = False
            continue

        # 图片
        img_match = re.match(r"!\[(.*?)\]\((.*?)\)", stripped)
        if img_match:
            html_parts.append(f'<img src="{img_match.group(2)}" alt="{img_match.group(1)}" style="max-width:100%;margin:12px 0;border-radius:8px;">')
            continue

        # 标题
        if stripped.startswith("### "):
            html_parts.append(f"<h3 style='font-size:17px;margin:20px 0 10px;'>{stripped[4:]}</h3>")
            continue
        if stripped.startswith("## "):
            html_parts.append(f"<h2 style='font-size:18px;margin:24px 0 12px;'>{stripped[3:]}</h2>")
            continue
        if stripped.startswith("# "):
            html_parts.append(f"<h1 style='font-size:20px;margin:24px 0 12px;'>{stripped[2:]}</h1>")
            continue

        # 无序列表
        if stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:]
            if not in_list or list_type != "ul":
                if in_list:
                    html_parts.append(f"</{list_type}>")
                html_parts.append("<ul style='padding-left:20px;'>")
                in_list = True
                list_type = "ul"
            html_parts.append(f"<li style='margin:6px 0;'>{content}</li>")
            continue

        # 有序列表
        ol_match = re.match(r"^\d+\.\s+(.*)", stripped)
        if ol_match:
            content = ol_match.group(1)
            if not in_list or list_type != "ol":
                if in_list:
                    html_parts.append(f"</{list_type}>")
                html_parts.append("<ol style='padding-left:20px;'>")
                in_list = True
                list_type = "ol"
            html_parts.append(f"<li style='margin:6px 0;'>{content}</li>")
            continue

        # 引用
        if stripped.startswith("> "):
            content = stripped[2:]
            html_parts.append(
                f"<blockquote style='border-left:4px solid #3b82f6;padding:8px 16px;margin:12px 0;color:#666;background:#f8fafc;border-radius:0 8px 8px 0;'>{content}</blockquote>"
            )
            continue

        # 分割线
        if stripped in ("---", "***", "___"):
            html_parts.append("<hr style='border:none;border-top:1px solid #e2e8f0;margin:24px 0;'>")
            continue

        # 普通段落（处理加粗、斜体、行内代码）
        if in_list:
            html_parts.append(f"</{list_type}>")
            in_list = False

        paragraph = _inline_format(stripped)
        html_parts.append(
            f"<p style='font-size:15px;line-height:1.75;margin:12px 0;letter-spacing:0.5px;'>{paragraph}</p>"
        )

    if in_list:
        html_parts.append(f"</{list_type}>")

    return "\n".join(html_parts)


def _inline_format(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.*?)`", r"<code style='background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:14px;'>\1</code>", text)
    text = re.sub(r"~~(.*?)~~", r"<del style='color:#999;'>\1</del>", text)
    return text


def _wrap_html(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>公众号文章</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; padding: 20px; max-width: 680px; margin: 0 auto; background: #fff; color: #333; }}
</style>
</head>
<body>
{body}
</body>
</html>"""
