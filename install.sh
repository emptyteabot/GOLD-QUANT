#!/bin/bash
# AURUM 完整部署脚本 - 在腾讯云服务器上运行

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=========================================="
echo "🚀 AURUM 系统完整部署"
echo "=========================================="
echo -e "${NC}"
echo ""

# 检查是否在正确的目录
if [ ! -f "aurum_24h_service.py" ]; then
    echo -e "${RED}❌ 错误：aurum_24h_service.py 不存在${NC}"
    echo "请确保所有文件都在当前目录"
    exit 1
fi

# 1. 更新系统
echo -e "${YELLOW}📍 第一步：更新系统...${NC}"
sudo apt-get update -qq
sudo apt-get upgrade -y -qq
echo -e "${GREEN}✅ 系统已更新${NC}"
echo ""

# 2. 安装依赖
echo -e "${YELLOW}📍 第二步：安装系统依赖...${NC}"
sudo apt-get install -y -qq python3 python3-pip python3-venv git curl wget
echo -e "${GREEN}✅ 系统依赖已安装${NC}"
echo ""

# 3. 检查Python版本
echo -e "${YELLOW}📍 第三步：检查Python版本...${NC}"
python3 --version
pip3 --version
echo ""

# 4. 创建虚拟环境
echo -e "${YELLOW}📍 第四步：创建虚拟环境...${NC}"
python3 -m venv venv
source venv/bin/activate
echo -e "${GREEN}✅ 虚拟环境已创建${NC}"
echo ""

# 5. 安装Python依赖
echo -e "${YELLOW}📍 第五步：安装Python依赖...${NC}"
pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
else
    echo -e "${YELLOW}⚠️  requirements.txt 不存在，安装基础依赖...${NC}"
    pip install pandas numpy scikit-learn xgboost aiohttp python-dotenv -q
fi
echo -e "${GREEN}✅ Python依赖已安装${NC}"
echo ""

# 6. 检查配置文件
echo -e "${YELLOW}📍 第六步：检查配置文件...${NC}"
if [ ! -f ".env.trading" ]; then
    echo -e "${RED}❌ 错误：.env.trading 文件不存在${NC}"
    echo "请创建 .env.trading 文件并配置API密钥"
    exit 1
fi

# 检查API密钥是否已配置
if grep -q "your_api_key_here" .env.trading; then
    echo -e "${RED}❌ 错误：API密钥未配置${NC}"
    echo "请编辑 .env.trading 文件，填入你的OKX API密钥"
    exit 1
fi
echo -e "${GREEN}✅ 配置文件已检查${NC}"
echo ""

# 7. 测试API连接
echo -e "${YELLOW}📍 第七步：测试API连接...${NC}"
python3 << 'PYEOF'
import sys
import os
sys.path.insert(0, '.')
os.environ['PYTHONUNBUFFERED'] = '1'

try:
    from okx_client import OKXClient
    import asyncio

    async def test():
        try:
            client = OKXClient()
            await client.initialize()
            ticker = await client.get_ticker('XAU-USDT-SWAP')
            if ticker:
                print(f"✅ API连接成功！")
                print(f"   当前黄金价格: ${ticker['last']}")
                return True
            else:
                print("❌ 无法获取行情")
                return False
        except Exception as e:
            print(f"❌ API连接失败: {e}")
            return False

    result = asyncio.run(test())
    sys.exit(0 if result else 1)
except Exception as e:
    print(f"❌ 测试失败: {e}")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ API连接测试失败${NC}"
    exit 1
fi
echo ""

# 8. 创建systemd服务
echo -e "${YELLOW}📍 第八步：创建systemd服务...${NC}"
SERVICE_FILE="/etc/systemd/system/aurum.service"

sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=AURUM 24H Trading System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python aurum_24h_service.py
Restart=always
RestartSec=10
StandardOutput=append:$(pwd)/aurum_24h.log
StandardError=append:$(pwd)/aurum_24h.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo -e "${GREEN}✅ systemd服务已创建${NC}"
echo ""

# 9. 启动系统
echo -e "${YELLOW}📍 第九步：启动系统...${NC}"
sudo systemctl enable aurum
sudo systemctl start aurum
sleep 2
sudo systemctl status aurum
echo ""

# 10. 显示完成信息
echo -e "${BLUE}"
echo "=========================================="
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "=========================================="
echo -e "${NC}"
echo ""
echo "🎯 系统已启动"
echo ""
echo "📋 常用命令："
echo ""
echo "  查看状态："
echo "    sudo systemctl status aurum"
echo ""
echo "  查看日志："
echo "    tail -f aurum_24h.log"
echo ""
echo "  停止系统："
echo "    sudo systemctl stop aurum"
echo ""
echo "  重启系统："
echo "    sudo systemctl restart aurum"
echo ""
echo "  查看实时日志："
echo "    sudo journalctl -u aurum -f"
echo ""
echo "=========================================="
echo ""
