"""去 AI 味引擎：三级力度，流式输出"""

from typing import Generator
from core.llm import chat_stream
from core.memory import build_system_prompt

PROMPT_LIGHT = """你是一个文稿编辑。请对以下文本做轻度去 AI 味处理：

仅做两项操作：
1. 删除 AI 高频禁用词（此外、至关重要、彰显、契合、优化提升等）
2. 把长句拆短

保持原文长度和内容不变，不要重写。"""

PROMPT_MEDIUM = """你是一个专业文稿编辑。请对以下文本做中度去 AI 味处理：

修改范围：
1. 删除 AI 高频禁用词（此外、至关重要、彰显、契合、优化提升、收获热度等）
2. 拆解「不仅是…更是…」「不单单只是…核心在于…」这类递进句式
3. 把「为达成这一目标」改成「为达成目标」等啰嗦书面语缩简
4. 删除无意义加粗和无依据的「业内人士认为」「数据表明」
5. 将结尾的空洞展望改成具体行动或事实

不要缩短文章长度，不要改变核心观点和信息。"""

PROMPT_HEAVY = """你是一个专业文稿编辑。请对以下文本做重度去 AI 味处理（全面真人化改写）：

修改范围：
1. 执行中度去味所有操作
2. 句式长短交替：加入短句、口语化表达
3. 适当加入第一人称观点（「说实话」「我总觉得」）
4. 删除模板化「现存困境+未来展望」段落
5. 替换所有破折号抒情句为直接陈述
6. 避免「三点式」排比，改为自然叙述
7. 加入具体感（有数字的保留数字，没数字的场景化）

不要缩短文章长度，不要丢失核心信息和观点。"""

PROMPTS = {
    "light": PROMPT_LIGHT,
    "medium": PROMPT_MEDIUM,
    "heavy": PROMPT_HEAVY,
}


def de_ai_stream(text: str, intensity: str = "medium") -> Generator[str, None, None]:
    """流式去 AI 味"""
    prompt = PROMPTS.get(intensity, PROMPT_MEDIUM)
    system = build_system_prompt("")
    prompt_full = f"{prompt}\n\n文本：\n{text}"
    yield from chat_stream(system, [{"role": "user", "content": prompt_full}])
