#!/usr/bin/env python3
"""
AURUM 腾讯云部署脚�?- 使用paramiko库处理SSH密码认证
"""
import os
import sys
import paramiko
from pathlib import Path

class AURUMDeployer:
    def __init__(self):
        self.server_ip = "43.135.51.214"
        self.server_user = "ubuntu"
        self.server_password = "<SERVER_PASSWORD>"
        self.remote_dir = "~/GOLD-QUANT"
        self.local_dir = Path.home() / "Desktop" / "GOLD-QUANT"

    def deploy(self):
        print("\n" + "="*50)
        print("🚀 AURUM 腾讯云部�?)
        print("="*50 + "\n")

        # 连接到服务器
        print("📍 连接到服务器...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                self.server_ip,
                username=self.server_user,
                password=self.server_password,
                timeout=10
            )
            print("�?连接成功\n")
        except Exception as e:
            print(f"�?连接失败: {e}")
            return False

        # 创建远程目录
        print("📍 创建远程目录...")
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {self.remote_dir}")
        stdout.read()
        print("�?目录已创建\n")

        # 上传文件
        print("📍 上传文件...")
        sftp = ssh.open_sftp()

        files_to_upload = [
            "aurum_24h_service.py",
            "agent_16_scalping_system.py",
            "scalping_engine.py",
            "okx_client.py",
            "risk_manager.py",
            "config.py",
            "requirements.txt",
            ".env.trading"
        ]

        for file in files_to_upload:
            local_path = self.local_dir / file
            remote_path = f"/home/{self.server_user}/GOLD-QUANT/{file}"

            if not local_path.exists():
                print(f"   ⚠️  {file} 不存在，跳过")
                continue

            try:
                sftp.put(str(local_path), remote_path)
                print(f"   �?{file}")
            except Exception as e:
                print(f"   �?{file}: {e}")
                return False

        sftp.close()
        print("�?文件已上传\n")

        # 执行部署脚本
        print("📍 执行部署脚本...")
        print("   这可能需要几分钟...\n")

        deploy_commands = """
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
    try:
        client = OKXClient()
        await client.initialize()
        ticker = await client.get_ticker('XAU-USDT-SWAP')
        if ticker:
            print(f"�?API连接成功！价�? ${ticker['last']}")
            return True
    except:
        pass
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
echo "系统已启�?
echo ""
"""

        stdin, stdout, stderr = ssh.exec_command(deploy_commands)

        # 实时输出
        for line in stdout:
            print(line.rstrip())

        errors = stderr.read().decode()
        if errors:
            print(f"⚠️  {errors}")

        ssh.close()

        print("\n" + "="*50)
        print("�?部署完成�?)
        print("="*50 + "\n")

        print("🎯 系统已启动\n")
        print("📋 常用命令:\n")
        print("  查看日志:")
        print("    ssh ubuntu@43.135.51.214")
        print("    tail -f ~/GOLD-QUANT/aurum_24h.log\n")
        print("  查看状�?")
        print("    sudo systemctl status aurum\n")

        return True

if __name__ == "__main__":
    # 检查paramiko
    try:
        import paramiko
    except ImportError:
        print("�?需要安�?paramiko")
        print("运行: pip install paramiko")
        sys.exit(1)

    deployer = AURUMDeployer()
    if deployer.deploy():
        print("�?部署成功�?)
        sys.exit(0)
    else:
        print("�?部署失败�?)
        sys.exit(1)
