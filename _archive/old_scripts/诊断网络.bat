@echo off
chcp 65001 >nul
echo ========================================
echo 🔧 网络诊断工具
echo ========================================
echo.

REM 获取当前目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo 正在诊断网络连接...
echo.

D:\ANA\python.exe "%SCRIPT_DIR%诊断工具.py"

echo.
echo ========================================
echo 💡 根据诊断结果：
echo.
echo 如果 Binance 或 OKX 连接成功：
echo   → 可以直接使用，无需申请 API
echo.
echo 如果都失败：
echo   → 可能是网络问题（防火墙/代理）
echo   → 或者需要申请 GoldAPI
echo ========================================
echo.
pause



