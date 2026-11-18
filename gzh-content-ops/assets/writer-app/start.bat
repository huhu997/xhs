@echo off
chcp 65001 >nul
title 公众号写作工作台

echo ============================================
echo   📝 公众号写作工作台 - 启动中...
echo ============================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)
echo ✅ Python 已就绪

:: 检查 .env
if not exist ".env" (
    echo ❌ 缺少 .env 配置文件
    echo    请复制 .env.example 为 .env 并填入你的 DeepSeek API Key
    pause
    exit /b 1
)

:: 检查 API Key（粗略判断是否还是占位符）
findstr /C:"sk-your-key" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ .env 中的 DEEPSEEK_API_KEY 还是默认占位符
    echo    请编辑 .env 填入你的真实 API Key
    pause
    exit /b 1
)
echo ✅ 配置已就绪

:: 安装/更新依赖
echo.
echo 📦 检查依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖已就绪

:: 启动
echo.
echo 🚀 正在启动 Streamlit...
echo    浏览器打开后如果空白，请稍等几秒
echo    按 Ctrl+C 停止服务
echo.
streamlit run app.py --server.port 8501 --browser.serverAddress localhost

pause
