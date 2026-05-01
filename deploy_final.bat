@echo off
REM AURUM 腾讯云部署脚�?- Windows版本

setlocal enabledelayedexpansion

set SERVER_IP=43.135.51.214
set SERVER_USER=ubuntu
set SERVER_PASSWORD=<SERVER_PASSWORD>
set REMOTE_DIR=~/GOLD-QUANT

echo.
echo ==========================================
echo 🚀 AURUM 腾讯云部�?echo ==========================================
echo.

REM 检查文�?echo 📍 检查本地文�?..
cd /d "%USERPROFILE%\Desktop\GOLD-QUANT"

if not exist "aurum_24h_service.py" (
    echo �?aurum_24h_service.py 不存�?    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo �?requirements.txt 不存�?    pause
    exit /b 1
)

if not exist ".env.trading" (
    echo �?.env.trading 不存�?    pause
    exit /b 1
)

echo �?所有文件已检�?echo.

REM 创建部署脚本
echo 📍 创建部署脚本...

(
echo #!/bin/bash
echo set -e
echo cd ~/GOLD-QUANT
echo.
echo echo "📍 更新系统..."
echo sudo apt-get update -qq
echo sudo apt-get upgrade -y -qq
echo.
echo echo "📍 安装依赖..."
echo sudo apt-get install -y -qq python3 python3-pip python3-venv git
echo.
echo echo "📍 创建虚拟环境..."
echo python3 -m venv venv
echo source venv/bin/activate
echo.
echo echo "📍 安装Python依赖..."
echo pip install --upgrade pip -q
echo pip install -r requirements.txt -q
echo.
echo echo "📍 测试API连接..."
echo python3 ^<^< 'PYEOF'
echo import sys
echo sys.path.insert^(0, '.'
echo from okx_client import OKXClient
echo import asyncio
echo.
echo async def test^(^):
echo     client = OKXClient^(^)
echo     await client.initialize^(^)
echo     ticker = await client.get_ticker^('XAU-USDT-SWAP'^)
echo     if ticker:
echo         print^(f"�?API连接成功！价�? ${ticker['last']}"^)
echo PYEOF
echo.
echo echo "📍 创建systemd服务..."
echo sudo tee /etc/systemd/system/aurum.service ^> /dev/null ^<^< 'EOF'
echo [Unit]
echo Description=AURUM 24H Trading System
echo After=network.target
echo.
echo [Service]
echo Type=simple
echo User=ubuntu
echo WorkingDirectory=/home/ubuntu/GOLD-QUANT
echo Environment="PATH=/home/ubuntu/GOLD-QUANT/venv/bin"
echo ExecStart=/home/ubuntu/GOLD-QUANT/venv/bin/python aurum_24h_service.py
echo Restart=always
echo RestartSec=10
echo StandardOutput=append:/home/ubuntu/GOLD-QUANT/aurum_24h.log
echo StandardError=append:/home/ubuntu/GOLD-QUANT/aurum_24h.log
echo.
echo [Install]
echo WantedBy=multi-user.target
echo EOF
echo.
echo echo "📍 启动系统..."
echo sudo systemctl daemon-reload
echo sudo systemctl enable aurum
echo sudo systemctl start aurum
echo sleep 2
echo.
echo echo "=========================================="
echo echo "�?部署完成�?
echo echo "=========================================="
echo echo ""
echo echo "系统已启�?
echo echo ""
) > deploy_script.sh

echo �?部署脚本已创�?echo.

REM 上传文件
echo 📍 上传文件到服务器...

ssh -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% "mkdir -p %REMOTE_DIR%" >nul 2>&1

scp -o StrictHostKeyChecking=no *.py %SERVER_USER%@%SERVER_IP%:%REMOTE_DIR%/ >nul 2>&1
scp -o StrictHostKeyChecking=no requirements.txt %SERVER_USER%@%SERVER_IP%:%REMOTE_DIR%/ >nul 2>&1
scp -o StrictHostKeyChecking=no .env.trading %SERVER_USER%@%SERVER_IP%:%REMOTE_DIR%/ >nul 2>&1

echo �?文件已上�?echo.

REM 上传部署脚本
echo 📍 上传部署脚本...
scp -o StrictHostKeyChecking=no deploy_script.sh %SERVER_USER%@%SERVER_IP%:%REMOTE_DIR%/deploy.sh >nul 2>&1
echo �?部署脚本已上�?echo.

REM 执行部署
echo 📍 在服务器上执行部�?..
echo    这可能需要几分钟...
echo.

ssh -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% "bash ~/GOLD-QUANT/deploy.sh"

echo.
echo ==========================================
echo �?部署完成�?echo ==========================================
echo.
echo 🎯 系统已启�?echo.
echo 📋 常用命令:
echo.
echo   查看日志:
echo     ssh %SERVER_USER%@%SERVER_IP%
echo     tail -f ~/GOLD-QUANT/aurum_24h.log
echo.
echo   查看状�?
echo     sudo systemctl status aurum
echo.
echo ==========================================
echo.

pause
