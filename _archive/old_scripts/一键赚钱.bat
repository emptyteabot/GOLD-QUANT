@echo off
chcp 65001 >nul
title 💰 一键赚钱 - 黄金交易系统

color 0A
cls

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║                  💰 一键赚钱 - 黄金交易系统                   ║
echo ║                                                              ║
echo ║  你只需要:                                                    ║
echo ║    1. 看飞书通知                                              ║
echo ║    2. 根据建议交易                                            ║
echo ║    3. 赚钱                                                    ║
echo ║                                                              ║
echo ║  系统会自动:                                                  ║
echo ║    • 监控市场                                                 ║
echo ║    • 分析信号                                                 ║
echo ║    • 推送飞书                                                 ║
echo ║    • 给出建议                                                 ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo.

echo 📱 确保你已经配置好飞书webhook
echo.
echo 配置文件: .env
echo 需要填写: FEISHU_WEBHOOK_URL=你的webhook地址
echo.
echo.

set /p confirm=确认启动? (Y/N): 

if /i "%confirm%"=="Y" (
    echo.
    echo ========================================================================
    echo 🚀 系统启动中...
    echo ========================================================================
    echo.
    echo 💡 提示:
    echo    • 系统会在后台运行
    echo    • 发现交易机会时会推送到你的飞书
    echo    • 按 Ctrl+C 可以停止系统
    echo.
    echo ========================================================================
    echo.
    
    python 一键赚钱.py
    
) else (
    echo.
    echo 已取消启动
    timeout /t 2 >nul
)

pause



