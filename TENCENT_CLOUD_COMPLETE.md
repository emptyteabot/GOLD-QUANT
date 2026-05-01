# 🚀 腾讯云服务器部署 - 完整指南

## 📋 服务器信�?
```
IP地址: 43.135.51.214
用户�? ubuntu
密码: <SERVER_PASSWORD>
系统: Linux (Ubuntu)
```

---

## 🚀 快速部署（3步）

### 第一步：连接到服务器

```bash
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

### 第二步：上传项目文件

**在本地电脑上运行�?*

```bash
# 上传整个项目
scp -r ~/Desktop/GOLD-QUANT ubuntu@43.135.51.214:~/

# 或使用WinSCP/FileZilla等工具上�?```

### 第三步：一键部�?
**在服务器上运行：**

```bash
cd ~/GOLD-QUANT
chmod +x deploy_one_click.sh
./deploy_one_click.sh
```

脚本会自动：
- �?更新系统
- �?安装Python和依�?- �?创建虚拟环境
- �?安装Python�?- �?测试API连接
- �?启动系统

---

## 📝 详细部署步骤

### 步骤1：连接到服务�?
**Windows用户（使用PowerShell�?**
```powershell
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

**Linux/Mac用户:**
```bash
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

### 步骤2：上传项目文�?
**方式一：使用SCP（推荐）**

在本地电脑上运行�?```bash
# 上传整个项目目录
scp -r ~/Desktop/GOLD-QUANT ubuntu@43.135.51.214:~/

# 或上传单个文�?scp ~/Desktop/GOLD-QUANT/aurum_24h_service.py ubuntu@43.135.51.214:~/GOLD-QUANT/
scp ~/Desktop/GOLD-QUANT/requirements.txt ubuntu@43.135.51.214:~/GOLD-QUANT/
```

**方式二：使用WinSCP（Windows�?*
1. 下载并安�?WinSCP
2. 连接到服务器
3. 拖拽文件上传

**方式三：使用FileZilla（跨平台�?*
1. 下载并安�?FileZilla
2. 连接到服务器
3. 拖拽文件上传

### 步骤3：配置API密钥

在服务器上运行：

```bash
cd ~/GOLD-QUANT

# 创建 .env.trading 文件
nano .env.trading

# 添加以下内容�?OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here
OKX_PASSPHRASE=your_passphrase_here

# 保存并退出：Ctrl+X, 然后按Y, 然后按Enter
```

### 步骤4：安装依�?
```bash
# 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 安装Python
sudo apt-get install -y python3 python3-pip python3-venv

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 步骤5：启动系�?
**方式一：前台运�?*
```bash
python aurum_24h_service.py
```

**方式二：后台运行（推荐）**
```bash
nohup python aurum_24h_service.py > aurum_24h_output.log 2>&1 &
```

**方式三：使用screen（推荐）**
```bash
screen -S aurum
python aurum_24h_service.py
# Ctrl+A, 然后按D 分离
```

**方式四：使用systemd（最推荐�?*
```bash
# 创建服务文件
sudo nano /etc/systemd/system/aurum.service

# 添加以下内容�?[Unit]
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

[Install]
WantedBy=multi-user.target

# 保存并退出：Ctrl+X, 然后按Y, 然后按Enter

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable aurum
sudo systemctl start aurum
sudo systemctl status aurum
```

---

## 📊 常用命令

### 查看系统状�?
```bash
# 查看进程
ps aux | grep aurum_24h_service

# 查看日志
tail -f aurum_24h.log

# 查看最�?00行日�?tail -100 aurum_24h.log

# 搜索特定内容
grep "做多" aurum_24h.log
```

### 管理screen会话

```bash
# 查看所有screen会话
screen -ls

# 重新连接screen会话
screen -r aurum

# 分离screen会话
# Ctrl+A, 然后按D

# 杀死screen会话
screen -X -S aurum quit
```

### 管理systemd服务

```bash
# 查看服务状�?sudo systemctl status aurum

# 启动服务
sudo systemctl start aurum

# 停止服务
sudo systemctl stop aurum

# 重启服务
sudo systemctl restart aurum

# 查看服务日志
sudo journalctl -u aurum -f
```

### 文件操作

```bash
# 查看文件
cat aurum_24h.log

# 查看文件大小
du -h aurum_24h.log

# 清空日志文件
> aurum_24h.log

# 下载日志文件到本�?scp ubuntu@43.135.51.214:~/GOLD-QUANT/aurum_24h.log ~/Desktop/
```

---

## 🛠�?部署方式对比

| 方式 | 优点 | 缺点 | 推荐�?|
|------|------|------|--------|
| 前台运行 | 简单直�?| 关闭终端后停�?| �?|
| nohup后台 | 关闭终端后继续运�?| 无法交互 | ⭐⭐ |
| screen会话 | 可随时重新连�?| 需要学习命�?| ⭐⭐�?|
| systemd服务 | 自动启动、自动重�?| 需要sudo权限 | ⭐⭐⭐⭐�?|

---

## 🚨 故障排查

### 连接失败

**错误**: `Permission denied (publickey,password)`

**解决方案**:
1. 检查IP地址是否正确
2. 检查用户名是否正确
3. 检查密码是否正�?4. 检查网络连�?
### 文件上传失败

**错误**: `scp: command not found`

**解决方案**:
1. 使用WinSCP或FileZilla
2. 在服务器上使用git clone

### Python依赖安装失败

**错误**: `pip: command not found`

**解决方案**:
```bash
# 安装pip
sudo apt-get install -y python3-pip

# 或使用python3 -m pip
python3 -m pip install -r requirements.txt
```

### API连接失败

**错误**: `�?无法获取账户信息`

**解决方案**:
```bash
# 检�?.env.trading 文件
cat .env.trading

# 检查API密钥是否正确
# 检查网络连�?ping api.okx.com
```

### 飞书通知失败

**错误**: `�?飞书通知失败`

**解决方案**:
```bash
# 检查网络连�?curl -X POST https://open.larksuite.com/open-apis/bot/v2/hook/6121a7d9-b385-4cc0-b969-b120a4229c9a

# 检查Webhook URL是否正确
grep "webhook_url" aurum_24h_service.py
```

---

## 📊 监控系统

### 查看系统资源

```bash
# 查看CPU和内存使�?top

# 查看磁盘使用
df -h

# 查看进程详情
ps aux | grep python
```

### 设置告警

```bash
# 如果进程停止，自动重�?# 使用systemd的Restart=always选项

# 或使用cron定期检�?crontab -e

# 添加以下行：
*/5 * * * * pgrep -f "aurum_24h_service" || nohup python /home/ubuntu/GOLD-QUANT/aurum_24h_service.py > /home/ubuntu/GOLD-QUANT/aurum_24h_output.log 2>&1 &
```

---

## 🎯 完整部署流程

```bash
# 1. 本地上传项目
scp -r ~/Desktop/GOLD-QUANT ubuntu@43.135.51.214:~/

# 2. 连接到服务器
ssh ubuntu@43.135.51.214

# 3. 进入项目目录
cd ~/GOLD-QUANT

# 4. 配置API密钥
nano .env.trading
# 添加API密钥

# 5. 一键部�?chmod +x deploy_one_click.sh
./deploy_one_click.sh

# 6. 系统会自动启�?# 或手动启动：
# python aurum_24h_service.py

# 7. 查看日志
tail -f aurum_24h.log
```

---

## 💡 最佳实�?
1. **使用虚拟环境** - 隔离项目依赖
2. **使用systemd** - 确保系统持续运行和自动重�?3. **定期检查日�?* - 监控系统状�?4. **设置日志轮转** - 防止日志文件过大
5. **定期备份** - 备份重要文件
6. **监控资源使用** - 确保服务器有足够资源

---

## 📞 支持

如遇到问题，请检查：

1. 网络连接是否正常
2. API密钥是否正确配置
3. 日志文件中的错误信息
4. 服务器资源是否充�?
---

**祝你交易顺利！🚀💰**

*最后更新：2026-03-20*
