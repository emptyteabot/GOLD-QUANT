@echo off
chcp 65001 >nul
title Gold Advisor Pro™ - 授权码管理
color 0E

echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║   🔑 Gold Advisor Pro™ 授权码管理工具        ║
echo  ╚═══════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

python license_manager.py

echo.
pause


