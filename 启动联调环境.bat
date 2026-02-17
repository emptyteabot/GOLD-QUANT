@echo off
chcp 65001 >nul
echo ========================================
echo 启动前后端联调环境
echo ========================================
echo.

cd /d "%~dp0.."

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装
    pause
    exit /b 1
)

:: 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装
    pause
    exit /b 1
)

echo [1/4] 启动后端服务...
start "Gold Advisor Backend" cmd /k "cd backend && python app.py"
timeout /t 3 >nul

echo [2/4] 等待后端启动...
timeout /t 5 >nul

echo [3/4] 启动前端服务...
start "Gold Advisor Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 3 >nul

echo [4/4] 打开浏览器...
timeout /t 8 >nul
start http://localhost:3000

echo.
echo ========================================
echo ✓ 服务已启动
echo ========================================
echo 前端: http://localhost:3000
echo 后端: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo ========================================
echo.
echo 按任意键关闭此窗口（服务将继续运行）
pause >nul
