@echo off
chcp 65001 >nul
cls
echo ========================================
echo 💰 黄金监控系统 - 最终版
echo ========================================
echo.

REM 获取当前目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo 请选择操作：
echo.
echo 1. 测试数据源（必须先测试）
echo 2. 启动黄金监控
echo 3. 测试飞书连接
echo 4. 退出
echo.

set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🧪 测试数据源...
    echo.
    D:\ANA\python.exe "%SCRIPT_DIR%简化版监控.py" test
) else if "%choice%"=="2" (
    echo.
    echo 🚀 启动黄金监控系统...
    echo.
    echo ⚠️ 按 Ctrl+C 可以停止系统
    echo.
    D:\ANA\python.exe "%SCRIPT_DIR%简化版监控.py"
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



