"""写作阶段：根据大纲和素材撰写正文"""

from typing import Generator
from core.llm import chat_stream
from core.memory import build_system_prompt
from core.thoughts import get_relevant

SOUL_WRITING = """你是一个公众号文章写手。你的任务是写出读者愿意转发到朋友圈的文章。

## ⛔ 绝对禁止（违反任意一条，文章直接不合格）

1. **禁止编造数据**——不要写"调查显示""数据显示""研究表明""XX%的人"，除非素材里明确给出了具体出处。没有真实来源的数据一律不写。
2. **禁止 AI 过渡句**——不要用以下句式：
   - "你知道吗？"
   - "为什么？"（自问自答）
   - "让我们来看看"
   - "数据也证明了这一点"
   - "这不是偶然"
   - "更扎心的是"
   - 任何以"问句"开启下一段的套路
3. **禁止鸡汤金句**——不要写"XX是最好的XX""忙碌是最大的XX"这种看似有道理实则空洞的对仗句。金句必须来自素材中的具体故事或观察，不能是凭空造出来的"道理"。
4. **禁止三段式结构**——不要用"原因一/原因二/原因三"或"首先/其次/最后"来组织段落。每个段落应该是一个独立的场景或故事，自然推进。
5. **禁止编造人物**——素材里没有给出具体人物时，不要编"我有一个朋友""同事老张""邻居小王"。用"你"或"有人"代替。
6. **禁止正确废话**——不要写"职场人都知道""谁还没经历过呢""成年人的世界没有容易二字"这种放之四海而皆准的废话。

## ✅ 必须做到的写作原则

1. **场景先行**——每一段从一个具体的画面或场景开始，让读者"看到"而不是"被告诉"。先场景，后感受。
2. **用细节代替形容词**——不要写"他很沮丧"，写"他盯着屏幕发了五分钟呆，然后关掉了文档"。不要写"压力很大"，写"凌晨两点还在改第六版方案"。
3. **每段只讲一件事**——一个段落就是一个独立的场景，讲完就换。手机阅读，每段不超过 3 行。
4. **开头必须有画面**——前 100 字必须是一个具体的时间、地点、人物、动作构成的场景，不能是道理或感慨。
5. **结尾给转发理由**——要么让读者觉得"说的是我"，要么给一个可以@朋友的理由。
6. **口语化但有节制**——用"了""吗""吧"收尾的短句，不用成语堆砌，不用生僻词。但不要刻意模仿东北话或网络梗。
"""


def _has_image_markers(outline: str) -> bool:
    """检查大纲或素材中是否已经包含配图标记"""
    return "[配图" in outline


def write_article(
    topic: str,
    outline: str,
    material: str = "",
    soul: str = "",
) -> Generator[str, None, None]:
    """根据大纲撰写正文（流式）"""
    system_parts = [SOUL_WRITING]
    if soul:
        system_parts.append(f"\n## 账号风格要求\n{soul}")
    system_parts.append(build_system_prompt(""))
    system = "\n\n".join(system_parts)

    # 配图说明：如果大纲里还没有配图标记，提醒 AI 插入
    image_note = ""
    if not _has_image_markers(outline) and not _has_image_markers(material):
        image_note = """
- 【配图】在适合配图的地方插入 `[配图：详细描述画面的具体场景、风格]` 占位符，至少 2 处。
  示例：`[配图：一个年轻人深夜坐在电脑前，屏幕上显示着银行卡余额，表情沮丧]`
  `[配图：手机支付账单截图特写，突出各种小额消费项目]`
"""

    material_block = f"\n\n## 素材（必须融入文章）\n{material}" if material else ""
    thoughts_block = get_relevant(topic)
    if thoughts_block:
        thoughts_block += "\n\n⚠️ 以上是作者的真实经历，必须优先融入文章，禁止编造类似故事。\n"

    prompt = f"""请根据以下信息撰写一篇完整的公众号文章。

## 主题
{topic}

## 确认的大纲
{outline}{material_block}{thoughts_block}

要求：
- 字数 800-1500 字
- 保留大纲中的结构，但行文要自然
- 素材必须融入，但不能生硬堆砌
- 语言口语化、有节奏感{image_note}
- 直接输出文章正文，不要加「以下是文章」之类的说明
"""
    yield from chat_stream(system, [{"role": "user", "content": prompt}])
