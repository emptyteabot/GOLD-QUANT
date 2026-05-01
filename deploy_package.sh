#!/bin/bash
# 完整部署�?- 包含所有必要文�?
set -e

echo "📦 准备部署�?.."

# 创建临时目录
mkdir -p /tmp/aurum_deploy
cd /tmp/aurum_deploy

# 复制所有必要文�?cp ~/Desktop/GOLD-QUANT/aurum_24h_service.py .
cp ~/Desktop/GOLD-QUANT/agent_16_scalping_system.py .
cp ~/Desktop/GOLD-QUANT/scalping_engine.py .
cp ~/Desktop/GOLD-QUANT/okx_client.py .
cp ~/Desktop/GOLD-QUANT/risk_manager.py .
cp ~/Desktop/GOLD-QUANT/config.py .
cp ~/Desktop/GOLD-QUANT/requirements.txt .
cp ~/Desktop/GOLD-QUANT/.env.trading .

echo "�?部署包已准备"
ls -lh

