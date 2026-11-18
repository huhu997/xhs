# -*- coding: utf-8 -*-
"""封面安全区程序化核验：真正的内容（文字/墨线/深色块）必须落在 2.35:1 横带 ∩ 1:1 方块内。

两种判据：
  默认（dark 模式）—— 只把"深色像素"（亮度 < --luma，默认 150）算作内容。
      适合有底纹/渐变/纸面质感的封面（v2 插画风）：浅色纸面与投影被裁不影响可读性，
      只有文字和深色元素被切才算失败。
  --strict 模式 —— 沿用旧判据：与四角背景色差异 > 60 的像素都算内容。
      适合纯色底封面（v1 扁平风）。渐变底会整片误报，只在该模式下用。

用法:
  python check_cover.py [图片路径...]
  python check_cover.py --strict cover.png
  python check_cover.py --luma 170 cover.png     # 更敏感（浅灰文字也算内容）
"""
import pathlib
import sys

from PIL import Image

BASE = pathlib.Path(__file__).resolve().parent


def safe_area(W, H):
    """2.35:1 中心横带 ∩ 1:1 中心方块"""
    band_h = W / 2.35
    b0, b1 = (H - band_h) / 2, (H + band_h) / 2
    sq = min(W, H)
    s0, s1 = (W - sq) / 2, (W + sq) / 2
    return max(0, s0), min(W, s1), max(0, b0), min(H, b1)


def check(path, strict=False, luma=150, label=""):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    px = im.load()

    if strict:
        corners = [px[2, 2], px[W - 3, 2], px[2, H - 3], px[W - 3, H - 3]]
        bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))

        def is_content(p):
            return sum(abs(p[i] - bg[i]) for i in range(3)) > 60
        mode = f"strict（对四角底色 {bg} 的色差）"
    else:
        def is_content(p):
            return (p[0] * 299 + p[1] * 587 + p[2] * 114) / 1000 < luma
        mode = f"dark（亮度 < {luma} 视为内容）"

    xs, ys = [], []
    for y in range(0, H):
        for x in range(0, W):
            if is_content(px[x, y]):
                xs.append(x)
                ys.append(y)

    print(f"  {path.name}{('  [' + label + ']') if label else ''}  尺寸 {W}x{H}  判据: {mode}")
    if not xs:
        print(f"    ⚠ 未检测到内容像素（阈值过严？）")
        return None
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sx0, sx1, sy0, sy1 = safe_area(W, H)
    print(f"    内容包围盒  x {x0}–{x1}  y {y0}–{y1}")
    print(f"    2.35:1 横带 y {sy0:.0f}–{sy1:.0f} ｜ 1:1 方块 x {sx0:.0f}–{sx1:.0f}")
    print(f"    安全区(交集) x {sx0:.0f}–{sx1:.0f}  y {sy0:.0f}–{sy1:.0f}")

    ok, over = True, []
    if y0 < sy0:
        over.append(f"上溢 {sy0 - y0:.0f}px"); ok = False
    if y1 > sy1:
        over.append(f"下溢 {y1 - sy1:.0f}px"); ok = False
    if x0 < sx0:
        over.append(f"左溢 {sx0 - x0:.0f}px"); ok = False
    if x1 > sx1:
        over.append(f"右溢 {x1 - sx1:.0f}px"); ok = False
    if ok:
        print("    ✅ 内容全部在安全区内（2.35:1 与 1:1 裁剪均不切）")
    else:
        print("    ❌ " + " / ".join(over) + "（裁剪会切到）")
    return ok


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:]
    strict = "--strict" in argv
    argv = [a for a in argv if a != "--strict"]
    luma = 150
    for a in list(argv):
        if a.startswith("--luma"):
            luma = int(a.split("=", 1)[1] if "=" in a else 150)
            argv.remove(a)
    paths = argv or [str(BASE / "cover.png")]
    results = [check(pathlib.Path(p), strict, luma) for p in paths]
    sys.exit(0 if all(r is not False for r in results) else 2)
