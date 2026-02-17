# AURUM Railway 快速参考

## 🚀 一键部署

```bash
./deploy-to-railway.sh
```

---

## 📝 常用命令

### 部署相关
```bash
railway login              # 登录Railway
railway init               # 初始化项目
railway up                 # 部署到Railway
railway status             # 查看状态
railway open               # 打开Dashboard
```

### 日志和监控
```bash
railway logs               # 查看日志
railway logs --follow      # 实时日志
railway logs --limit 100   # 最近100行
```

### 环境变量
```bash
railway variables          # 查看所有变量
railway variables set KEY=VALUE  # 设置变量
railway variables delete KEY     # 删除变量
```

### 服务管理
```bash
railway restart            # 重启服务
railway down               # 停止服务
railway environment        # 管理环境
```

---

## 🔑 必需环境变量

### OKX交易所
```
OKX_API_KEY
OKX_SECRET_KEY
OKX_PASSPHRASE
```

### 飞书通知
```
FEISHU_WEBHOOK_URL
```

### AI和数据
```
GEMINI_API_KEY
TUSHARE_TOKEN
ALPHAVANTAGE_API_KEY
```

---

## 📊 优化参数（推荐）

```bash
# 仓位和风控
POSITION_SIZE_PCT=0.30
BASE_LEVERAGE=5
STOP_LOSS_PCT=0.015

# 决策阈值
MIN_CONFIDENCE=0.50
MIN_SIGNAL=0.20
MIN_CONSENSUS=0.50

# 技术指标
ADX_RANGE_THRESHOLD=15
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
```

---

## 🐛 故障排查

### 部署失败
```bash
# 检查日志
railway logs

# 重新部署
railway up --force

# 检查环境变量
railway variables
```

### 服务崩溃
```bash
# 查看最近日志
railway logs --limit 200

# 重启服务
railway restart

# 检查资源使用
railway status
```

### 连接问题
```bash
# 测试OKX连接
python -c "from okx_client import OKXClient; print(OKXClient().get_account_balance())"

# 测试飞书推送
python -c "from feishu_notifier import FeishuNotifier; FeishuNotifier().send_text('测试')"
```

---

## 💰 成本估算

| 计划 | 价格 | 适用场景 |
|------|------|----------|
| Hobby | $0 (免费$5) | 测试、学习 |
| Pro | $20/月 | 生产环境 |

---

## 📚 相关文档

- [完整部署指南](./docs/Railway部署指南.md)
- [系统技术文档](./AURUM系统完整技术文档.md)
- [项目全景](./AURUM项目全景.md)

---

## ⚠️ 重要提示

1. **不要提交密钥到Git**
   - 使用Railway环境变量
   - 检查.gitignore

2. **监控资源使用**
   - 定期查看Dashboard
   - 设置告警通知

3. **定期备份**
   - 导出交易记录
   - 备份配置文件

4. **安全第一**
   - 使用只读API（如可能）
   - 启用2FA认证
   - 定期轮换密钥

---

**快速开始：** `./deploy-to-railway.sh` 🚀
