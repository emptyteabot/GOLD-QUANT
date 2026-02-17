@echo off
chcp 65001 >nul
echo ========================================
echo 💰 黄金监控系统 - 测试工具
echo ========================================
echo.

REM 获取当前目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo 当前目录: %CD%
echo.

REM 检查 Python
D:\ANA\python.exe --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python
    pause
    exit /b 1
)

echo ✅ Python 已找到
echo.

echo 请选择测试项目：
echo.
echo 1. 测试所有黄金数据源
echo 2. 启动黄金监控系统
echo 3. 测试飞书连接
echo 4. 退出
echo.

set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🧪 测试黄金数据源...
    echo.
    D:\ANA\python.exe "%SCRIPT_DIR%gold_monitor.py" test
) else if "%choice%"=="2" (
    echo.
    echo 🚀 启动黄金监控系统...
    echo.
    D:\ANA\python.exe "%SCRIPT_DIR%gold_monitor.py"
) else if "%choice%"=="3" (
    echo.
    echo 🧪 测试飞书连接...
    echo.
    D:\ANA\python.exe "%SCRIPT_DIR%test_feishu.py"
) else if "%choice%"=="4" (
    echo 👋 再见！
    exit /b 0
) else (
    echo ❌ 无效的选项
)

echo.
pause



