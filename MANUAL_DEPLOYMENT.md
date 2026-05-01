# 🚀 AURUM 手动部署指南 - 在服务器上运�?
## 📋 部署步骤

### 第一步：连接到服务器

```bash
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

### 第二步：创建项目目录

```bash
mkdir -p ~/GOLD-QUANT
cd ~/GOLD-QUANT
```

### 第三步：上传文件

在本地电脑上运行（不是在服务器上）：

```bash
cd ~/Desktop/GOLD-QUANT
scp -r *.py requirements.txt .env.trading ubuntu@43.135.51.214:~/GOLD-QUANT/
```

### 第四步：在服务器上执行部�?
连接到服务器后，运行以下命令�?
```bash
cd ~/GOLD-QUANT

# 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 安装依赖
sudo apt-get install -y python3 python3-pip python3-venv git curl wget

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt

# 测试API连接
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
        print(f"�?API连接成功！当前黄金价�? ${ticker['last']}")
        return True
    return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
PYEOF

# 创建systemd服务
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

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable aurum
sudo systemctl start aurum

# 检查状�?sudo systemctl status aurum

# 查看日志
tail -f aurum_24h.log
```

---

## 🎯 完整部署命令（一次性复制粘贴）

连接到服务器后，直接复制粘贴以下命令�?
```bash
cd ~/GOLD-QUANT && \
sudo apt-get update && \
sudo apt-get upgrade -y && \
sudo apt-get install -y python3 python3-pip python3-venv git curl wget && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip && \
pip install -r requirements.txt && \
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
        print(f"�?API连接成功！当前黄金价�? ${ticker['last']}")
        return True
    return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
PYEOF
&& \
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
&& \
sudo systemctl daemon-reload && \
sudo systemctl enable aurum && \
sudo systemctl start aurum && \
sudo systemctl status aurum && \
tail -f aurum_24h.log
```

---

## 📝 分步骤详�?
### 1. 连接到服务器
```bash
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

### 2. 进入项目目录
```bash
cd ~/GOLD-QUANT
```

### 3. 更新系统
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 4. 安装系统依赖
```bash
sudo apt-get install -y python3 python3-pip python3-venv git curl wget
```

### 5. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

### 6. 安装Python依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. 测试API连接
```bash
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
        print(f"�?API连接成功！当前黄金价�? ${ticker['last']}")
        return True
    return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
PYEOF
```

### 8. 创建systemd服务
```bash
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
```

### 9. 启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable aurum
sudo systemctl start aurum
```

### 10. 检查状�?```bash
sudo systemctl status aurum
```

### 11. 查看日志
```bash
tail -f aurum_24h.log
```

---

## 🛠�?常用命令

### 查看系统状�?```bash
sudo systemctl status aurum
```

### 查看实时日志
```bash
tail -f ~/GOLD-QUANT/aurum_24h.log
```

### 停止系统
```bash
sudo systemctl stop aurum
```

### 重启系统
```bash
sudo systemctl restart aurum
```

### 查看进程
```bash
ps aux | grep aurum_24h_service
```

### 查看systemd日志
```bash
sudo journalctl -u aurum -f
```

---

## 📊 部署完成�?
### 验证系统运行

```bash
sudo systemctl status aurum
```

应该看到�?```
�?aurum.service - AURUM 24H Trading System
   Loaded: loaded (/etc/systemd/system/aurum.service; enabled; vendor preset: enabled)
   Active: active (running) since ...
```

### 查看日志

```bash
tail -100 ~/GOLD-QUANT/aurum_24h.log
```

应该看到�?```
2026-03-20 10:00:00 - INFO - 🚀 AURUM 24小时后台交易系统启动
2026-03-20 10:00:05 - INFO - 💰 账户信息:
2026-03-20 10:00:05 - INFO -    总权�? $10,000.00
```

---

**祝你交易顺利！🚀💰**
