@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║         🔥 完整版激进交易系统 - 5200+行代码                   ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 第1步：修复NumPy版本冲突...
echo.

pip install "numpy<2.0" --force-reinstall -q

echo ✅ NumPy已修复
echo.
echo 第2步：启动完整版系统...
echo.

python 激进交易系统.py

pause


