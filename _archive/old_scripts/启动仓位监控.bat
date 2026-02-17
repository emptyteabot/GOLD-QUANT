@echo off
chcp 65001 >nul
title 🚨 专属仓位监控

color 0C
cls

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║              🚨 专属仓位风险监控系统                          ║
echo ║                                                              ║
echo ║  你的仓位：                                                   ║
echo ║    • 持仓：0.3061 XAUT                                        ║
echo ║    • 杠杆：10x                                                ║
echo ║    • 开仓价：$4,546.7                                         ║
echo ║    • 强平价：$4,229.8                                         ║
echo ║                                                              ║
echo ║  监控功能：                                                   ║
echo ║    • 实时价格监控                                             ║
echo ║    • 盈亏计算                                                 ║
echo ║    • 爆仓风险预警                                             ║
echo ║    • 加仓机会提醒                                             ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo.

echo 🚀 启动监控...
echo.

python 专属仓位监控.py

pause


