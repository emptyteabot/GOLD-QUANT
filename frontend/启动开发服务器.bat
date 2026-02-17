@echo off
chcp 65001 >nul
echo ========================================
echo   AURUM Dashboard - 快速启动
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)
echo ✅ Node.js环境正常

echo.
echo [2/4] 检查依赖...
if not exist "node_modules" (
    echo 📦 首次运行，正在安装依赖...
    call npm install
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖已存在
)

echo.
echo [3/4] 检查环境变量...
if not exist ".env.local" (
    echo 📝 创建环境变量文件...
    copy .env.local.example .env.local >nul
    echo ✅ 已创建 .env.local，请根据需要修改配置
) else (
    echo ✅ 环境变量文件已存在
)

echo.
echo [4/4] 启动开发服务器...
echo 🚀 正在启动 http://localhost:3000
echo.
echo ----------------------------------------
echo   按 Ctrl+C 停止服务器
echo ----------------------------------------
echo.

call npm run dev
