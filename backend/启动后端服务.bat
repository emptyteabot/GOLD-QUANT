@echo off
chcp 65001 >nul
echo ========================================
echo AURUM 后端服务启动
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/3] 检查依赖包...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
)

echo.
echo [3/3] 启动FastAPI服务...
echo.
echo 访问地址:
echo   - API文档: http://localhost:8000/docs
echo   - ReDoc: http://localhost:8000/redoc
echo   - 健康检查: http://localhost:8000/health
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
