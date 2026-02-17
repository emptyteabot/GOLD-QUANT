@echo off
chcp 65001 >nul 2>nul
title Gold Advisor Pro™ - 部署到云端
color 0E

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   Gold Advisor Pro™ - 部署到 Streamlit Cloud    ║
echo  ║   部署后客户通过网址直接访问                    ║
echo  ╚══════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: 检查 git
git --version >nul 2>nul
if errorlevel 1 (
    echo  未检测到 Git，请先安装：https://git-scm.com/downloads
    echo  安装完成后重新运行本脚本
    start https://git-scm.com/downloads
    pause
    exit /b
)
echo  Git [OK]

:: 初始化 git
if not exist ".git" (
    echo.
    echo  初始化 Git 仓库...
    git init
    git branch -M main
)

:: 添加文件
echo  添加文件到 Git...
git add gold_advisor_app.py
git add gold_strategy_engine.py
git add gold_config.py
git add ashare_provider.py
git add license_manager.py
git add requirements.txt
git add requirements_ashare.txt
git add .gitignore
git add .streamlit/config.toml
git add "Gold Advisor Pro.html"
git add 一键启动.bat

:: 提交
git commit -m "Gold Advisor Pro v3.0 - deploy"

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  Git 仓库已准备好！                             ║
echo  ║                                                  ║
echo  ║  接下来请完成以下3步：                           ║
echo  ║                                                  ║
echo  ║  第1步：创建 GitHub 仓库                         ║
echo  ║    1. 打开 https://github.com/new               ║
echo  ║    2. 仓库名: gold-advisor-pro                   ║
echo  ║    3. 选择 Private（私有）                       ║
echo  ║    4. 点击 Create repository                     ║
echo  ║                                                  ║
echo  ║  第2步：推送代码                                 ║
echo  ║    在本窗口输入以下命令（替换你的用户名）：     ║
echo  ║                                                  ║
echo  ║    git remote add origin                         ║
echo  ║      https://github.com/你的用户名/gold-advisor-pro.git ║
echo  ║    git push -u origin main                       ║
echo  ║                                                  ║
echo  ║  第3步：部署到 Streamlit Cloud                   ║
echo  ║    1. 打开 https://share.streamlit.io            ║
echo  ║    2. 用 GitHub 账号登录                         ║
echo  ║    3. 选择 gold-advisor-pro 仓库                 ║
echo  ║    4. Main file: gold_advisor_app.py             ║
echo  ║    5. 在 Advanced > Secrets 中设置授权码         ║
echo  ║    6. 点击 Deploy!                               ║
echo  ║                                                  ║
echo  ║  部署成功后你会得到一个网址：                   ║
echo  ║  https://你的名字-gold-advisor-pro.streamlit.app ║
echo  ║                                                  ║
echo  ║  把这个网址发给客户就行了！                     ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: 打开 GitHub 创建页面
start https://github.com/new

pause

