#!/bin/bash
# AURUM 一键部署脚本（在腾讯云服务器上运行�?
set -e

echo ""
echo "=========================================="
echo "🚀 AURUM 系统一键部�?
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 更新系统
echo -e "${YELLOW}📍 第一步：更新系统...${NC}"
sudo apt-get update -qq
sudo apt-get upgrade -y -qq
echo -e "${GREEN}�?系统已更�?{NC}"
echo ""

# 2. 安装依赖
echo -e "${YELLOW}📍 第二步：安装依赖...${NC}"
sudo apt-get install -y -qq python3 python3-pip python3-venv git curl wget
echo -e "${GREEN}�?依赖已安�?{NC}"
echo ""

# 3. 检查Python版本
echo -e "${YELLOW}📍 第三步：检查Python版本...${NC}"
python3 --version
pip3 --version
echo ""

# 4. 创建项目目录
echo -e "${YELLOW}📍 第四步：创建项目目录...${NC}"
mkdir -p ~/GOLD-QUANT
cd ~/GOLD-QUANT
echo -e "${GREEN}�?项目目录已创�? ~/GOLD-QUANT${NC}"
echo ""

# 5. 检查项目文�?echo -e "${YELLOW}📍 第五步：检查项目文�?..${NC}"
if [ ! -f "aurum_24h_service.py" ]; then
    echo -e "${RED}�?错误：aurum_24h_service.py 文件不存�?{NC}"
    echo "请先上传项目文件�?~/GOLD-QUANT 目录"
    exit 1
fi
echo -e "${GREEN}�?项目文件已检�?{NC}"
echo ""

# 6. 创建虚拟环境
echo -e "${YELLOW}📍 第六步：创建虚拟环境...${NC}"
python3 -m venv venv
source venv/bin/activate
echo -e "${GREEN}�?虚拟环境已创�?{NC}"
echo ""

# 7. 安装Python依赖
echo -e "${YELLOW}📍 第七步：安装Python依赖...${NC}"
pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
else
    echo -e "${YELLOW}⚠️  requirements.txt 不存在，安装基础依赖...${NC}"
    pip install pandas numpy scikit-learn xgboost aiohttp python-dotenv -q
fi
echo -e "${GREEN}�?Python依赖已安�?{NC}"
echo ""

# 8. 配置环境变量
echo -e "${YELLOW}📍 第八步：配置环境变量...${NC}"
if [ ! -f ".env.trading" ]; then
    echo -e "${RED}�?错误�?env.trading 文件不存�?{NC}"
    echo ""
    echo "请创�?.env.trading 文件，添加以下内容："
    echo ""
    echo "OKX_API_KEY=your_api_key_here"
    echo "OKX_SECRET_KEY=your_secret_key_here"
    echo "OKX_PASSPHRASE=your_passphrase_here"
    echo ""
    echo "命令�?
    echo "  nano .env.trading"
    echo ""
    exit 1
fi
echo -e "${GREEN}�?环境变量已配�?{NC}"
echo ""

# 9. 测试API连接
echo -e "${YELLOW}📍 第九步：测试API连接...${NC}"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
try:
    from okx_client import OKXClient
    import asyncio

    async def test():
        client = OKXClient()
        await client.initialize()
        ticker = await client.get_ticker('XAU-USDT-SWAP')
        if ticker:
            print(f"�?API连接成功！当前黄金价�? ${ticker['last']}")
            return True
        else:
            print("�?无法获取行情")
            return False

    result = asyncio.run(test())
    sys.exit(0 if result else 1)
except Exception as e:
    print(f"�?API连接失败: {e}")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo -e "${RED}�?API连接测试失败${NC}"
    exit 1
fi
echo ""

# 10. 启动系统
echo -e "${YELLOW}📍 第十步：启动系统...${NC}"
echo ""
echo "=========================================="
echo -e "${GREEN}�?部署完成�?{NC}"
echo "=========================================="
echo ""
echo "🎯 系统已准备就�?
echo ""
echo "📋 启动选项�?
echo ""
echo "1️⃣  前台运行（可以看到实时输出）�?
echo "   python aurum_24h_service.py"
echo ""
echo "2️⃣  后台运行（推荐）�?
echo "   nohup python aurum_24h_service.py > aurum_24h_output.log 2>&1 &"
echo ""
echo "3️⃣  使用screen运行（推荐）�?
echo "   screen -S aurum"
echo "   python aurum_24h_service.py"
echo "   # Ctrl+A, 然后按D 分离"
echo ""
echo "📝 查看日志�?
echo "   tail -f aurum_24h.log"
echo ""
echo "🛑 停止系统�?
echo "   Ctrl+C (前台运行)"
echo "   kill <PID> (后台运行)"
echo "   screen -X -S aurum quit (screen运行)"
echo ""
echo "=========================================="
echo ""

# 询问是否启动系统
read -p "是否现在启动系统�?y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 启动系统...${NC}"
    echo ""
    python aurum_24h_service.py
else
    echo -e "${YELLOW}⏭️  跳过启动${NC}"
    echo ""
    echo "稍后可以使用以下命令启动�?
    echo "  cd ~/GOLD-QUANT"
    echo "  source venv/bin/activate"
    echo "  python aurum_24h_service.py"
fi
