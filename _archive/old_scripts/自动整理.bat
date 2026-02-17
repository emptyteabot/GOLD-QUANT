@echo off
chcp 65001 >nul
cls
echo ========================================
echo 📁 自动整理文件夹
echo ========================================
echo.

REM 获取当前目录
set SOURCE_DIR=%~dp0
set DEST_DIR=%USERPROFILE%\Desktop\黄金监控-最终版

echo 源文件夹: %SOURCE_DIR%
echo 目标文件夹: %DEST_DIR%
echo.

echo ⚠️ 此操作将：
echo 1. 在桌面创建新文件夹：黄金监控-最终版
echo 2. 复制核心文件到新文件夹
echo 3. 不会删除当前文件夹
echo.

set /p confirm="确认继续？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消
    pause
    exit /b 0
)

echo.
echo 开始整理...
echo.

REM 创建目标文件夹
if not exist "%DEST_DIR%" (
    mkdir "%DEST_DIR%"
    echo ✅ 创建文件夹: %DEST_DIR%
) else (
    echo ⚠️ 文件夹已存在: %DEST_DIR%
)

REM 复制核心文件
echo.
echo 📋 复制核心文件...
echo.

REM 1. 主程序
if exist "%SOURCE_DIR%终极版监控.py" (
    copy "%SOURCE_DIR%终极版监控.py" "%DEST_DIR%\" >nul
    echo ✅ 终极版监控.py
) else (
    echo ❌ 未找到: 终极版监控.py
)

REM 2. 启动脚本
if exist "%SOURCE_DIR%最终启动.bat" (
    copy "%SOURCE_DIR%最终启动.bat" "%DEST_DIR%\" >nul
    echo ✅ 最终启动.bat
) else (
    echo ❌ 未找到: 最终启动.bat
)

REM 3. 配置文件
if exist "%SOURCE_DIR%.env" (
    copy "%SOURCE_DIR%.env" "%DEST_DIR%\" >nul
    echo ✅ .env
) else (
    echo ⚠️ 未找到 .env，请手动创建
)

REM 4. 配置示例
if exist "%SOURCE_DIR%配置示例.txt" (
    copy "%SOURCE_DIR%配置示例.txt" "%DEST_DIR%\" >nul
    echo ✅ 配置示例.txt
) else (
    echo ❌ 未找到: 配置示例.txt
)

REM 5. 使用说明
if exist "%SOURCE_DIR%使用说明.md" (
    copy "%SOURCE_DIR%使用说明.md" "%DEST_DIR%\" >nul
    echo ✅ 使用说明.md
) else (
    echo ❌ 未找到: 使用说明.md
)

REM 6. 测试脚本（可选）
if exist "%SOURCE_DIR%test_feishu.py" (
    copy "%SOURCE_DIR%test_feishu.py" "%DEST_DIR%\" >nul
    echo ✅ test_feishu.py
)

REM 7. 依赖文件（可选）
if exist "%SOURCE_DIR%requirements.txt" (
    copy "%SOURCE_DIR%requirements.txt" "%DEST_DIR%\" >nul
    echo ✅ requirements.txt
)

echo.
echo ========================================
echo ✅ 整理完成！
echo ========================================
echo.
echo 新文件夹位置: %DEST_DIR%
echo.
echo 📋 下一步：
echo 1. 打开新文件夹
echo 2. 编辑 .env 文件，填入飞书 Webhook
echo 3. 双击 最终启动.bat 测试
echo.

set /p open="是否打开新文件夹？(Y/N): "
if /i "%open%"=="Y" (
    explorer "%DEST_DIR%"
)

echo.
pause



