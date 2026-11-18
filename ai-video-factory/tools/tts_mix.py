#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI视频工厂 · 本地零成本 TTS + 混音工具（剪辑角色严过剪调用）

依赖: pip install edge-tts
特点: 用微软免费语音(edge-tts)，无需 API Key，零成本。

用法:
  # 只生成旁白
  python tts_mix.py --text "旁白稿" --out voice.mp3

  # 把旁白混进静音成片（可选叠 BGM）
  python tts_mix.py --text "旁白稿" --video silent.mp4 --bgm bgm.mp3 --out final.mp4
"""
import argparse
import asyncio
import os
import shutil
import subprocess
import sys

FFMPEG = (
    os.environ.get("HYPERFRAMES_FFMPEG_PATH")
    or shutil.which("ffmpeg")
    or r"C:/Users/admin/.cursor/extensions/kilocode.kilo-code-7.3.1-win32-x64/bin/ffmpeg.exe"
)
# 男声(宣言/搞钱调性)；女声换 zh-CN-XiaoxiaoNeural；更多: edge-tts --list-voices
DEFAULT_VOICE = "zh-CN-YunxiNeural"


async def tts(text: str, out_mp3: str, voice: str):
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_mp3)


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description="本地零成本 TTS + 混音")
    ap.add_argument("--text", required=True, help="旁白文本")
    ap.add_argument("--voice", default=DEFAULT_VOICE, help="edge-tts 语音名")
    ap.add_argument("--video", help="静音 mp4，把音频混进音轨")
    ap.add_argument("--bgm", help="背景音乐 mp3，音量自动压低")
    ap.add_argument("--bgm-vol", default="0.12", help="BGM 音量(默认 0.12)")
    ap.add_argument("--out", required=True, help="输出文件")
    args = ap.parse_args()

    out_dir = os.path.dirname(args.out) or "."
    os.makedirs(out_dir, exist_ok=True)
    tmp_voice = os.path.join(out_dir, "_tts_voice_tmp.mp3")

    print(">> 生成旁白中...")
    asyncio.run(tts(args.text, tmp_voice, args.voice))

    if not args.video:
        shutil.move(tmp_voice, args.out)
        print("✅ 旁白已生成:", args.out)
        return

    if args.bgm:
        fc = (
            f"[0:a]volume=1.0[a];"
            f"[1:a]volume=1.0[v];"
            f"[2:a]volume={args.bgm_vol}[b];"
            f"[v][b]amix=inputs=2:duration=first:dropout_transition=0[mix];"
            f"[a][mix]amix=inputs=2:duration=first:dropout_transition=0[out]"
        )
        cmd = [
            FFMPEG, "-y", "-i", args.video, "-i", tmp_voice, "-i", args.bgm,
            "-filter_complex", fc,
            "-map", "0:v", "-map", "[out]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", args.out,
        ]
    else:
        fc = "[1:a]volume=1.0[a]"
        cmd = [
            FFMPEG, "-y", "-i", args.video, "-i", tmp_voice,
            "-filter_complex", fc,
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", args.out,
        ]
    run(cmd)
    os.remove(tmp_voice)
    print("✅ 有声成片已生成:", args.out)


if __name__ == "__main__":
    main()
