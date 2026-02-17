@echo off
chcp 65001 >nul
echo ========================================
echo 停止所有服务
echo ========================================
echo.

:: 停止Python进程（后端）
taskkill /F /FI "WINDOWTITLE eq Gold Advisor Backend*" >nul 2>&1
taskkill /F /IM python.exe /FI "MEMUSAGE gt 50000" >nul 2>&1

:: 停止Node进程（前端）
taskkill /F /FI "WINDOWTITLE eq Gold Advisor Frontend*" >nul 2>&1
taskkill /F /IM node.exe /FI "MEMUSAGE gt 50000" >nul 2>&1

echo ✓ 所有服务已停止
echo.
pause
