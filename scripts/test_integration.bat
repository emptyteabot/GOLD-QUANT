@echo off
chcp 65001 >nul
echo ========================================
echo 前后端联调测试
echo ========================================
echo.

cd /d "%~dp0.."

echo [1/2] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    pause
    exit /b 1
)

echo [2/2] 运行测试脚本...
python scripts/test_integration.py

echo.
pause
