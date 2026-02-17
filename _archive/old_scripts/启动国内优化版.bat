@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ========================================
echo 启动国内优化版交易系统
echo ========================================
echo.
echo 使用国内数据源，无需代理
echo.
python 国内版-一键赚钱.py
pause


