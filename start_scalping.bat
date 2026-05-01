@echo off
REM AURUM 短线交易系统启动脚本 (Windows)

echo.
echo 🚀 AURUM 黄金量化系统启动
echo ================================
echo.

REM 检查Python版本
echo 📍 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查依赖
echo.
echo 📍 检查依赖...
python -c "import pandas; import numpy; import sklearn; print('   ✅ 所有依赖已安装')" 2>nul
if errorlevel 1 (
    echo    ⚠️  缺少依赖，正在安装...
    pip install -r requirements.txt
)

REM 检查API配置
echo.
echo 📍 检查API配置...
if exist ".env.trading" (
    echo    ✅ .env.trading 文件存在
    findstr /M "OKX_API_KEY=" .env.trading >nul
    if errorlevel 1 (
        echo    ⚠️  API密钥未配置，请编辑 .env.trading
        pause
        exit /b 1
    ) else (
        echo    ✅ API密钥已配置
    )
) else (
    echo    ⚠️  .env.trading 文件不存在
    echo    请复制 .env.trading.example 为 .env.trading 并填入API密钥
    pause
    exit /b 1
)

REM 启动系统
echo.
echo ================================
echo 🎯 启动短线交易系统
echo 📊 模式: 16-Agent + 5分钟K线
echo ⏱️  目标: 5-15分钟内平仓
echo ================================
echo.

python main_scalping.py

pause
