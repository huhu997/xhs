#!/usr/bin/env bash
# AI视频工厂 · 一键渲染封装（剪辑/渲染角色调用）
# 用法: cd <工程目录> && bash <本文件绝对路径>/render.sh
# 已封装 hyperframes 的 ffmpeg/ffprobe 环境变量 + 本地 node_modules 查找，免新人撞 ffmpeg 墙。
set -e

# 清死代理（本机 HTTP_PROXY 指向 127.0.0.1:1080 但没起代理，会卡死 npm/网络）
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

# hyperframes 只认这两个环境变量绝对路径，不认 PATH / 不认 require
export HYPERFRAMES_FFMPEG_PATH="${HYPERFRAMES_FFMPEG_PATH:-C:/Users/admin/.cursor/extensions/kilocode.kilo-code-7.3.1-win32-x64/bin/ffmpeg.exe}"
export HYPERFRAMES_FFPROBE_PATH="${HYPERFRAMES_FFPROBE_PATH:-C:/Users/admin/ffprobe_tmp/node_modules/ffprobe-static/bin/win32/x64/ffprobe.exe}"

echo "ffmpeg : $HYPERFRAMES_FFMPEG_PATH"
echo "ffprobe: $HYPERFRAMES_FFPROBE_PATH"

if [ -x "./node_modules/.bin/hyperframes" ]; then
  echo ">> 用工程本地 hyperframes 渲染"
  ./node_modules/.bin/hyperframes render "$@"
elif command -v hyperframes >/dev/null 2>&1; then
  echo ">> 用全局 hyperframes 渲染"
  hyperframes render "$@"
else
  echo "ERROR: 未找到 hyperframes。请先在该工程目录执行: npm install hyperframes@0.8.230" >&2
  exit 1
fi
