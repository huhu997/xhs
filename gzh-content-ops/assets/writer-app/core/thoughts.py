"""个人想法库 — 按月存储，按标签检索

按月拆分文件（thoughts/2026-06.md），不会越来越臃肿。
每条记录带时间戳和标签，写作时按话题自动匹配注入。
支持附带图片（thoughts/images/）。
"""

import datetime
import re
import shutil
from pathlib import Path

from .config import load as load_config

cfg = load_config()
THOUGHTS_DIR = Path(cfg["ROOT_DIR"]) / "thoughts"
IMAGES_DIR = THOUGHTS_DIR / "images"


def ensure_dir():
    THOUGHTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _month_file(year: int, month: int) -> Path:
    return THOUGHTS_DIR / f"{year}-{month:02d}.md"


def save_image(source_path: str | Path) -> str | None:
    """将图片复制到 thoughts/images/，返回 Markdown 图片引用

    Args:
        source_path: 上传图片的临时路径

    Returns:
        Markdown 格式的图片引用，如 ![描述](thoughts/images/xxx.png)
        失败则返回 None
    """
    ensure_dir()
    try:
        src = Path(source_path)
        if not src.exists():
            return None
        ext = src.suffix.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            ext = ".png"
        now = datetime.datetime.now()
        filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{src.stem[:20]}{ext}"
        dst = IMAGES_DIR / filename
        shutil.copy2(src, dst)
        # 存相对路径，写入文章后在公众号排版时也能引用
        return f"![配图]({dst.relative_to(Path(cfg['ROOT_DIR']))})"
    except Exception as e:
        return None


def save_image_from_bytes(data: bytes, original_name: str) -> str | None:
    """从字节数据保存图片到 thoughts/images/，返回 Markdown 图片引用"""
    ensure_dir()
    try:
        ext = Path(original_name).suffix.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            ext = ".png"
        safe_name = re.sub(r'[^a-zA-Z0-9_\-.]+', '_', Path(original_name).stem)[:20]
        now = datetime.datetime.now()
        filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{safe_name}{ext}"
        dst = IMAGES_DIR / filename
        dst.write_bytes(data)
        return f"![配图]({dst.relative_to(Path(cfg['ROOT_DIR']))})"
    except Exception as e:
        return None


def append_thought(tags: str, content: str, image_md: str = ""):
    """追加一条想法，带时间戳和标签

    Args:
        tags: 逗号分隔的标签
        content: 文字内容
        image_md: 可选的 Markdown 图片引用，会追加到内容末尾
    """
    ensure_dir()
    now = datetime.datetime.now()
    ts = now.strftime("%Y-%m-%d %H:%M")
    fpath = _month_file(now.year, now.month)
    full_content = content
    if image_md:
        full_content += f"\n\n{image_md}"
    entry = f"\n## {ts}\n标签：{tags}\n{full_content}\n"
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(entry)


def read_current_month() -> str:
    """读取当月所有想法"""
    now = datetime.datetime.now()
    return read_month(now.year, now.month)


def read_month(year: int, month: int) -> str:
    """读取指定月的想法"""
    fpath = _month_file(year, month)
    if fpath.exists():
        return fpath.read_text(encoding="utf-8")
    return ""


def list_months() -> list[str]:
    """返回有记录的月份列表，倒序，如 ['2026-06', '2026-05']"""
    ensure_dir()
    files = sorted(THOUGHTS_DIR.glob("*.md"), reverse=True)
    return [f.stem for f in files]


def get_relevant(topic: str, max_months: int = 3) -> str:
    """按话题标签匹配，返回最近 N 个月相关的想法

    读取最近 max_months 个月的文件，提取所有标签，
    检查是否有标签出现在话题文本中（子串匹配）。
    返回格式化的 Markdown 文本，或空字符串。
    """
    ensure_dir()
    all_files = sorted(THOUGHTS_DIR.glob("*.md"), reverse=True)[:max_months]
    if not all_files:
        return ""

    # 第一步：收集所有标签 → 条目映射
    tag_to_entries: dict[str, list[str]] = {}
    for fpath in all_files:
        text = fpath.read_text(encoding="utf-8")
        # "## " 前可能有换行，统一分割
        entries = re.split(r'\n(?=## \d{4})', text)
        for entry in entries:
            if not entry.strip():
                continue
            tag_match = re.search(r'标签[：:](.*?)(?:\n|$)', entry)
            if not tag_match:
                continue
            tags_str = tag_match.group(1)
            for t in re.split(r'[，,\s、]+', tags_str):
                t = t.strip()
                if len(t) >= 2:
                    tag_to_entries.setdefault(t, []).append(entry.strip())

    # 第二步：检查标签是否与话题匹配（子串或子序列）
    matched: set[str] = set()
    for tag, entries in tag_to_entries.items():
        if tag in topic or _is_subseq(tag, topic):
            for e in entries:
                matched.add(e)

    if not matched:
        return ""

    header = f"## 作者的真实想法（与「{topic}」相关，必须优先使用）"
    body = "\n\n---\n\n".join(matched)
    return f"\n\n{header}\n\n{body}\n"


def _is_subseq(tag: str, topic: str) -> bool:
    """检查 tag 的字符是否按顺序出现在 topic 中（子序列匹配，不必连续）

    例：_is_subseq("存钱", "为什么你总是存不下钱") → True
    """
    i = 0
    for ch in topic:
        if ch == tag[i]:
            i += 1
            if i == len(tag):
                return True
    return False
