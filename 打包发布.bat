@echo off
chcp 65001 >nul 2>nul
title Gold Advisor Pro™ - 打包发布工具
color 0E

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   Gold Advisor Pro™ - 打包发布工具              ║
echo  ║   将核心文件打包为可分发的客户版本              ║
echo  ╚══════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

set DIST_DIR=发布版_GoldAdvisorPro

:: 创建发布目录
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
mkdir "%DIST_DIR%"
mkdir "%DIST_DIR%\.streamlit"

:: 复制核心文件
echo  正在复制核心文件...
copy "gold_advisor_app.py"       "%DIST_DIR%\" >nul
copy "gold_strategy_engine.py"   "%DIST_DIR%\" >nul
copy "gold_config.py"            "%DIST_DIR%\" >nul
copy "ashare_provider.py"        "%DIST_DIR%\" >nul
copy "license_manager.py"        "%DIST_DIR%\" >nul
copy "requirements_ashare.txt"   "%DIST_DIR%\" >nul
copy "一键启动.bat"              "%DIST_DIR%\" >nul
copy "Gold Advisor Pro.html"     "%DIST_DIR%\" >nul
copy "生成授权码.bat"            "%DIST_DIR%\" >nul
copy ".streamlit\config.toml"    "%DIST_DIR%\.streamlit\" >nul

:: 创建 .env.trading 模板
echo # Gold Advisor Pro 配置文件> "%DIST_DIR%\.env.trading"
echo # 如有飞书通知需求，填写下方 Webhook>> "%DIST_DIR%\.env.trading"
echo # FEISHU_WEBHOOK_URL=>> "%DIST_DIR%\.env.trading"

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   打包完成！                                    ║
echo  ║                                                  ║
echo  ║   发布目录: %DIST_DIR%\                         ║
echo  ║                                                  ║
echo  ║   客户使用方法:                                  ║
echo  ║   1. 解压整个文件夹                              ║
echo  ║   2. 双击 "一键启动.bat"                         ║
echo  ║   3. 等待自动安装并打开浏览器                    ║
echo  ║   4. 输入授权码激活                              ║
echo  ║                                                  ║
echo  ║   你需要做的:                                    ║
echo  ║   1. 运行 "生成授权码.bat" 获取客户的授权码     ║
echo  ║   2. 将授权码发给客户                            ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: 打开发布目录
explorer "%DIST_DIR%"

pause


