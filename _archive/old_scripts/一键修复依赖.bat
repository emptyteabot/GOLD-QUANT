@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║              🔧 一键修复依赖问题                              ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 正在修复NumPy版本冲突...
echo.

REM 降级NumPy到1.x版本
pip install "numpy<2.0" --force-reinstall

echo.
echo ✅ NumPy已降级到1.x版本
echo.
echo 正在重新安装依赖...
echo.

REM 重新安装其他依赖
pip install pandas scipy scikit-learn --force-reinstall

echo.
echo ════════════════════════════════════════════════════════════════
echo ✅ 修复完成！
echo ════════════════════════════════════════════════════════════════
echo.
pause


