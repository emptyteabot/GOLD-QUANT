@echo off
chcp 65001 >nul 2>nul
title Gold Advisor Pro™ v3.0 - Trading Terminal
color 0E

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║                                                  ║
echo  ║   Gold Advisor Pro™ v3.0                         ║
echo  ║   Next.js + FastAPI 交易终端                     ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: ── 1. 启动 Python 后端 ──
echo  [1/2] 启动 API 后端 (port 8000)...
start "GoldAdvisor-Backend" cmd /c "cd /d "%~dp0" && python backend\app.py"
timeout /t 3 /nobreak >nul
echo        Backend [OK]

:: ── 2. 启动 Next.js 前端 ──
echo  [2/2] 启动前端 (port 3000)...

cd frontend
if not exist "node_modules" (
    echo        首次运行，安装前端依赖...
    call npm install
)
echo        Frontend starting...
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║                                                  ║
echo  ║   系统启动完成！                                ║
echo  ║                                                  ║
echo  ║   前端: http://localhost:3000                    ║
echo  ║   API:  http://localhost:8000/docs               ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

start http://localhost:3000
call npm run dev
pause



