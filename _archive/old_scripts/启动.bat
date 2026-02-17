@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 飞书交互版黄金监控系统
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python 已安装
echo.

REM 检查 .env 文件
if not exist .env (
    echo ❌ 未找到 .env 文件
    echo.
    echo 请创建 .env 文件并添加以下内容：
    echo FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-key
    echo.
    pause
    exit /b 1
)

echo ✅ 配置文件已找到
echo.

REM 检查依赖
echo 📦 检查依赖包...
pip show ccxt >nul 2>&1
if errorlevel 1 (
    echo ⚠️  缺少依赖包，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo ✅ 依赖包已安装
echo.

REM 选择运行模式
echo 请选择运行模式：
echo.
echo 1. 测试飞书连接 (test_feishu.py)
echo 2. 测试 OKX 连接 (okx_monitor.py)
echo 3. 启动交互式监控 (main_interactive.py)
echo 4. 启动基础监控 (main_okx.py)
echo.

set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🧪 测试飞书连接...
    echo.
    python test_feishu.py
) else if "%choice%"=="2" (
    echo.
    echo 🧪 测试 OKX 连接...
    echo.
    python okx_monitor.py
) else if "%choice%"=="3" (
    echo.
    echo 🚀 启动交互式监控系统...
    echo.
    python main_interactive.py
) else if "%choice%"=="4" (
    echo.
    echo 🚀 启动基础监控系统...
    echo.
    python main_okx.py
) else (
    echo ❌ 无效的选项
)

echo.
pause



