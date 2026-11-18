"""质检阶段：写完自动检查质量，给出改进建议"""

from typing import Generator, Optional
from core.llm import chat_once, chat_stream
from core.memory import build_system_prompt

SOUL_QUALITY = """你是一个严格的公众号文章编辑。

你的工作是把关文章质量，确保每一篇发出去的文章都能对得起读者的时间。

检查标准：
1. 开头 100 字有没有钩子
2. 金句密度（每 300 字至少 1 句）
3. 手机阅读友好度（段落不超过 3 行）
4. 有没有 AI 写作痕迹（禁用词、僵硬句式、编造数据、鸡汤金句、AI过渡句）
5. 结尾有没有转发动力
6. 整体读完是否值得转发
7. ⚠️ 特别检查是否有编造数据（"调查显示""数据显示""XX%的人"等无来源数据）
8. ⚠️ 特别检查是否有 AI 过渡句（"你知道吗？""为什么？""数据也证明了这一点"等）
9. ⚠️ 特别检查是否有空洞鸡汤（"XX是最好的XX""XX是最大的XX"等对仗句）
"""


def review_article(article: str) -> str:
    """跑质量清单，返回评分和改进建议"""
    system = build_system_prompt(SOUL_QUALITY)
    prompt = f"""请对以下文章进行质量评审，按以下格式输出：

## 总体评分（满分 10 分）

## 各维度检查
- [✅/⚠️/❌] 开头钩子：...
- [✅/⚠️/❌] 金句密度：...
- [✅/⚠️/❌] 段落节奏：...
- [✅/⚠️/❌] AI 痕迹：...
- [✅/⚠️/❌] 结尾动力：...

## 需要改进的地方（按优先级排序）
1. ...
2. ...

## 修改建议（可以直接用的改写）
...

文章内容：
{article}
"""
    return chat_once(system, [{"role": "user", "content": prompt}]) or "评审失败"


def de_ai_taste(article: str, intensity: str = "medium") -> Generator[str, None, None]:
    """去 AI 味改写（流式）"""
    from tools.de_ai import de_ai_stream
    yield from de_ai_stream(article, intensity)


def generate_article_images(article: str) -> tuple[str, list[dict]]:
    """扫描文章中的 [配图：描述] 标记，生成图片并替换。

    返回:
        (替换后的文章, [{marker, description, url, status}, ...])
    """
    from tools.image_gen import replace_markers_with_images as _replace
    return _replace(article)


def has_image_markers(article: str) -> bool:
    """检查文章中是否有配图标记"""
    import re
    return bool(re.search(r'\[配图[：:].*?\]', article))
