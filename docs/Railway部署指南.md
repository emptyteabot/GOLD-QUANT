# AURUM Railway 部署指南

## 📋 目录

1. [Railway简介](#railway简介)
2. [准备工作](#准备工作)
3. [快速部署](#快速部署)
4. [环境变量配置](#环境变量配置)
5. [数据库配置](#数据库配置)
6. [监控和日志](#监控和日志)
7. [常见问题](#常见问题)
8. [成本估算](#成本估算)

---

## Railway简介

### 什么是Railway？

Railway是一个现代化的云平台，提供：
- ✅ **自动部署**：Git推送即部署
- ✅ **免费额度**：$5/月免费使用
- ✅ **PostgreSQL**：内置数据库支持
- ✅ **Redis**：内置缓存支持
- ✅ **自动HTTPS**：免费SSL证书
- ✅ **零配置**：开箱即用

### 为什么选择Railway？

| 特性 | Railway | Heroku | AWS |
|------|---------|--------|-----|
| 免费额度 | $5/月 | $0 | 复杂 |
| 部署速度 | 快 | 中等 | 慢 |
| 配置难度 | 简单 | 中等 | 困难 |
| PostgreSQL | ✅ 免费 | ✅ 有限 | ❌ 付费 |
| Redis | ✅ 免费 | ❌ 付费 | ❌ 付费 |
| 自动HTTPS | ✅ | ✅ | ❌ 需配置 |

---

## 准备工作

### 1. 注册Railway账号

访问 [railway.app](https://railway.app) 注册账号：
- 使用GitHub账号登录（推荐）
- 或使用邮箱注册

### 2. 安装Railway CLI

**macOS/Linux:**
```bash
npm install -g @railway/cli
```

**Windows:**
```bash
npm install -g @railway/cli
```

**验证安装:**
```bash
railway --version
```

### 3. 登录Railway

```bash
railway login
```

浏览器会自动打开，完成授权。

### 4. 准备项目文件

确保项目根目录包含以下文件：
```
黄金/
├── main.py                 # 主程序
├── config.py               # 配置文件
├── requirements.txt        # Python依赖
├── railway.json            # Railway配置
├── nixpacks.toml           # 构建配置
├── Procfile                # 进程配置
├── .env.railway            # 环境变量模板
└── deploy-to-railway.sh    # 部署脚本
```

---

## 快速部署

### 方法一：使用自动化脚本（推荐）

```bash
# 1. 进入项目目录
cd /c/Users/陈盈桦/Desktop/Desktop_整理_2026-02-09_172732/Folders/黄金

# 2. 给脚本添加执行权限
chmod +x deploy-to-railway.sh

# 3. 运行部署脚本
./deploy-to-railway.sh
```

脚本会自动：
- ✅ 检查Railway CLI
- ✅ 检查登录状态
- ✅ 检查必要文件
- ✅ 初始化项目
- ✅ 部署到Railway

### 方法二：手动部署

#### 步骤1：初始化项目

```bash
# 进入项目目录
cd /c/Users/陈盈桦/Desktop/Desktop_整理_2026-02-09_172732/Folders/黄金

# 初始化Railway项目
railway init
```

选择：
- `Create a new project` → 输入项目名称（如：aurum-trading）
- 选择环境：`production`

#### 步骤2：配置环境变量

```bash
# 打开Railway Dashboard
railway open
```

在Dashboard中：
1. 点击项目
2. 进入 `Variables` 标签
3. 添加环境变量（见下节）

#### 步骤3：部署

```bash
# 部署到Railway
railway up
```

#### 步骤4：查看日志

```bash
# 实时查看日志
railway logs
```

---

## 环境变量配置

### 必需的环境变量

在Railway Dashboard的Variables中添加以下变量：

#### 1. OKX交易所配置

```bash
OKX_API_KEY=your_okx_api_key
OKX_SECRET_KEY=your_okx_secret_key
OKX_PASSPHRASE=your_okx_passphrase
```

#### 2. 飞书通知配置

```bash
FEISHU_WEBHOOK_URL=your_feishu_webhook_url
FEISHU_MSG_TYPE=interactive
```

#### 3. Gemini AI配置

```bash
GEMINI_API_KEY=your_gemini_api_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
GEMINI_MODEL=gemini-pro
```

#### 4. Tushare数据配置

```bash
TUSHARE_TOKEN=your_tushare_token
TUSHARE_BASE_URL=http://lianghua.nanyangqiankun.top
```

#### 5. Alpha Vantage配置

```bash
ALPHAVANTAGE_API_KEY=your_alphavantage_api_key
```

### 交易参数配置（优化版）

```bash
# 基础配置
INST_ID=XAU-USDT-SWAP
RISK_PER_TRADE=0.01
POSITION_SIZE_PCT=0.30
MAX_TOTAL_POSITION=0.75
STOP_LOSS_PCT=0.015
TAKE_PROFIT_PCT=0.30

# 杠杆配置
BASE_LEVERAGE=5
MAX_LEVERAGE=20
MIN_LEVERAGE=1

# 决策阈值（优化版）
MIN_CONFIDENCE=0.50
MIN_SIGNAL=0.20
MIN_CONSENSUS=0.50
MIN_TRADE_INTERVAL_MINUTES=15

# 技术指标
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
ADX_RANGE_THRESHOLD=15
ADX_TREND_THRESHOLD=25

# 风控
MAX_DAILY_LOSS=0.05
SIGNAL_ONLY=1
```

### 快速导入环境变量

使用`.env.railway`模板：

1. 复制`.env.railway`内容
2. 在Railway Dashboard中批量粘贴
3. 替换所有`your_xxx_here`为实际值

---

## 数据库配置

### PostgreSQL（可选）

如果需要存储交易历史：

#### 1. 添加PostgreSQL服务

在Railway Dashboard中：
1. 点击 `New` → `Database` → `PostgreSQL`
2. Railway自动创建数据库
3. 自动注入环境变量：
   - `DATABASE_URL`
   - `PGHOST`
   - `PGPORT`
   - `PGUSER`
   - `PGPASSWORD`
   - `PGDATABASE`

#### 2. 在代码中使用

```python
import os
import psycopg2

# Railway自动提供DATABASE_URL
database_url = os.getenv('DATABASE_URL')

# 连接数据库
conn = psycopg2.connect(database_url)
```

### Redis（可选）

如果需要缓存数据：

#### 1. 添加Redis服务

在Railway Dashboard中：
1. 点击 `New` → `Database` → `Redis`
2. Railway自动创建Redis
3. 自动注入环境变量：
   - `REDIS_URL`
   - `REDIS_HOST`
   - `REDIS_PORT`
   - `REDIS_PASSWORD`

#### 2. 在代码中使用

```python
import os
import redis

# Railway自动提供REDIS_URL
redis_url = os.getenv('REDIS_URL')

# 连接Redis
r = redis.from_url(redis_url)
```

---

## 监控和日志

### 查看实时日志

```bash
# 实时日志
railway logs

# 查看最近100行
railway logs --limit 100

# 跟踪日志
railway logs --follow
```

### 在Dashboard中查看

1. 打开Railway Dashboard
2. 点击项目
3. 进入 `Deployments` 标签
4. 点击最新部署
5. 查看 `Logs` 和 `Metrics`

### 监控指标

Railway自动提供：
- ✅ **CPU使用率**
- ✅ **内存使用率**
- ✅ **网络流量**
- ✅ **请求数量**
- ✅ **响应时间**

### 设置告警

在Railway Dashboard中：
1. 进入 `Settings` → `Notifications`
2. 配置告警规则：
   - CPU > 80%
   - 内存 > 90%
   - 部署失败
   - 服务崩溃

---

## 常见问题

### 1. 部署失败：找不到requirements.txt

**问题：**
```
Error: requirements.txt not found
```

**解决：**
```bash
# 确保requirements.txt存在
ls requirements.txt

# 如果不存在，创建
pip freeze > requirements.txt
```

### 2. 环境变量未生效

**问题：**
```
KeyError: 'OKX_API_KEY'
```

**解决：**
1. 检查Railway Dashboard中是否配置了环境变量
2. 重新部署：`railway up`
3. 检查config.py是否正确读取环境变量

### 3. 内存不足

**问题：**
```
MemoryError: Out of memory
```

**解决：**
1. 升级Railway计划（$5/月 → $20/月）
2. 优化代码，减少内存使用
3. 使用Redis缓存数据

### 4. 连接超时

**问题：**
```
TimeoutError: Connection timeout
```

**解决：**
1. 检查OKX API是否可访问
2. 检查Railway网络配置
3. 增加超时时间：
   ```python
   import requests
   requests.get(url, timeout=30)
   ```

### 5. 时区问题

**问题：**
```
交易时间不对
```

**解决：**
```python
import os
os.environ['TZ'] = 'Asia/Shanghai'

import time
time.tzset()
```

### 6. 日志中文乱码

**问题：**
```
飞书推送显示乱码
```

**解决：**
```bash
# 在Railway Variables中添加
PYTHONIOENCODING=utf-8
LANG=zh_CN.UTF-8
```

### 7. 部署后无法访问

**问题：**
```
Service not responding
```

**解决：**
1. 检查main.py是否正常运行
2. 查看日志：`railway logs`
3. 检查Procfile配置
4. 确保程序不会立即退出

---

## 成本估算

### Railway定价

| 计划 | 价格 | 资源 |
|------|------|------|
| **Hobby** | $5/月（免费） | 512MB RAM, 1GB存储 |
| **Pro** | $20/月 | 8GB RAM, 100GB存储 |
| **Team** | $20/用户/月 | 无限资源 |

### AURUM预估成本

#### 最小配置（Hobby计划）

```
基础服务：$0（免费$5额度）
PostgreSQL：$0（包含在免费额度）
Redis：$0（包含在免费额度）
流量：$0（包含在免费额度）

总计：$0/月（在免费额度内）
```

#### 推荐配置（Pro计划）

```
基础服务：$20/月
PostgreSQL：$0（包含）
Redis：$0（包含）
额外流量：$0（通常够用）

总计：$20/月
```

### 成本优化建议

1. **使用免费额度**
   - 初期使用Hobby计划
   - 监控资源使用情况
   - 超出后再升级

2. **优化代码**
   - 减少API调用频率
   - 使用缓存减少计算
   - 优化数据库查询

3. **按需扩展**
   - 只在交易时段运行
   - 使用定时任务
   - 避免24/7运行

---

## 部署检查清单

### 部署前

- [ ] Railway账号已注册
- [ ] Railway CLI已安装
- [ ] 已登录Railway
- [ ] 所有必要文件已准备
- [ ] requirements.txt已更新
- [ ] 环境变量已准备

### 部署中

- [ ] 项目已初始化
- [ ] 环境变量已配置
- [ ] 代码已推送
- [ ] 部署成功

### 部署后

- [ ] 服务正常运行
- [ ] 日志无错误
- [ ] 飞书推送正常
- [ ] OKX连接正常
- [ ] 数据获取正常
- [ ] 监控已设置

---

## 高级配置

### 自定义域名

1. 在Railway Dashboard中：
   - 进入 `Settings` → `Domains`
   - 点击 `Add Domain`
   - 输入域名（如：aurum.yourdomain.com）

2. 在域名DNS中添加CNAME记录：
   ```
   aurum.yourdomain.com → your-app.railway.app
   ```

### 自动部署

配置GitHub自动部署：

1. 在Railway Dashboard中：
   - 进入 `Settings` → `Source`
   - 连接GitHub仓库
   - 选择分支（如：main）

2. 每次推送代码自动部署：
   ```bash
   git push origin main
   ```

### 多环境部署

创建多个环境：

```bash
# 创建开发环境
railway environment create development

# 创建生产环境
railway environment create production

# 切换环境
railway environment use production
```

---

## 故障排查

### 查看服务状态

```bash
# 查看服务状态
railway status

# 查看部署历史
railway deployments

# 查看环境变量
railway variables
```

### 重启服务

```bash
# 重启服务
railway restart

# 重新部署
railway up --force
```

### 回滚部署

在Railway Dashboard中：
1. 进入 `Deployments`
2. 找到之前的成功部署
3. 点击 `Redeploy`

---

## 安全建议

### 1. 保护API密钥

- ❌ 不要将密钥提交到Git
- ✅ 使用Railway环境变量
- ✅ 定期轮换密钥
- ✅ 使用只读API密钥（如可能）

### 2. 限制访问

- ✅ 使用Railway的访问控制
- ✅ 配置IP白名单
- ✅ 启用2FA认证

### 3. 监控异常

- ✅ 设置告警通知
- ✅ 监控异常交易
- ✅ 定期检查日志

---

## 总结

### Railway优势

- ✅ **简单**：零配置，开箱即用
- ✅ **快速**：部署只需几分钟
- ✅ **便宜**：$5/月免费额度
- ✅ **可靠**：自动扩展，高可用

### 适用场景

- ✅ 个人量化交易系统
- ✅ 小型交易机器人
- ✅ 原型验证
- ✅ 学习和测试

### 不适用场景

- ❌ 高频交易（延迟要求极高）
- ❌ 大规模集群（成本高）
- ❌ 需要GPU计算

---

## 下一步

1. **完成部署**
   ```bash
   ./deploy-to-railway.sh
   ```

2. **监控运行**
   ```bash
   railway logs --follow
   ```

3. **优化策略**
   - 根据实际运行调整参数
   - 监控收益和风险
   - 持续改进

---

## 参考资源

- [Railway官方文档](https://docs.railway.app/)
- [Railway CLI文档](https://docs.railway.app/develop/cli)
- [Nixpacks文档](https://nixpacks.com/)
- [AURUM项目文档](./AURUM系统完整技术文档.md)

---

**祝部署顺利！** 🚀

如有问题，请查看[常见问题](#常见问题)或联系技术支持。
