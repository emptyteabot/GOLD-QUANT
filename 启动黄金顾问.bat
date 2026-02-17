@echo off
chcp 65001 >nul 2>&1
title Gold Advisor Pro™ - A股黄金日内策略系统

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║                                                       ║
echo  ║     🥇  Gold Advisor Pro™                             ║
echo  ║     A股黄金板块 · 日内智能交易策略系统                ║
echo  ║     版本 2.0.0                                        ║
echo  ║                                                       ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

:: 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ❌ 未找到Python，请先安装 Python 3.10+
    echo     下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查依赖
echo  📦 检查依赖包...
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo  📦 首次运行，正在安装依赖...
    pip install -r requirements_ashare.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo  ❌ 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)

pip show akshare >nul 2>&1
if %errorlevel% neq 0 (
    echo  📦 安装 akshare 数据源...
    pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo  🚀 启动系统...
echo  📊 浏览器将自动打开 http://localhost:8501
echo  📌 按 Ctrl+C 停止系统
echo.

:: 启动Streamlit应用
cd /d "%~dp0"
streamlit run gold_advisor_app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false --theme.primaryColor "#ffd700" --theme.backgroundColor "#0e1117" --theme.secondaryBackgroundColor "#1e1e2f" --theme.textColor "#ffffff"

