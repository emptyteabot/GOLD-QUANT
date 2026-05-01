@echo off
REM AURUM 腾讯云部署脚�?(Windows)

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo 🚀 AURUM 腾讯云部�?echo ==========================================
echo.

REM 服务器信�?set SERVER_IP=43.135.51.214
set SERVER_USER=ubuntu
set SERVER_PASSWORD=<SERVER_PASSWORD>
set REMOTE_DIR=~/GOLD-QUANT

echo 📋 部署信息:
echo    服务�? %SERVER_USER%@%SERVER_IP%
echo    远程目录: %REMOTE_DIR%
echo.

REM 检查必要文�?echo 📍 第一步：检查必要文�?..
set MISSING_FILES=0

if not exist "aurum_24h_service.py" (
    echo    �?aurum_24h_service.py 不存�?    set MISSING_FILES=1
)
if not exist "agent_16_scalping_system.py" (
    echo    �?agent_16_scalping_system.py 不存�?    set MISSING_FILES=1
)
if not exist "scalping_engine.py" (
    echo    �?scalping_engine.py 不存�?    set MISSING_FILES=1
)
if not exist "requirements.txt" (
    echo    �?requirements.txt 不存�?    set MISSING_FILES=1
)
if not exist ".env.trading" (
    echo    �?.env.trading 不存�?    set MISSING_FILES=1
)
if not exist "install.sh" (
    echo    �?install.sh 不存�?    set MISSING_FILES=1
)

if %MISSING_FILES% equ 1 (
    echo.
    echo �?缺少必要文件�?    pause
    exit /b 1
)

echo    �?所有文件已检�?echo.

REM 检查SSH连接
echo 📍 第二步：检查SSH连接...
ssh -o ConnectTimeout=5 %SERVER_USER%@%SERVER_IP% "echo OK" >nul 2>&1
if errorlevel 1 (
    echo    �?无法连接到服务器
    echo    请检查：
    echo    - IP地址是否正确: %SERVER_IP%
    echo    - 用户名是否正�? %SERVER_USER%
    echo    - 网络连接是否正常
    echo.
    pause
    exit /b 1
)
echo    �?SSH连接成功
echo.

REM 上传文件
echo 📍 第三步：上传文件到服务器...
echo    这可能需要几分钟...
echo.

REM 创建远程目录
ssh %SERVER_USER%@%SERVER_IP% "mkdir -p %REMOTE_DIR%" >nul 2>&1

REM 上传文件
scp -r *.py %SERVER_USER%@%SERVER_IP%:%REMOTE_DIR%/ >nul 2>&1
if errorlevel 1 (
    echo    �?上传Python文件失败
    pause
    exit /b 1
)

scp requirements.txt %SERVER_USER%@%SERVER_IP%:%REMOTE_DIR%/ >nul 2>&1
if errorlevel 1 (
    echo    �?上传requirements.txt失败
    pause
    exit /b 1
)

scp .env.trading %SERVER_USER%@%SERVER_IP%:%REMOTE_DIR%/ >nul 2>&1
if errorlevel 1 (
    echo    �?上传.env.trading失败
    pause
    exit /b 1
)

scp install.sh %SERVER_USER%@%SERVER_IP%:%REMOTE_DIR%/ >nul 2>&1
if errorlevel 1 (
    echo    �?上传install.sh失败
    pause
    exit /b 1
)

echo    �?文件已上�?echo.

REM 执行部署
echo 📍 第四步：在服务器上执行部�?..
echo    这可能需要几分钟...
echo.

ssh %SERVER_USER%@%SERVER_IP% "cd %REMOTE_DIR% && chmod +x install.sh && ./install.sh"

if errorlevel 1 (
    echo.
    echo �?部署失败�?    pause
    exit /b 1
)

echo.
echo ==========================================
echo �?部署完成�?echo ==========================================
echo.
echo 🎯 系统已启�?echo.
echo 📋 常用命令:
echo.
echo   查看状�?
echo     ssh %SERVER_USER%@%SERVER_IP%
echo     sudo systemctl status aurum
echo.
echo   查看日志:
echo     ssh %SERVER_USER%@%SERVER_IP%
echo     tail -f ~/GOLD-QUANT/aurum_24h.log
echo.
echo   停止系统:
echo     ssh %SERVER_USER%@%SERVER_IP%
echo     sudo systemctl stop aurum
echo.
echo   重启系统:
echo     ssh %SERVER_USER%@%SERVER_IP%
echo     sudo systemctl restart aurum
echo.
echo ==========================================
echo.

pause
