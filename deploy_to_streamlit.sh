#!/bin/bash
# 快速部署到Streamlit Cloud

echo "🚀 AURUM 系统部署到Streamlit Cloud"
echo "===================================="
echo ""

# 检查Git
if ! command -v git &> /dev/null; then
    echo "�?Git未安装，请先安装Git"
    exit 1
fi

# 检查GitHub用户�?read -p "请输入你的GitHub用户�? " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "�?GitHub用户名不能为�?
    exit 1
fi

# 初始化Git仓库
echo ""
echo "📍 初始化Git仓库..."
git init
git add .
git commit -m "Initial commit: AURUM scalping system"
git branch -M main

# 添加远程仓库
echo ""
echo "📍 添加远程仓库..."
git remote add origin https://github.com/$GITHUB_USERNAME/GOLD-QUANT.git

# 推送到GitHub
echo ""
echo "📍 推送代码到GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "�?代码已推送到GitHub"
    echo ""
    echo "📋 下一步："
    echo "1. 访问 https://streamlit.io/cloud"
    echo "2. 用GitHub账户登录"
    echo "3. 点击 'New app'"
    echo "4. 选择仓库: $GITHUB_USERNAME/GOLD-QUANT"
    echo "5. 选择分支: main"
    echo "6. 选择文件: app_scalping_live.py"
    echo "7. 点击 'Deploy'"
    echo ""
    echo "⚙️  部署完成后，在Streamlit Cloud中设置Secrets�?
    echo "OKX_API_KEY = 'your_api_key'"
    echo "OKX_SECRET_KEY = 'your_secret_key'"
    echo "OKX_PASSPHRASE = 'your_passphrase'"
else
    echo "�?推送失败，请检查GitHub连接"
    exit 1
fi
