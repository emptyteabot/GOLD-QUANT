# 🚀 AURUM 腾讯云部�?- 最终指�?
## �?部署文件已准�?
所有部署文件都已创建在 `~/Desktop/GOLD-QUANT` 目录中�?
---

## 🚀 快速部署（Windows用户�?
### 第一步：打开命令�?
```bash
# 进入项目目录
cd ~/Desktop/GOLD-QUANT

# 或在文件管理器中右键 �?在此处打开PowerShell
```

### 第二步：运行部署脚本

```bash
# 方式一：使用批处理脚本（推荐）
deploy.bat

# 方式二：使用PowerShell
powershell -ExecutionPolicy Bypass -File deploy.ps1
```

脚本会自动：
1. �?检查所有必要文�?2. �?验证SSH连接
3. �?上传文件到服务器
4. �?在服务器上执行部�?5. �?启动系统

---

## 📋 部署前检�?
### 1. 确保API密钥已配�?
编辑 `.env.trading` 文件�?
```bash
# 打开文件
notepad .env.trading

# 修改以下内容（不要改�?your_api_key_here）：
OKX_API_KEY=your_actual_api_key
OKX_SECRET_KEY=your_actual_secret_key
OKX_PASSPHRASE=your_actual_passphrase
```

### 2. 确保所有文件都在项目目�?
```
~/Desktop/GOLD-QUANT/
├── aurum_24h_service.py
├── agent_16_scalping_system.py
├── scalping_engine.py
├── okx_client.py
├── risk_manager.py
├── config.py
├── requirements.txt
├── .env.trading
├── install.sh
└── deploy.bat
```

---

## 🎯 部署步骤详解

### 步骤1：检查文�?
脚本会检查以下文件是否存在：
- aurum_24h_service.py
- agent_16_scalping_system.py
- scalping_engine.py
- okx_client.py
- risk_manager.py
- config.py
- requirements.txt
- .env.trading
- install.sh

### 步骤2：验证SSH连接

脚本会尝试连接到服务器：
- 服务�? 43.135.51.214
- 用户: ubuntu
- 密码: <SERVER_PASSWORD>

### 步骤3：上传文�?
脚本会上传所有文件到服务器的 `~/GOLD-QUANT` 目录�?
### 步骤4：执行部�?
脚本会在服务器上运行 `install.sh`，自动完成：
- 更新系统
- 安装Python和依�?- 创建虚拟环境
- 安装Python�?- 测试API连接
- 创建systemd服务
- 启动系统

---

## 📊 部署完成�?
### 查看系统状�?
```bash
ssh ubuntu@43.135.51.214
sudo systemctl status aurum
```

应该看到�?```
�?aurum.service - AURUM 24H Trading System
   Loaded: loaded (/etc/systemd/system/aurum.service; enabled; vendor preset: enabled)
   Active: active (running) since ...
```

### 查看实时日志

```bash
ssh ubuntu@43.135.51.214
tail -f ~/GOLD-QUANT/aurum_24h.log
```

应该看到�?```
2026-03-20 10:00:00 - INFO - 🚀 AURUM 24小时后台交易系统启动
2026-03-20 10:00:05 - INFO - 💰 账户信息:
2026-03-20 10:00:05 - INFO -    总权�? $10,000.00
```

### 监控飞书通知

系统有交易信号时，会自动发送飞书通知�?
---

## 🛠�?常用命令

### 连接到服务器

```bash
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

### 查看系统状�?
```bash
sudo systemctl status aurum
```

### 查看日志

```bash
# 实时查看
tail -f ~/GOLD-QUANT/aurum_24h.log

# 查看最�?00�?tail -100 ~/GOLD-QUANT/aurum_24h.log

# 搜索做多信号
grep "做多" ~/GOLD-QUANT/aurum_24h.log
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

## 🚨 故障排查

### 问题1：SSH连接失败

**错误**: `无法连接到服务器`

**解决方案**:
1. 检查IP地址: 43.135.51.214
2. 检查用户名: ubuntu
3. 检查网络连�?4. 尝试手动连接: `ssh ubuntu@43.135.51.214`

### 问题2：文件上传失�?
**错误**: `上传失败`

**解决方案**:
1. 检查所有文件是否存�?2. 检查网络连�?3. 尝试手动上传: `scp -r . ubuntu@43.135.51.214:~/GOLD-QUANT/`

### 问题3：API密钥未配�?
**错误**: `API密钥未配置`

**解决方案**:
1. 编辑 `.env.trading` 文件
2. 填入你的OKX API密钥
3. 重新运行部署脚本

### 问题4：API连接失败

**错误**: `API连接失败`

**解决方案**:
1. 检查API密钥是否正确
2. 检查API密钥权限
3. 检查网络连�?4. 查看日志了解详情

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

### 2. 查看日志

```bash
ssh ubuntu@43.135.51.214
tail -100 ~/GOLD-QUANT/aurum_24h.log
```

### 3. 监控飞书通知

系统有交易信号时，会自动发送飞书通知�?
### 4. 定期检�?
每天检查一次日志，确保系统正常运行�?
---

## 💡 最佳实�?
1. **定期检查日�?* - 监控系统状�?2. **定期备份** - 备份重要文件
3. **监控资源使用** - 确保服务器有足够资源
4. **设置告警** - 如果系统停止，自动重�?
---

## 🎯 下一�?
1. �?配置API密钥
2. �?运行部署脚本
3. �?验证系统运行
4. �?监控飞书通知
5. �?根据信号执行交易

---

**祝你交易顺利！🚀💰**

*最后更新：2026-03-20*
