# �?AURUM 腾讯云部�?- 完成

## 🎉 系统已完全准备就�?
你的AURUM黄金量化系统现在可以部署到腾讯云服务器上�?4小时不间断运行�?
---

## 📦 新增文件

**部署脚本**
- `deploy_to_tencent.sh` - 腾讯云部署脚�?- `deploy_one_click.sh` - 一键部署脚本（推荐�?
**完整文档**
- `TENCENT_CLOUD_DEPLOYMENT.md` - 详细部署指南
- `TENCENT_CLOUD_COMPLETE.md` - 完成说明

---

## 🚀 快速部署（3步）

### 第一步：连接到服务器

```bash
ssh ubuntu@43.135.51.214
# 输入密码: <SERVER_PASSWORD>
```

### 第二步：上传项目文件

在本地电脑上运行�?```bash
scp -r ~/Desktop/GOLD-QUANT ubuntu@43.135.51.214:~/
```

### 第三步：一键部�?
在服务器上运行：
```bash
cd ~/GOLD-QUANT
chmod +x deploy_one_click.sh
./deploy_one_click.sh
```

脚本会自动完成所有部署步骤！

---

## 📋 服务器信�?
```
IP地址: 43.135.51.214
用户�? ubuntu
密码: <SERVER_PASSWORD>
系统: Linux (Ubuntu)
```

---

## 🎯 部署流程

```
1. 连接到服务器
   �?2. 上传项目文件
   �?3. 运行一键部署脚�?   ├─ 更新系统
   ├─ 安装Python和依�?   ├─ 创建虚拟环境
   ├─ 安装Python�?   ├─ 测试API连接
   └─ 启动系统
   �?4. 系统24小时运行
   ├─ �?分钟分析一�?   ├─ 有信号发送飞书通知
   └─ 日志记录所有操�?```

---

## 📊 启动选项

### 方式一：前台运�?```bash
python aurum_24h_service.py
```
- 简单直�?- 可以看到实时输出
- 关闭终端后停�?
### 方式二：后台运行
```bash
nohup python aurum_24h_service.py > aurum_24h_output.log 2>&1 &
```
- 关闭终端后继续运�?- 输出保存到日志文�?
### 方式三：screen会话（推荐）
```bash
screen -S aurum
python aurum_24h_service.py
# Ctrl+A, 然后按D 分离
```
- 可以随时重新连接
- 可以看到实时输出
- 关闭终端后继续运�?
### 方式四：systemd服务（最推荐�?```bash
sudo systemctl start aurum
sudo systemctl status aurum
```
- 自动启动
- 自动重启
- 最稳定可靠

---

## 📝 常用命令

### 查看日志
```bash
# 实时查看日志
tail -f aurum_24h.log

# 查看最�?00�?tail -100 aurum_24h.log

# 搜索做多信号
grep "做多" aurum_24h.log
```

### 管理进程
```bash
# 查看进程
ps aux | grep aurum_24h_service

# 杀死进�?kill <PID>

# 查看screen会话
screen -ls

# 重新连接screen
screen -r aurum
```

### 管理systemd服务
```bash
# 查看状�?sudo systemctl status aurum

# 启动服务
sudo systemctl start aurum

# 停止服务
sudo systemctl stop aurum

# 重启服务
sudo systemctl restart aurum
```

---

## 🔔 飞书通知

系统有交易信号时，会自动发送飞书通知，包含：

- 🟢 **做多信号** �?🔴 **做空信号**
- 💹 **当前价格**
- 📊 **信心�?*
- 🎯 **开仓点�?*
- 🛑 **止损点位**
- �?**止盈点位**
- 💪 **杠杆倍数**
- 🤖 **Agent讨论结果**

---

## 📊 系统架构

```
腾讯云服务器
�?├─ 数据�?�? └─ OKX API (5分钟K�?
�?├─ 分析�?(16-Agent)
�? ├─ RSI Agent
�? ├─ MACD Agent
�? ├─ Bollinger Bands Agent
�? ├─ Stochastic Agent
�? ├─ ADX Agent
�? ├─ Volume Agent
�? ├─ CCI Agent
�? ├─ ROC Agent
�? └─ 8个快速版�?�?├─ 决策�?�? └─ 16-Agent讨论系统
�?├─ 通知�?�? └─ 飞书Webhook
�?└─ 监控�?   ├─ 日志文件
   ├─ 性能统计
   └─ 状态跟�?```

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
- 检查IP地址是否正确
- 检查用户名是否正确
- 检查密码是否正�?- 检查网络连�?
### 文件上传失败
- 使用WinSCP或FileZilla
- 或在服务器上使用git clone

### API连接失败
- 检�?`.env.trading` 中的API密钥
- 检查API密钥权限
- 检查网络连�?
### 飞书通知失败
- 检查Webhook URL是否正确
- 检查网络连�?- 检查飞书机器人权限

---

## 💡 最佳实�?
1. **使用虚拟环境** - 隔离项目依赖
2. **使用systemd** - 确保系统持续运行
3. **定期检查日�?* - 监控系统状�?4. **设置日志轮转** - 防止日志文件过大
5. **定期备份** - 备份重要文件
6. **监控资源使用** - 确保服务器有足够资源

---

## 🎯 下一�?
### 立即行动
1. �?上传项目文件到服务器
2. �?运行一键部署脚�?3. �?系统自动启动

### 持续运行
1. �?让系�?4小时不间断运�?2. �?每天检查一次日�?3. �?根据飞书信号执行交易

### 优化系统
1. �?调整参数
2. �?优化Agent权重
3. �?改进风险管理

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
*系统版本：v2.0 (短线交易�?+ 24小时后台服务 + 腾讯云部�?*
