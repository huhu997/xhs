"""大纲阶段：生成大纲 → 用户确认/修改 → 进入写作"""

from typing import Generator
from core.llm import chat_stream, chat_once
from core.memory import build_system_prompt

SOUL_OUTLINE = """你是一个公众号文章结构设计师。

你的任务是根据选题和素材，设计出让人忍不住读完的文章结构。

结构设计原则：
1. 开头 100 字决定读者是否划走——必须有钩子
2. 正文层层递进，每段都要有「继续读下去」的理由
3. 结尾必须有转发动力——要么让人认同，要么让人想吵
4. 好文章 = 好故事 × 好逻辑 × 好金句
"""


def generate_outline(topic: str, material: str = "", soul: str = "") -> Generator[str, None, None]:
    """根据话题和素材生成大纲（流式）"""
    system_parts = [SOUL_OUTLINE]
    if soul:
        system_parts.append(f"\n## 账号风格要求\n{soul}")
    system_parts.append(build_system_prompt(""))  # 记忆部分
    system = "\n\n".join(system_parts)

    material_block = f"\n\n## 可用素材\n{material}" if material else ""

    prompt = f"""请为主题「{topic}」设计一份详细的公众号文章大纲。{material_block}

要求：
- 标题候选（至少 3 个，不同风格）
- 开头钩子（用什么方式抓住注意力）
- 正文结构（2-4 个核心段落，每段说清楚要点）
- 金句预埋位（至少标注 2 处需要金句的位置）
- 结尾（转发动力 + 互动引导）
- 预估字数

你的大纲要让人看了就觉得「这篇文章值得写」。"""
    yield from chat_stream(system, [{"role": "user", "content": prompt}])
