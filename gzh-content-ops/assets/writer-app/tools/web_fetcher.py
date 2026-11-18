"""网页内容抓取工具"""

import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_text(url: str, max_len: int = 4000) -> str:
    """抓取网页正文文本"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:max_len] if text else "未能提取到正文"
    except Exception as e:
        logger.warning(f"网页抓取失败 {url}: {e}")
        return ""
