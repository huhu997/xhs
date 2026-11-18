"""选题阶段：热点追踪、角度生成、竞品分析"""

from core.llm import chat_stream, chat_once
from core.memory import build_system_prompt

SOUL_TOPIC = """你是一个公众号选题策划专家。你的任务是帮作者找到好的选题和切入角度。

你的核心原则：
1. 选题 = 用户想看的 × 你能写的 × 还没被写烂的
2. 角度比话题更重要——同一个话题，换一个切入角度就是一篇新文章
3. 好的选题要让人产生「这说的不就是我吗」的代入感
"""


def generate_angles(topic: str) -> str:
    """围绕一个话题生成 3-5 个切入角度"""
    system = build_system_prompt(SOUL_TOPIC)
    prompt = f"""围绕「{topic}」这个主题，生成 3-5 个公众号选题角度。

每个角度要求：
- 一个吸引人的标题候选
- 一句话说清「这篇文章帮读者解决什么问题」
- 目标读者是谁
- 独特的切入视角（不要烂大街的角度）

输出格式（Markdown）：

## 角度一：<标题>

**解决的问题：** ...
**目标读者：** ...
**独特视角：** ...

## 角度二：...
"""
    return chat_once(system, [{"role": "user", "content": prompt}]) or "生成失败"


def analyze_hot_topic(url: str) -> str:
    """分析一篇热点文章，拆解它为什么能火"""
    from tools.web_fetcher import fetch_text

    content = fetch_text(url)
    if not content:
        return "抓取失败"

    system = build_system_prompt(SOUL_TOPIC)
    prompt = f"""分析以下文章为什么能吸引读者，拆解：

1. 标题为什么吸引人
2. 开头怎么抓住注意力的
3. 文章结构（起承转合）
4. 金句/亮点摘录
5. 如果让你写同主题，你会怎么切入（给出 2 个不同的角度）

文章内容：
{content[:4000]}
"""
    return chat_once(system, [{"role": "user", "content": prompt}]) or "分析失败"
