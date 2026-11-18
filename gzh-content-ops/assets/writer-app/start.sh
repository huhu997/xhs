#!/usr/bin/env bash
set -e

echo "============================================"
echo "  📝 公众号写作工作台 - 启动中..."
echo "============================================"
echo ""

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "❌ 未检测到 Python3，请先安装 Python 3.10+"
    exit 1
fi
echo "✅ Python 已就绪"

# 检查 .env
if [ ! -f ".env" ]; then
    echo "❌ 缺少 .env 配置文件"
    echo "   请复制 .env.example 为 .env 并填入你的 DeepSeek API Key"
    exit 1
fi

if grep -q "sk-your-key" .env 2>/dev/null; then
    echo "❌ .env 中的 DEEPSEEK_API_KEY 还是默认占位符"
    echo "   请编辑 .env 填入你的真实 API Key"
    exit 1
fi
echo "✅ 配置已就绪"

# 安装依赖
echo ""
echo "📦 检查依赖..."
pip3 install -r requirements.txt -q
echo "✅ 依赖已就绪"

# 启动
echo ""
echo "🚀 正在启动 Streamlit..."
echo "   浏览器打开后如果空白，请稍等几秒"
echo "   按 Ctrl+C 停止服务"
echo ""
exec streamlit run app.py --server.port 8501 --browser.serverAddress localhost
