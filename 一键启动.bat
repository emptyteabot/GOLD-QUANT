@echo off
chcp 65001 >nul 2>nul
title Gold Advisor Pro™ v3.0 - 一键启动
color 0E
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════════════
::  Gold Advisor Pro™ v3.0 - 全自动一键启动
::  客户什么都不需要懂，双击就能用
:: ═══════════════════════════════════════════════════

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║                                                  ║
echo  ║     Gold Advisor Pro™ v3.0                       ║
echo  ║     A股黄金日内智能交易策略系统                  ║
echo  ║                                                  ║
echo  ║     正在为您准备系统环境，请稍候...              ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: ──────────────────────────────────────────────────
::  第1步：查找 Python
:: ──────────────────────────────────────────────────
echo  [1/4] 检测 Python 环境...

set PYTHON_CMD=

:: 尝试 python
python --version >nul 2>nul
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :python_found
)

:: 尝试 python3
python3 --version >nul 2>nul
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto :python_found
)

:: 尝试 py -3
py -3 --version >nul 2>nul
if not errorlevel 1 (
    set PYTHON_CMD=py -3
    goto :python_found
)

:: 尝试常见安装路径
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :python_found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :python_found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :python_found
)

:: Python 未找到
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  未检测到 Python！请先安装 Python 3.10+         ║
echo  ║                                                  ║
echo  ║  下载地址：https://www.python.org/downloads/     ║
echo  ║                                                  ║
echo  ║  安装时请务必勾选：                              ║
echo  ║  [√] Add Python to PATH                         ║
echo  ║                                                  ║
echo  ║  安装完成后重新双击本文件即可                    ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  正在为您打开 Python 下载页面...
start https://www.python.org/downloads/
echo.
pause
exit /b 1

:python_found
for /f "tokens=*" %%v in ('%PYTHON_CMD% --version 2^>^&1') do set PYVER=%%v
echo        %PYVER% [OK]

:: ──────────────────────────────────────────────────
::  第2步：创建/激活虚拟环境
:: ──────────────────────────────────────────────────
echo  [2/4] 准备运行环境...

if not exist ".venv\Scripts\python.exe" (
    echo        首次运行，正在创建虚拟环境...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo        创建虚拟环境失败，尝试直接安装...
        goto :install_global
    )
)

:: 使用虚拟环境的 python
set PYTHON_CMD=.venv\Scripts\python.exe
set PIP_CMD=.venv\Scripts\pip.exe
echo        虚拟环境 [OK]

:: ──────────────────────────────────────────────────
::  第3步：安装依赖
:: ──────────────────────────────────────────────────
echo  [3/4] 检查依赖包...

:: 检查 streamlit 是否已安装
.venv\Scripts\python.exe -c "import streamlit" >nul 2>nul
if errorlevel 1 (
    echo        首次运行，正在安装依赖包（约2-3分钟）...
    echo        使用清华镜像加速下载...
    echo.
    %PIP_CMD% install -r requirements_ashare.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    if errorlevel 1 (
        echo.
        echo        镜像源安装失败，尝试官方源...
        %PIP_CMD% install -r requirements_ashare.txt --quiet
        if errorlevel 1 (
            echo.
            echo  ╔══════════════════════════════════════════════════╗
            echo  ║  依赖安装失败！请检查网络连接后重试             ║
            echo  ╚══════════════════════════════════════════════════╝
            echo.
            pause
            exit /b 1
        )
    )
    echo.
)

echo        依赖包 [OK]

goto :launch

:install_global
:: 没有虚拟环境时的备选方案
set PYTHON_CMD=python
set PIP_CMD=pip
pip show streamlit >nul 2>nul
if errorlevel 1 (
    echo        正在安装依赖包...
    pip install -r requirements_ashare.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
)

:: ──────────────────────────────────────────────────
::  第4步：启动系统
:: ──────────────────────────────────────────────────
:launch
echo  [4/4] 启动 Gold Advisor Pro™...
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║                                                  ║
echo  ║   系统正在启动，浏览器将自动打开...             ║
echo  ║                                                  ║
echo  ║   如浏览器未自动打开，请手动访问：              ║
echo  ║                                                  ║
echo  ║   >>> http://localhost:8501 <<<                  ║
echo  ║                                                  ║
echo  ║   关闭本窗口即可停止系统                        ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: 延迟2秒后自动打开浏览器
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8501"

:: 启动 Streamlit
%PYTHON_CMD% -m streamlit run gold_advisor_app.py --server.port 8501

echo.
echo  系统已停止。
pause


