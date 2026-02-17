@echo off
chcp 65001 >nul
title 📦 安装依赖包

color 0E
cls

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║                  📦 安装系统依赖包                            ║
echo ║                                                              ║
echo ║  这个过程只需要运行一次                                        ║
echo ║  大约需要 2-5 分钟                                            ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo.

echo 正在安装依赖包...
echo.

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ========================================================================
echo.

if %errorlevel% equ 0 (
    echo ✅ 依赖包安装成功！
    echo.
    echo 现在可以运行: 一键赚钱.bat
) else (
    echo ❌ 部分依赖包安装失败
    echo.
    echo 💡 不用担心，系统会在运行时自动安装缺失的包
    echo.
    echo 你可以直接运行: 一键赚钱.bat
)

echo.
echo ========================================================================
echo.

pause



