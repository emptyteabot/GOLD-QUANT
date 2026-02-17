# AURUM Railway 部署文件说明

## 📁 文件清单

本目录包含AURUM项目部署到Railway所需的所有配置文件和文档。

### 配置文件

| 文件名 | 用途 | 说明 |
|--------|------|------|
| `railway.json` | Railway配置 | 定义构建和部署命令 |
| `nixpacks.toml` | 构建配置 | 指定Python版本和依赖安装 |
| `Procfile` | 进程配置 | 定义启动命令 |
| `.env.railway` | 环境变量模板 | 包含所有需要的环境变量示例 |
| `.gitignore` | Git忽略规则 | 防止敏感文件被提交 |

### 脚本文件

| 文件名 | 用途 | 使用方法 |
|--------|------|----------|
| `deploy-to-railway.sh` | 自动部署脚本 | `./deploy-to-railway.sh` |

### 文档文件

| 文件名 | 用途 | 内容 |
|--------|------|------|
| `docs/Railway部署指南.md` | 完整部署指南 | 详细的部署步骤和故障排查 |
| `RAILWAY_QUICKSTART.md` | 快速参考 | 常用命令和配置速查 |
| `RAILWAY_CHECKLIST.md` | 部署检查清单 | 部署前后的完整检查项 |
| `README_RAILWAY.md` | 本文件 | 文件说明和快速开始 |

---

## 🚀 快速开始

### 方法一：使用自动化脚本（推荐）

```bash
# 1. 给脚本添加执行权限
chmod +x deploy-to-railway.sh

# 2. 运行部署脚本
./deploy-to-railway.sh
```

### 方法二：手动部署

```bash
# 1. 安装Railway CLI
npm install -g @railway/cli

# 2. 登录Railway
railway login

# 3. 初始化项目
railway init

# 4. 配置环境变量（在Railway Dashboard中）
railway open

# 5. 部署
railway up
```

---

## 📝 配置说明

### 1. railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install --no-cache-dir -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**说明：**
- 使用Nixpacks构建器
- 安装Python依赖
- 启动main.py
- 失败时自动重启（最多3次）

### 2. nixpacks.toml

```toml
[phases.setup]
nixPkgs = ["python311", "gcc", "g++"]

[phases.install]
cmds = [
  "pip install --upgrade pip",
  "pip install --no-cache-dir -r requirements.txt"
]

[start]
cmd = "python main.py"
```

**说明：**
- 使用Python 3.11
- 安装gcc和g++（编译依赖）
- 升级pip并安装依赖

### 3. Procfile

```
web: python main.py
```

**说明：**
- 定义web进程
- 运行main.py

### 4. .env.railway

这是环境变量模板文件，包含所有需要配置的变量。

**使用方法：**
1. 复制文件内容
2. 在Railway Dashboard中粘贴
3. 替换所有`your_xxx_here`为实际值

**必需变量：**
- OKX_API_KEY
- OKX_SECRET_KEY
- OKX_PASSPHRASE
- FEISHU_WEBHOOK_URL
- GEMINI_API_KEY
- TUSHARE_TOKEN
- ALPHAVANTAGE_API_KEY

---

## 🔧 环境变量配置

### 在Railway Dashboard中配置

1. 运行 `railway open` 打开Dashboard
2. 点击项目
3. 进入 `Variables` 标签
4. 点击 `Raw Editor`
5. 粘贴`.env.railway`内容
6. 替换所有占位符为实际值
7. 点击 `Save`

### 推荐配置（优化版）

```bash
# 仓位和杠杆
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

# 风控
MAX_DAILY_LOSS=0.05
SIGNAL_ONLY=1
```

---

## 📊 部署流程

```
1. 准备工作
   ├── 注册Railway账号
   ├── 安装Railway CLI
   └── 准备API密钥

2. 配置项目
   ├── 检查必要文件
   ├── 配置环境变量
   └── 测试本地运行

3. 部署到Railway
   ├── railway init
   ├── railway up
   └── 查看日志

4. 验证部署
   ├── 检查服务状态
   ├── 测试功能
   └── 监控运行
```

---

## 🐛 故障排查

### 部署失败

**问题：** 构建失败
```bash
# 查看构建日志
railway logs

# 检查requirements.txt
cat requirements.txt

# 重新部署
railway up --force
```

**问题：** 环境变量未生效
```bash
# 查看环境变量
railway variables

# 重新设置
railway variables set KEY=VALUE
```

### 服务崩溃

**问题：** 服务启动后立即退出
```bash
# 查看日志
railway logs --limit 200

# 检查main.py
python main.py  # 本地测试

# 重启服务
railway restart
```

### 连接问题

**问题：** 无法连接OKX
```bash
# 检查API密钥
railway variables | grep OKX

# 测试连接
python -c "from okx_client import OKXClient; print(OKXClient().get_account_balance())"
```

---

## 📚 相关文档

### 详细文档
- [Railway部署指南](./docs/Railway部署指南.md) - 完整的部署教程
- [快速参考](./RAILWAY_QUICKSTART.md) - 常用命令速查
- [部署检查清单](./RAILWAY_CHECKLIST.md) - 完整的检查项

### 项目文档
- [AURUM系统完整技术文档](./AURUM系统完整技术文档.md)
- [AURUM项目全景](./AURUM项目全景.md)

### 外部资源
- [Railway官方文档](https://docs.railway.app/)
- [Railway CLI文档](https://docs.railway.app/develop/cli)
- [Nixpacks文档](https://nixpacks.com/)

---

## 💰 成本说明

### Railway定价

| 计划 | 价格 | 资源 | 适用场景 |
|------|------|------|----------|
| Hobby | $0 (免费$5) | 512MB RAM | 测试、学习 |
| Pro | $20/月 | 8GB RAM | 生产环境 |

### AURUM预估成本

**最小配置（Hobby）：** $0/月（在免费额度内）
- 基础服务：$0
- PostgreSQL：$0（可选）
- Redis：$0（可选）

**推荐配置（Pro）：** $20/月
- 更多资源
- 更好的性能
- 适合生产环境

---

## ⚠️ 重要提示

### 安全
- ❌ **不要**将API密钥提交到Git
- ✅ **使用**Railway环境变量
- ✅ **定期**轮换密钥
- ✅ **启用**2FA认证

### 监控
- ✅ 定期查看Dashboard
- ✅ 设置告警通知
- ✅ 监控资源使用
- ✅ 检查错误日志

### 备份
- ✅ 定期备份交易记录
- ✅ 备份配置文件
- ✅ 记录环境变量（安全位置）

---

## 🎯 下一步

1. **阅读文档**
   - [Railway部署指南](./docs/Railway部署指南.md)
   - [部署检查清单](./RAILWAY_CHECKLIST.md)

2. **准备部署**
   - 准备API密钥
   - 检查必要文件
   - 配置环境变量

3. **执行部署**
   ```bash
   ./deploy-to-railway.sh
   ```

4. **验证和监控**
   ```bash
   railway logs --follow
   ```

---

## 📞 获取帮助

### 遇到问题？

1. 查看[常见问题](./docs/Railway部署指南.md#常见问题)
2. 查看Railway日志：`railway logs`
3. 访问[Railway文档](https://docs.railway.app/)
4. 检查[部署检查清单](./RAILWAY_CHECKLIST.md)

### 紧急情况

```bash
# 停止服务
railway down

# 查看日志
railway logs --limit 500

# 重新部署
railway up --force
```

---

**准备好了吗？开始部署：**

```bash
./deploy-to-railway.sh
```

**祝部署成功！** 🚀
