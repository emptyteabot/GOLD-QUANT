# 🚀 AURUM 系统部署到腾讯云服务�?
## 📋 服务器信�?
```
IP地址: 43.135.51.214
用户�? ubuntu
密码: <SERVER_PASSWORD>
系统: Linux (Ubuntu)
```

---

## 🚀 部署步骤

### 第一步：连接到服务器

**Windows用户（使用PuTTY或PowerShell�?**
```bash
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

**Linux/Mac用户:**
```bash
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

### 第二步：上传项目文件

**方式一：使用SCP上传**
```bash
# 从本地上传整个项目到服务�?scp -r ~/Desktop/GOLD-QUANT ubuntu@43.135.51.214:~/

# 或上传单个文�?scp ~/Desktop/GOLD-QUANT/aurum_24h_service.py ubuntu@43.135.51.214:~/GOLD-QUANT/
```

**方式二：在服务器上克隆GitHub**
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/GOLD-QUANT.git
cd GOLD-QUANT
```

### 第三步：配置环境变量

连接到服务器后：

```bash
cd ~/GOLD-QUANT

# 创建 .env.trading 文件
nano .env.trading

# 添加以下内容�?OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here
OKX_PASSPHRASE=your_passphrase_here

# 保存并退出（Ctrl+X, 然后按Y, 然后按Enter�?```

### 第四步：安装依赖

```bash
# 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 安装Python和pip
sudo apt-get install -y python3 python3-pip python3-venv

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 第五步：启动系统

```bash
# 方式一：直接运行（前台�?python aurum_24h_service.py

# 方式二：后台运行（推荐）
nohup python aurum_24h_service.py > aurum_24h_output.log 2>&1 &

# 方式三：使用screen（推荐）
screen -S aurum
python aurum_24h_service.py
# Ctrl+A, 然后按D 分离
```

---

## 📊 常用命令

### 查看系统状�?
```bash
# 查看进程
ps aux | grep aurum_24h_service

# 查看日志
tail -f aurum_24h.log

# 查看实时日志（最�?00行）
tail -100 aurum_24h.log

# 搜索特定内容
grep "做多" aurum_24h.log
```

### 管理后台进程

```bash
# 查看所有screen会话
screen -ls

# 重新连接screen会话
screen -r aurum

# 分离screen会话
# Ctrl+A, 然后按D

# 杀死screen会话
screen -X -S aurum quit

# 杀死进�?kill <PID>
kill -9 <PID>  # 强制杀�?```

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

### 方式一：直接运行（前台�?
```bash
python aurum_24h_service.py
```

**优点:**
- 简单直�?- 可以看到实时输出

**缺点:**
- 关闭终端后系统停�?- 不适合长期运行

### 方式二：nohup后台运行

```bash
nohup python aurum_24h_service.py > aurum_24h_output.log 2>&1 &
```

**优点:**
- 关闭终端后系统继续运�?- 输出保存到日志文�?
**缺点:**
- 无法实时交互
- 需要手动管理进�?
### 方式三：screen会话（推荐）

```bash
screen -S aurum
python aurum_24h_service.py
# Ctrl+A, 然后按D 分离
```

**优点:**
- 可以随时重新连接
- 可以看到实时输出
- 关闭终端后系统继续运�?
**缺点:**
- 需要学习screen命令

### 方式四：systemd服务（最推荐�?
创建 `/etc/systemd/system/aurum.service`�?
```ini
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

[Install]
WantedBy=multi-user.target
```

然后运行�?
```bash
sudo systemctl daemon-reload
sudo systemctl enable aurum
sudo systemctl start aurum
sudo systemctl status aurum
```

---

## 📝 日志管理

### 查看日志

```bash
# 查看最�?00�?tail -100 aurum_24h.log

# 实时查看日志
tail -f aurum_24h.log

# 查看特定时间的日�?grep "2026-03-20 10:" aurum_24h.log

# 查看所有做多信�?grep "做多" aurum_24h.log

# 查看所有错�?grep "ERROR" aurum_24h.log
```

### 日志轮转

为了防止日志文件过大，可以设置日志轮转：

创建 `/etc/logrotate.d/aurum`�?
```
/home/ubuntu/GOLD-QUANT/aurum_24h.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
}
```

---

## 🚨 故障排查

### 系统无法启动

**错误**: `ModuleNotFoundError: No module named 'okx_client'`

**解决方案**:
```bash
# 确保虚拟环境已激�?source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
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
# 检查Webhook URL
grep "webhook_url" aurum_24h_service.py

# 检查网络连�?curl -X POST https://open.larksuite.com/open-apis/bot/v2/hook/6121a7d9-b385-4cc0-b969-b120a4229c9a
```

---

## 📊 监控系统

### 查看系统资源使用

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
# 1. 连接到服务器
ssh ubuntu@43.135.51.214

# 2. 上传项目文件
# 使用SCP或git clone

# 3. 进入项目目录
cd ~/GOLD-QUANT

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装依赖
pip install -r requirements.txt

# 6. 配置API密钥
nano .env.trading
# 添加API密钥

# 7. 启动系统（使用screen�?screen -S aurum
python aurum_24h_service.py

# 8. 分离screen会话
# Ctrl+A, 然后按D

# 9. 查看日志
tail -f aurum_24h.log
```

---

## 💡 最佳实�?
1. **使用虚拟环境** - 隔离项目依赖
2. **使用screen或systemd** - 确保系统持续运行
3. **定期检查日�?* - 监控系统状�?4. **设置日志轮转** - 防止日志文件过大
5. **定期备份** - 备份重要文件

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
