#!/bin/bash
# AURUM 完整部署脚本 - 在本地运行，自动上传和部署到腾讯�?
set -e

SERVER_IP="43.135.51.214"
SERVER_USER="ubuntu"
SERVER_PASSWORD="<SERVER_PASSWORD>"
REMOTE_DIR="~/GOLD-QUANT"

echo ""
echo "=========================================="
echo "🚀 AURUM 腾讯云一键部�?
echo "=========================================="
echo ""

# 检查文�?echo "📍 检查本地文�?.."
cd ~/Desktop/GOLD-QUANT

REQUIRED_FILES=(
    "aurum_24h_service.py"
    "agent_16_scalping_system.py"
    "scalping_engine.py"
    "okx_client.py"
    "risk_manager.py"
    "config.py"
    "requirements.txt"
    ".env.trading"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "�?缺少文件: $file"
        exit 1
    fi
done
echo "�?所有文件已检�?
echo ""

# 创建部署脚本
echo "📍 创建部署脚本..."
cat > /tmp/deploy_on_server.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
set -e

cd ~/GOLD-QUANT

echo "📍 更新系统..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

echo "📍 安装依赖..."
sudo apt-get install -y -qq python3 python3-pip python3-venv git

echo "📍 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

echo "📍 安装Python依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "📍 测试API连接..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from okx_client import OKXClient
import asyncio

async def test():
    client = OKXClient()
    await client.initialize()
    ticker = await client.get_ticker('XAU-USDT-SWAP')
    if ticker:
        print(f"�?API连接成功！价�? ${ticker['last']}")
        return True
    return False

asyncio.run(test())
PYEOF

echo "📍 创建systemd服务..."
sudo tee /etc/systemd/system/aurum.service > /dev/null << 'EOF'
[Unit]
Description=AURUM 24H Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/GOLD-QUANT
Environment="PATH=/home/ubuntu/GOLD-QUANT/venv/bin"
ExecStart=/home/ubuntu/GOLD-QUANT/venv/bin/python aurum_24h_service.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/GOLD-QUANT/aurum_24h.log
StandardError=append:/home/ubuntu/GOLD-QUANT/aurum_24h.log

[Install]
WantedBy=multi-user.target
EOF

echo "📍 启动系统..."
sudo systemctl daemon-reload
sudo systemctl enable aurum
sudo systemctl start aurum
sleep 2

echo ""
echo "=========================================="
echo "�?部署完成�?
echo "=========================================="
echo ""
echo "系统已启动，查看日志�?
echo "  tail -f ~/GOLD-QUANT/aurum_24h.log"
echo ""

DEPLOY_SCRIPT

chmod +x /tmp/deploy_on_server.sh
echo "�?部署脚本已创�?
echo ""

# 上传文件
echo "📍 上传文件到服务器..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $SERVER_USER@$SERVER_IP "mkdir -p $REMOTE_DIR" 2>/dev/null || true

for file in "${REQUIRED_FILES[@]}"; do
    scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$file" $SERVER_USER@$SERVER_IP:$REMOTE_DIR/ 2>/dev/null
    echo "   �?$file"
done
echo "�?文件已上�?
echo ""

# 上传部署脚本
echo "📍 上传部署脚本..."
scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null /tmp/deploy_on_server.sh $SERVER_USER@$SERVER_IP:$REMOTE_DIR/deploy.sh 2>/dev/null
echo "�?部署脚本已上�?
echo ""

# 执行部署
echo "📍 在服务器上执行部�?.."
echo ""

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $SERVER_USER@$SERVER_IP "bash ~/GOLD-QUANT/deploy.sh"

echo ""
echo "=========================================="
echo "�?部署完成�?
echo "=========================================="
echo ""
echo "🎯 系统已启�?
echo ""
echo "📋 常用命令�?
echo ""
echo "  查看日志�?
echo "    ssh $SERVER_USER@$SERVER_IP"
echo "    tail -f ~/GOLD-QUANT/aurum_24h.log"
echo ""
echo "  查看状态："
echo "    ssh $SERVER_USER@$SERVER_IP"
echo "    sudo systemctl status aurum"
echo ""
echo "=========================================="
echo ""
