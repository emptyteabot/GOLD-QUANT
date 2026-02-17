@echo off
echo ========================================
echo 启动 AURUM 黄金交易系统
echo ========================================
echo.

echo [1/2] 检查持仓...
python check_positions.py

echo.
echo [2/2] 启动主系统...
python main.py

pause
