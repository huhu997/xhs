# -*- coding: utf-8 -*-
"""公众号稿子违规风险排查（薄封装，规则全部来自 _wx_read/riskcheck.py 单一词表）

⚠️ 本文件不再自己维护禁用词——历史上这里和 audit_images.py 各有一份词表，
   两份会漂移（改了一处漏另一处）。现在统一由 riskcheck.py 提供，
   要加词改 `_wx_read/riskcheck_extra.json`，不要改这里。

默认扫描（沿用原行为）：article.md / upload_article.py / gemini-prompts.md
用法:
  python audit_risk.py                       # 扫上述三个文件
  python audit_risk.py 别的文件.md            # 扫指定文件
  python audit_risk.py --dir .                # 扫整个目录
  python audit_risk.py --strict               # WARN 也算失败
  python upload_article.py --dry-run 的产物 | python audit_risk.py --stdin   # 扫最终产物

退出码：0 无 BLOCK / 2 有 BLOCK
"""
import pathlib
import sys

sys.path.insert(0, r"F:\桌面\zcode工作区\_wx_read")
from riskcheck import main as risk_main  # noqa: E402

BASE = pathlib.Path(__file__).resolve().parent
DEFAULT_TARGETS = ["article.md", "upload_article.py", "gemini-prompts.md"]


if __name__ == "__main__":
    argv = sys.argv[1:]
    # 没给任何目标时，用本目录的默认三件套
    if not argv or argv[0].startswith("-"):
        argv = [str(BASE / t) for t in DEFAULT_TARGETS if (BASE / t).exists()] + argv
    sys.argv = [sys.argv[0]] + argv
    sys.exit(risk_main())
