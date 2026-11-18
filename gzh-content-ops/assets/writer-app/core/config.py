"""环境配置管理：加载 .env，校验必填项，全局可访问"""

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent


def load():
    load_dotenv(ROOT_DIR / ".env")

    # 代理（非全局，各模块按需使用）
    proxy = os.getenv("HTTP_PROXY", "") or ""
    if proxy:
        os.environ["HTTP_PROXY"] = proxy
    https_proxy = os.getenv("HTTPS_PROXY", "") or ""
    if https_proxy:
        os.environ["HTTPS_PROXY"] = https_proxy

    return {
        "DEEPSEEK_API_KEY": _require("DEEPSEEK_API_KEY"),
        "SILICONFLOW_API_KEY": os.getenv("SILICONFLOW_API_KEY", ""),
        "PEXELS_API_KEY": os.getenv("PEXELS_API_KEY", ""),
        "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
        "SILICONFLOW_BASE_URL": "https://api.siliconflow.cn/v1",
        "HTTP_PROXY": proxy,
        "HTTPS_PROXY": https_proxy,
        "ROOT_DIR": ROOT_DIR,
    }


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise RuntimeError(
            f"❌ 缺少必填配置 {key}，请在 .env 文件中设置"
        )
    return val
