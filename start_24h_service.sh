#!/bin/bash
# AURUM 24小时后台交易系统启动脚本 (Linux/Mac)

echo ""
echo "🚀 AURUM 24小时后台交易系统启动"
echo "===================================="
echo ""

# 检查Python版本
echo "📍 检查Python环境..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "   Python版本: $python_version"

# 检查依赖
echo ""
echo "📍 检查依赖..."
python -c "import pandas; import numpy; import sklearn; import aiohttp; print('   ✅ 所有依赖已安装')" 2>/dev/null || {
    echo "   ⚠️  缺少依赖，正在安装..."
    pip install -r requirements.txt
}

# 检查API配置
echo ""
echo "📍 检查API配置..."
if [ -f ".env.trading" ]; then
    echo "   ✅ .env.trading 文件存在"
    if grep -q "OKX_API_KEY=" .env.trading; then
        echo "   ✅ API密钥已配置"
    else
        echo "   ⚠️  API密钥未配置，请编辑 .env.trading"
        exit 1
    fi
else
    echo "   ⚠️  .env.trading 文件不存在"
    echo "   请复制 .env.trading.example 为 .env.trading 并填入API密钥"
    exit 1
fi

# 启动系统
echo ""
echo "================================"
echo "🎯 启动24小时后台交易系统"
echo "📊 模式: 16-Agent + 5分钟K线"
echo "🔔 通知: 飞书实时推送"
echo "================================"
echo ""
echo "💡 提示："
echo "- 系统会每5分钟分析一次行情"
echo "- 有交易信号时会发送飞书通知"
echo "- 按 Ctrl+C 停止系统"
echo ""

python aurum_24h_service.py
