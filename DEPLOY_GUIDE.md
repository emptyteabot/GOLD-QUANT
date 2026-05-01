# 🚀 AURUM 腾讯云一键部署指�?
## 📋 前置要求

### 1. 安装sshpass（用于自动输入密码）

**Windows (Git Bash �?WSL):**
```bash
# 如果使用WSL
sudo apt-get install sshpass

# 如果使用Git Bash，需要手动下载或使用其他方式
```

**macOS:**
```bash
brew install sshpass
```

**Linux:**
```bash
sudo apt-get install sshpass
```

### 2. 配置API密钥

编辑 `.env.trading` 文件，填入你的OKX API密钥�?
```bash
nano .env.trading
```

修改以下内容�?```
OKX_API_KEY=your_actual_api_key
OKX_SECRET_KEY=your_actual_secret_key
OKX_PASSPHRASE=your_actual_passphrase
```

---

## 🚀 一键部�?
### 方式一：使用Python部署脚本（推荐）

```bash
cd ~/Desktop/GOLD-QUANT
python3 deploy.py
```

脚本会自动：
1. �?检查所有必要文�?2. �?上传文件到服务器
3. �?在服务器上执行部�?4. �?检查部署状�?
### 方式二：手动部署

#### 第一步：上传文件

```bash
cd ~/Desktop/GOLD-QUANT

# 上传整个项目
scp -r . ubuntu@43.135.51.214:~/GOLD-QUANT/
```

#### 第二步：连接到服务器

```bash
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

#### 第三步：执行部署脚本

```bash
cd ~/GOLD-QUANT
chmod +x install.sh
./install.sh
```

---

## 📊 部署过程

部署脚本会执行以下步骤：

```
1. 更新系统
   �?2. 安装系统依赖 (Python, pip, git�?
   �?3. 创建虚拟环境
   �?4. 安装Python依赖
   �?5. 检查配置文�?   �?6. 测试API连接
   �?7. 创建systemd服务
   �?8. 启动系统
   �?9. 显示完成信息
```

---

## 📝 部署完成�?
### 查看系统状�?
```bash
ssh ubuntu@43.135.51.214
sudo systemctl status aurum
```

### 查看实时日志

```bash
ssh ubuntu@43.135.51.214
tail -f ~/GOLD-QUANT/aurum_24h.log
```

### 查看实时日志（systemd�?
```bash
ssh ubuntu@43.135.51.214
sudo journalctl -u aurum -f
```

### 停止系统

```bash
ssh ubuntu@43.135.51.214
sudo systemctl stop aurum
```

### 重启系统

```bash
ssh ubuntu@43.135.51.214
sudo systemctl restart aurum
```

---

## 🛠�?故障排查

### 问题1：sshpass 未安�?
**错误**: `sshpass: command not found`

**解决方案**:
```bash
# Ubuntu/Debian
sudo apt-get install sshpass

# macOS
brew install sshpass

# Windows (WSL)
sudo apt-get install sshpass
```

### 问题2：连接被拒绝

**错误**: `Permission denied (publickey,password)`

**解决方案**:
1. 检查IP地址是否正确: 43.135.51.214
2. 检查用户名是否正确: ubuntu
3. 检查密码是否正�? <SERVER_PASSWORD>
4. 检查网络连�?
### 问题3：API密钥未配�?
**错误**: `API密钥未配置`

**解决方案**:
```bash
# 编辑 .env.trading 文件
nano .env.trading

# 填入你的OKX API密钥
OKX_API_KEY=your_actual_api_key
OKX_SECRET_KEY=your_actual_secret_key
OKX_PASSPHRASE=your_actual_passphrase
```

### 问题4：API连接失败

**错误**: `API连接失败`

**解决方案**:
1. 检查API密钥是否正确
2. 检查API密钥权限是否足够
3. 检查网络连�?4. 检查OKX服务是否正常

---

## 📊 服务器信�?
```
IP地址: 43.135.51.214
用户�? ubuntu
密码: <SERVER_PASSWORD>
系统: Linux (Ubuntu)
```

---

## 🎯 部署完成后的操作

### 1. 验证系统运行

```bash
ssh ubuntu@43.135.51.214
sudo systemctl status aurum
```

应该看到�?```
�?aurum.service - AURUM 24H Trading System
   Loaded: loaded (/etc/systemd/system/aurum.service; enabled; vendor preset: enabled)
   Active: active (running) since ...
```

### 2. 查看日志

```bash
ssh ubuntu@43.135.51.214
tail -100 ~/GOLD-QUANT/aurum_24h.log
```

应该看到�?```
2026-03-20 10:00:00 - INFO - 🚀 AURUM 24小时后台交易系统启动
2026-03-20 10:00:05 - INFO - 💰 账户信息:
2026-03-20 10:00:05 - INFO -    总权�? $10,000.00
```

### 3. 监控飞书通知

系统有交易信号时，会自动发送飞书通知�?
---

## 💡 常用命令速查

```bash
# 连接到服务器
ssh ubuntu@43.135.51.214

# 查看系统状�?sudo systemctl status aurum

# 查看日志
tail -f ~/GOLD-QUANT/aurum_24h.log

# 停止系统
sudo systemctl stop aurum

# 重启系统
sudo systemctl restart aurum

# 查看进程
ps aux | grep aurum_24h_service

# 查看systemd日志
sudo journalctl -u aurum -f

# 下载日志到本�?scp ubuntu@43.135.51.214:~/GOLD-QUANT/aurum_24h.log ~/Desktop/
```

---

## 🎯 下一�?
1. �?安装sshpass
2. �?配置API密钥
3. �?运行部署脚本
4. �?验证系统运行
5. �?监控飞书通知

---

**祝你交易顺利！🚀💰**

*最后更新：2026-03-20*
