"""图片生成工具

三级策略：
1. 硅基流动 API（需 SILICONFLOW_API_KEY + 余额）
2. Pexels 免费 API（需 PEXELS_API_KEY，可选配置）
3. Picsum.photos（免 API，兜底，出真实照片）

Pexels 免费 key 注册：https://www.pexels.com/api/
Picsum 是 Unsplash 团队维护的免费随机图片服务。
"""

import logging
import time
import re
import hashlib
from typing import Optional
from openai import OpenAI
import requests

from core.config import load as load_config

logger = logging.getLogger(__name__)
cfg = load_config()

SILICONFLOW_MODELS = [
    "Tongyi-MAI/Z-Image-Turbo",
    "Qwen/Qwen-Image",
]

PEXELS_API_KEY = cfg.get("PEXELS_API_KEY", "") or ""


def generate_image(prompt: str, size: str = "1024x1024") -> Optional[str]:
    """生成一张图片。三级策略递进。"""
    # 1. 硅基流动
    url = _try_siliconflow(prompt, size)
    if url:
        return url

    # 2. Pexels
    if PEXELS_API_KEY:
        url = _try_pexels(prompt)
        if url:
            logger.info("使用 Pexels 配图")
            return url

    # 3. Picsum 兜底
    url = _try_picsum(prompt)
    if url:
        logger.info("使用 Picsum 兜底配图")
        return url

    return None


def _try_siliconflow(prompt: str, size: str) -> Optional[str]:
    """尝试硅基流动 API"""
    api_key = cfg.get("SILICONFLOW_API_KEY", "")
    if not api_key:
        return None
    client = OpenAI(api_key=api_key, base_url=cfg["SILICONFLOW_BASE_URL"], timeout=60)
    for model in SILICONFLOW_MODELS:
        try:
            logger.info(f"硅基流动尝试: {model}")
            resp = client.images.generate(model=model, prompt=prompt, n=1, size=size)
            url = resp.data[0].url
            if url:
                return url
        except Exception as e:
            logger.warning(f"{model} 失败: {str(e)[:60]}")
            continue
    return None


def _try_pexels(prompt: str) -> Optional[str]:
    """用 Pexels API 搜索配图（免费，每小时 200 次）"""
    keyword = _extract_keyword_en(prompt)
    if not keyword:
        return None
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": keyword, "per_page": 5, "orientation": "landscape"},
            headers={"Authorization": PEXELS_API_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            photos = resp.json().get("photos", [])
            if photos:
                import random
                photo = random.choice(photos)
                return photo.get("src", {}).get("large")
    except Exception as e:
        logger.warning(f"Pexels 失败: {e}")
    return None


def _try_picsum(prompt: str) -> Optional[str]:
    """Picsum.photos 兜底（Unsplash 团队维护，免 API，返回真实照片）"""
    seed = _prompt_to_seed(prompt)
    # 返回 800x600 图片，seed 确保同一 prompt 得到同一张图
    return f"https://picsum.photos/seed/{seed}/800/600"


def _extract_keyword_en(text: str) -> str:
    """从中文提示词中提取英文搜索关键词"""
    SCENE_MAP = {
        "深夜": "night",
        "电脑": "desk computer",
        "手机": "smartphone",
        "账单": "bill receipt finance",
        "钱": "money saving",
        "咖啡": "coffee",
        "奶茶": "tea drink",
        "办公": "office workspace",
        "家": "home living room",
        "城市": "city street",
        "年轻人": "young person",
        "悲伤": "sad lonely",
        "开心": "happy smile",
        "焦虑": "anxious stressed",
        "交易": "trading stocks",
        "股票": "stock market chart",
        "数据": "data analytics chart",
        "图表": "chart graph",
        "对比": "comparison contrast",
        "成功": "success achievement",
        "失败": "failure loss",
        "学习": "study reading learning",
        "工作": "work office",
        "健康": "health fitness",
        "旅行": "travel vacation",
        "休息": "rest relax break",
        "工位": "office desk workspace",
        "离职": "resign good bye office",
        "辞职": "resign quit job",
        "会议": "meeting conference",
        "熬夜": "night work late",
    }
    for cn, en in SCENE_MAP.items():
        if cn in text:
            return en
    return ""


def _prompt_to_seed(prompt: str) -> str:
    """将提示词转为 picsum seed，确保同一提示出同一张图"""
    return hashlib.md5(prompt.encode()).hexdigest()[:12]


# ── 标记处理 ──

def extract_image_markers(text: str) -> list[str]:
    """提取文章中所有 [配图：...] 标记"""
    return re.findall(r'\[配图[：:](.*?)\]', text)


def strip_image_markers(text: str) -> str:
    """移除所有的 [配图：...] 标记，替换为空行（用户不生成图片时用）"""
    return re.sub(r'\s*\[配图[：:].*?\]\s*', '\n\n', text)


def replace_markers_with_images(text: str, delay: float = 1.0) -> tuple[str, list[dict]]:
    """扫描文章中的 [配图：描述] 标记，生成图片并替换。

    返回:
        (替换后的文章, [{marker, description, url, status}, ...])
    """
    markers = list(re.finditer(r'\[配图[：:](.*?)\]', text))
    if not markers:
        return text, []

    results = []
    for i, m in enumerate(markers):
        desc = m.group(1).strip()
        logger.info(f"生成配图 {i+1}/{len(markers)}: {desc[:50]}")

        url = generate_image(desc[:200])
        if url:
            replacement = f"\n\n![{desc}]({url})\n\n"
            results.append({"marker": m.group(0), "description": desc, "url": url, "status": "ok"})
        else:
            replacement = f"\n\n> 🖼️ 配图生成失败：{desc}\n\n"
            results.append({"marker": m.group(0), "description": desc, "url": "", "status": "fail"})

        text = text.replace(m.group(0), replacement, 1)
        if i < len(markers) - 1:
            time.sleep(delay)

    return text, results
