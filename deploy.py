#!/usr/bin/env python3
"""
AURUM 部署助手 - 自动上传和部署到腾讯�?"""
import os
import sys
import subprocess
import getpass
from pathlib import Path

class AURUMDeployer:
    def __init__(self):
        self.server_ip = "43.135.51.214"
        self.server_user = "ubuntu"
        self.server_password = "<SERVER_PASSWORD>"
        self.project_dir = Path(__file__).parent
        self.remote_dir = "~/GOLD-QUANT"

    def print_header(self, text):
        print("\n" + "="*50)
        print(f"🚀 {text}")
        print("="*50 + "\n")

    def print_step(self, step_num, text):
        print(f"📍 第{step_num}步：{text}...")

    def print_success(self, text):
        print(f"�?{text}")

    def print_error(self, text):
        print(f"�?{text}")

    def run_command(self, cmd, description=""):
        """运行命令"""
        if description:
            print(f"   运行: {description}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"   错误: {result.stderr}")
                return False
            if result.stdout:
                print(f"   {result.stdout.strip()}")
            return True
        except Exception as e:
            print(f"   异常: {e}")
            return False

    def check_files(self):
        """检查必要文�?""
        self.print_step(1, "检查必要文�?)

        required_files = [
            "aurum_24h_service.py",
            "agent_16_scalping_system.py",
            "scalping_engine.py",
            "okx_client.py",
            "risk_manager.py",
            "config.py",
            "requirements.txt",
            ".env.trading",
            "install.sh"
        ]

        missing_files = []
        for file in required_files:
            file_path = self.project_dir / file
            if not file_path.exists():
                missing_files.append(file)
            else:
                print(f"   �?{file}")

        if missing_files:
            self.print_error(f"缺少文件: {', '.join(missing_files)}")
            return False

        self.print_success("所有文件已检�?)
        return True

    def upload_files(self):
        """上传文件到服务器"""
        self.print_step(2, "上传文件到服务器")

        print(f"   目标: {self.server_user}@{self.server_ip}:{self.remote_dir}")
        print(f"   源目�? {self.project_dir}")

        # 使用scp上传
        cmd = f'scp -r {self.project_dir}/* {self.server_user}@{self.server_ip}:{self.remote_dir}/'

        print(f"   运行: scp 上传文件...")
        try:
            # 注意：这里需要交互式输入密码
            result = subprocess.run(
                f'sshpass -p "{self.server_password}" {cmd}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                self.print_success("文件已上�?)
                return True
            else:
                self.print_error(f"上传失败: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.print_error("上传超时")
            return False
        except Exception as e:
            self.print_error(f"上传异常: {e}")
            return False

    def deploy_on_server(self):
        """在服务器上执行部�?""
        self.print_step(3, "在服务器上执行部�?)

        deploy_cmd = f"""
cd {self.remote_dir}
chmod +x install.sh
./install.sh
"""

        cmd = f'sshpass -p "{self.server_password}" ssh {self.server_user}@{self.server_ip} "{deploy_cmd}"'

        print(f"   连接到服务器并执行部�?..")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=False,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                self.print_success("部署完成")
                return True
            else:
                self.print_error("部署失败")
                return False
        except subprocess.TimeoutExpired:
            self.print_error("部署超时")
            return False
        except Exception as e:
            self.print_error(f"部署异常: {e}")
            return False

    def check_deployment(self):
        """检查部署状�?""
        self.print_step(4, "检查部署状�?)

        cmd = f'sshpass -p "{self.server_password}" ssh {self.server_user}@{self.server_ip} "sudo systemctl status aurum"'

        print(f"   检查系统状�?..")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if "active (running)" in result.stdout:
                self.print_success("系统运行�?)
                return True
            else:
                print(result.stdout)
                return False
        except Exception as e:
            self.print_error(f"检查异�? {e}")
            return False

    def deploy(self):
        """完整部署流程"""
        self.print_header("AURUM 腾讯云部�?)

        print("📋 部署信息:")
        print(f"   服务�? {self.server_user}@{self.server_ip}")
        print(f"   项目目录: {self.project_dir}")
        print(f"   远程目录: {self.remote_dir}")
        print("")

        # 检查文�?        if not self.check_files():
            return False

        print("")

        # 上传文件
        if not self.upload_files():
            return False

        print("")

        # 部署
        if not self.deploy_on_server():
            return False

        print("")

        # 检查状�?        if not self.check_deployment():
            return False

        print("")
        self.print_header("部署成功�?)

        print("🎯 系统已启�?)
        print("")
        print("📋 常用命令:")
        print("")
        print("  查看日志:")
        print(f"    ssh {self.server_user}@{self.server_ip}")
        print(f"    tail -f ~/GOLD-QUANT/aurum_24h.log")
        print("")
        print("  查看状�?")
        print(f"    ssh {self.server_user}@{self.server_ip}")
        print(f"    sudo systemctl status aurum")
        print("")
        print("  停止系统:")
        print(f"    ssh {self.server_user}@{self.server_ip}")
        print(f"    sudo systemctl stop aurum")
        print("")

        return True

def main():
    # 检查sshpass
    result = subprocess.run("which sshpass", shell=True, capture_output=True)
    if result.returncode != 0:
        print("�?错误：sshpass 未安�?)
        print("")
        print("请先安装 sshpass:")
        print("  Ubuntu/Debian: sudo apt-get install sshpass")
        print("  macOS: brew install sshpass")
        print("  Windows: 使用 WSL �?Git Bash")
        sys.exit(1)

    deployer = AURUMDeployer()

    if deployer.deploy():
        print("�?部署完成�?)
        sys.exit(0)
    else:
        print("�?部署失败�?)
        sys.exit(1)

if __name__ == "__main__":
    main()
