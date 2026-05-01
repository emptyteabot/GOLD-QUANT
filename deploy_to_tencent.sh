#!/bin/bash
# AURUM 系统在腾讯云服务器上的部署脚�?
set -e

echo "=========================================="
echo "🚀 AURUM 系统部署到腾讯云服务�?
echo "=========================================="
echo ""

# 1. 更新系统
echo "📍 第一步：更新系统..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# 2. 安装Python和依�?echo "📍 第二步：安装Python和依�?.."
sudo apt-get install -y -qq python3 python3-pip python3-venv git curl wget

# 3. 检查Python版本
echo "📍 第三步：检查Python版本..."
python3 --version
pip3 --version

# 4. 创建项目目录
echo "📍 第四步：创建项目目录..."
mkdir -p ~/GOLD-QUANT
cd ~/GOLD-QUANT

# 5. 克隆或下载项�?echo "📍 第五步：下载项目文件..."
# 这里假设你已经上传了项目文件
# 如果需要从GitHub克隆，使用以下命令：
# git clone https://github.com/YOUR_USERNAME/GOLD-QUANT.git

# 6. 创建虚拟环境
echo "📍 第六步：创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 7. 安装Python依赖
echo "📍 第七步：安装Python依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 8. 配置环境变量
echo "📍 第八步：配置环境变量..."
if [ ! -f ".env.trading" ]; then
    echo "⚠️  .env.trading 文件不存在，请创�?
    echo "请编�?.env.trading 文件，添加以下内容："
    echo ""
    echo "OKX_API_KEY=your_api_key"
    echo "OKX_SECRET_KEY=your_secret_key"
    echo "OKX_PASSPHRASE=your_passphrase"
    echo ""
    exit 1
fi

# 9. 启动系统
echo "📍 第九步：启动AURUM系统..."
echo ""
echo "=========================================="
echo "�?部署完成�?
echo "=========================================="
echo ""
echo "🎯 启动系统�?
echo "   python aurum_24h_service.py"
echo ""
echo "📝 查看日志�?
echo "   tail -f aurum_24h.log"
echo ""
echo "🛑 停止系统�?
echo "   Ctrl+C"
echo ""

# 启动系统
python aurum_24h_service.py
