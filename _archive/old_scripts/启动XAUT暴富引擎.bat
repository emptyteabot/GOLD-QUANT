@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║        🚀 XAUT暴富引擎 - 一键启动 🚀                      ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝

echo.
echo [1/3] 检查Redis...
tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I /N "redis-server.exe">NUL
if errorlevel 1 (
    echo ⚠️  Redis未运行，正在启动...
    start "Redis Server" redis-server
    timeout /t 2 >nul
) else (
    echo ✅ Redis已运行
)

echo.
echo [2/3] 检查配置文件...
if not exist .env (
    echo ❌ 未找到.env配置文件
    echo 请先运行: 安装XAUT依赖.bat
    pause
    exit /b 1
)

echo.
echo [3/3] 启动XAUT暴富引擎...
python XAUT暴富引擎.py

pause

