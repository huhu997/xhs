"""LLM 调用层：DeepSeek 流式调用 + SiliconFlow 降级

使用方式：
  for chunk in chat_stream(system_prompt, messages):
      print(chunk)

  result = chat_once(system_prompt, messages)  # 返回完整字符串
"""

import logging
from typing import Generator, Optional
from openai import OpenAI

from .config import load as load_config

logger = logging.getLogger(__name__)

cfg = load_config()


def _client(api_key: str, base_url: str) -> OpenAI:
    """构建 OpenAI 客户端。代理通过环境变量自动生效，无需额外配置。"""
    return OpenAI(api_key=api_key, base_url=base_url, timeout=60)


def _deepseek_models() -> list[str]:
    return ["deepseek-chat", "deepseek-ai/DeepSeek-V3"]


# ── 流式调用（带降级） ──

def chat_stream(
    system_prompt: str,
    messages: list[dict],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Generator[str, None, None]:
    """流式调用 DeepSeek，失败自动降级至硅基流动。"""
    # 第 1 轮：DeepSeek
    tried_deepseek = False
    for chunk in _try_stream(cfg["DEEPSEEK_API_KEY"], cfg["DEEPSEEK_BASE_URL"],
                              model, system_prompt, messages, temperature, max_tokens):
        tried_deepseek = True
        yield chunk

    if tried_deepseek:
        return  # DeepSeek 成功

    # 降级：硅基流动
    if not cfg["SILICONFLOW_API_KEY"]:
        yield "\n> ❌ DeepSeek 不可用且未配置备用 API\n"
        return

    yield "\n> ⚠️ DeepSeek 不可用，切换硅基流动...\n\n"
    for chunk in _try_stream(cfg["SILICONFLOW_API_KEY"], cfg["SILICONFLOW_BASE_URL"],
                              "deepseek-ai/DeepSeek-V3", system_prompt, messages,
                              temperature, max_tokens):
        yield chunk


def _try_stream(api_key, base_url, model, system_prompt, messages, temperature, max_tokens) -> Generator[str, None, None]:
    """尝试一次流式调用，成功就 yield 所有内容，失败则返回（不 yield 任何内容）。"""
    try:
        client = _client(api_key, base_url)
        msgs = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model=model,
            messages=msgs,
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.warning(f"LLM 流式调用失败 ({base_url}): {e}")


# ── 非流式调用（带降级） ──

def chat_once(
    system_prompt: str,
    messages: list[dict],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Optional[str]:
    """非流式调用，返回完整文本。失败返回 None。"""
    # 第 1 轮：DeepSeek
    result = _try_once(cfg["DEEPSEEK_API_KEY"], cfg["DEEPSEEK_BASE_URL"],
                        model, system_prompt, messages, temperature, max_tokens)
    if result is not None:
        return result

    # 降级：硅基流动
    if not cfg["SILICONFLOW_API_KEY"]:
        logger.error("DeepSeek 失败且未配置备用 API")
        return None

    logger.warning("降级至硅基流动")
    return _try_once(cfg["SILICONFLOW_API_KEY"], cfg["SILICONFLOW_BASE_URL"],
                      "deepseek-ai/DeepSeek-V3", system_prompt, messages,
                      temperature, max_tokens)


def _try_once(api_key, base_url, model, system_prompt, messages, temperature, max_tokens) -> Optional[str]:
    """尝试一次非流式调用，成功返回文本，失败返回 None。"""
    try:
        client = _client(api_key, base_url)
        msgs = [{"role": "system", "content": system_prompt}] + messages
        resp = client.chat.completions.create(
            model=model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.warning(f"LLM 非流式调用失败 ({base_url}): {e}")
        return None
