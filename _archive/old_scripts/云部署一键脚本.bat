@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║              ☁️ 云服务器一键部署脚本                          ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 📋 部署步骤：
echo.
echo 1. 购买云服务器（阿里云/腾讯云）
echo    配置：1核2G，Ubuntu 20.04
echo    费用：约 ¥100/年
echo.
echo 2. 连接服务器
echo    ssh root@你的服务器IP
echo.
echo 3. 安装Python
echo    apt update ^&^& apt install python3 python3-pip -y
echo.
echo 4. 上传代码
echo    scp -r 黄金文件夹 root@服务器IP:/root/
echo.
echo 5. 安装依赖
echo    cd /root/黄金
echo    pip3 install -r requirements.txt
echo.
echo 6. 后台运行
echo    nohup python3 国内版-一键赚钱.py ^> output.log 2^>^&1 ^&
echo.
echo 7. 查看日志
echo    tail -f output.log
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo 💡 详细教程请查看：云服务器部署教程.md
echo.
pause


