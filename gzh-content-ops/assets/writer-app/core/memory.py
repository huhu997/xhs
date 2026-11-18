"""分层记忆系统

三层架构：
  long_term.md  — 用户确认过的长期风格偏好（手动写入）
  short_term.log — 近期交互反馈（自动追加，超 7 天自动裁剪）
  rules.md      — 用户明确说过的禁用/偏好规则（function calling 写入）
"""

import os
import datetime
from pathlib import Path
from typing import Optional

from .config import load as load_config

cfg = load_config()
MEMORY_DIR = Path(cfg["ROOT_DIR"]) / "memory"


def ensure_dirs():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    for name in ["long_term.md", "short_term.log", "rules.md"]:
        fpath = MEMORY_DIR / name
        if not fpath.exists():
            fpath.write_text("", encoding="utf-8")


# ── 长期记忆 ──

def read_long_term() -> str:
    return _read("long_term.md")


def write_long_term(text: str):
    _write("long_term.md", text)


def append_long_term(line: str):
    """追加一条长期记忆（带时间戳）"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    content = read_long_term()
    content += f"\n[{now}] {line}\n"
    write_long_term(content)


# ── 短期日志（自动过期） ──

def read_short_term(max_lines: int = 5) -> str:
    lines = _read("short_term.log").strip().split("\n")
    lines = [l for l in lines if l.strip()]
    # 过滤掉超过 7 天的
    cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
    recent = []
    for line in lines:
        try:
            date_str = line[1:11]  # [2026-06-07 ...]
            line_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if line_date >= cutoff:
                recent.append(line)
        except (ValueError, IndexError):
            recent.append(line)
    return "\n".join(recent[-max_lines:])


def append_short_term(line: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"[{now}] {line}"
    content = _read("short_term.log")
    content += entry + "\n"
    # 自动截断超过 200 行的旧日志
    lines = content.strip().split("\n")
    if len(lines) > 200:
        lines = lines[-200:]
    _write("short_term.log", "\n".join(lines) + "\n")


# ── 规则记忆 ──

def read_rules() -> str:
    return _read("rules.md")


def append_rule(rule: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    content = _read("rules.md")
    content += f"\n[{now}] {rule}\n"
    _write("rules.md", content)


# ── 组装 system prompt ──

def build_system_prompt(soul_text: str) -> str:
    ensure_dirs()
    long_term = read_long_term()
    rules = read_rules()
    short_term = read_short_term()

    parts = [soul_text.strip()]
    if long_term.strip():
        parts.append(f"\n## 长期记忆\n{long_term.strip()}")
    if rules.strip():
        parts.append(f"\n## 写作规则\n{rules.strip()}")
    if short_term.strip():
        parts.append(f"\n## 近期反馈\n{short_term.strip()}")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    parts.append(f"\n## 当前时间\n{now}")
    return "\n\n".join(parts)


# ── 内部 ──

def _read(name: str) -> str:
    ensure_dirs()
    fpath = MEMORY_DIR / name
    if fpath.exists():
        return fpath.read_text(encoding="utf-8")
    return ""


def _write(name: str, content: str):
    ensure_dirs()
    (MEMORY_DIR / name).write_text(content, encoding="utf-8")
