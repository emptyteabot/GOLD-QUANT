# 🚀 AURUM Railway部署快速指南

**部署平台**: Railway.app
**预计时间**: 15-20分钟
**费用**: 免费（$5/月额度）

---

## 📋 部署前准备

### 1. 注册Railway账号
访问：https://railway.app
- 使用GitHub账号登录（推荐）
- 或使用邮箱注册

### 2. 安装Railway CLI（可选）
```bash
# Windows (使用npm)
npm install -g @railway/cli

# 登录
railway login
```

---

## 🚀 部署步骤

### 方式1：通过Railway Web界面（推荐新手）

#### Step 1: 创建新项目
1. 登录 https://railway.app
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 授权Railway访问你的GitHub
5. 选择AURUM项目仓库

#### Step 2: 添加数据库
1. 在项目中点击 "New"
2. 选择 "Database" → "PostgreSQL"
3. Railway会自动创建数据库并提供连接信息

#### Step 3: 添加Redis
1. 点击 "New" → "Database" → "Redis"
2. 自动创建Redis实例

#### Step 4: 配置环境变量
在后端服务中添加环境变量：
```
DATABASE_URL=${PGDATABASE_URL}
REDIS_URL=${REDIS_URL}
SECRET_KEY=your-secret-key-here
OKX_API_KEY=your-okx-api-key
OKX_SECRET_KEY=your-okx-secret
OKX_PASSPHRASE=your-passphrase
FEISHU_WEBHOOK_URL=your-feishu-webhook
```

#### Step 5: 部署
- Railway会自动检测并部署
- 等待构建完成（约3-5分钟）
- 获取部署URL

---

### 方式2：通过Railway CLI（推荐开发者）

```bash
# 1. 进入项目目录
cd "C:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\黄金"

# 2. 初始化Railway项目
railway init

# 3. 添加PostgreSQL
railway add --database postgres

# 4. 添加Redis
railway add --database redis

# 5. 设置环境变量
railway variables set SECRET_KEY=your-secret-key
railway variables set OKX_API_KEY=your-api-key
railway variables set OKX_SECRET_KEY=your-secret
railway variables set OKX_PASSPHRASE=your-passphrase

# 6. 部署后端
cd backend
railway up

# 7. 部署前端
cd ../frontend
railway up

# 8. 查看部署状态
railway status

# 9. 查看日志
railway logs

# 10. 打开应用
railway open
```

---

## 📁 需要的配置文件

### 1. railway.json（项目根目录）
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2. Procfile（后端目录）
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 3. nixpacks.toml（后端目录）
```toml
[phases.setup]
nixPkgs = ["python39", "postgresql"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

### 4. package.json（前端目录，已有）
确保有以下scripts：
```json
{
  "scripts": {
    "build": "next build",
    "start": "next start -p $PORT"
  }
}
```

---

## 🔧 环境变量配置

### 后端环境变量
```bash
# 数据库（Railway自动提供）
DATABASE_URL=${PGDATABASE_URL}
REDIS_URL=${REDIS_URL}

# 应用配置
SECRET_KEY=生成一个随机密钥
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OKX API（你的交易所密钥）
OKX_API_KEY=你的API密钥
OKX_SECRET_KEY=你的Secret密钥
OKX_PASSPHRASE=你的密码短语

# 通知
FEISHU_WEBHOOK_URL=你的飞书Webhook

# CORS（前端域名）
ALLOWED_ORIGINS=https://你的前端域名.railway.app
```

### 前端环境变量
```bash
NEXT_PUBLIC_API_URL=https://你的后端域名.railway.app
```

---

## 🎯 部署后的URL

部署成功后，你会得到：

### 后端API
```
https://aurum-backend-production.up.railway.app
```

### 前端应用
```
https://aurum-frontend-production.up.railway.app
```

### API文档
```
https://aurum-backend-production.up.railway.app/docs
```

---

## ✅ 验证部署

### 1. 检查后端健康
```bash
curl https://你的后端域名.railway.app/health
```

应该返回：
```json
{"status": "healthy"}
```

### 2. 检查API文档
访问：`https://你的后端域名.railway.app/docs`

### 3. 检查前端
访问：`https://你的前端域名.railway.app`

---

## 🔍 常见问题

### Q1: 构建失败怎么办？
**A**: 检查日志
```bash
railway logs
```
常见原因：
- 缺少依赖
- 环境变量未设置
- 端口配置错误

### Q2: 数据库连接失败？
**A**: 确认环境变量
```bash
railway variables
```
确保 `DATABASE_URL` 已设置

### Q3: 前端无法访问后端？
**A**: 检查CORS配置
- 后端需要允许前端域名
- 检查 `ALLOWED_ORIGINS` 环境变量

### Q4: 如何查看实时日志？
```bash
railway logs --follow
```

### Q5: 如何重新部署？
```bash
railway up --detach
```

---

## 💰 费用说明

### Railway免费额度
- **$5/月** 免费额度
- **500小时** 运行时间
- **100GB** 出站流量
- **1GB** 内存

### 预计使用
- 后端：约$2-3/月
- 前端：约$1-2/月
- PostgreSQL：约$1/月
- Redis：约$0.5/月

**总计**：约$4.5-6.5/月（可能超出免费额度）

### 升级选项
如果超出免费额度：
- **Hobby Plan**: $5/月
- **Pro Plan**: $20/月

---

## 🚀 自动部署（CI/CD）

### 配置GitHub自动部署

1. **连接GitHub仓库**
   - Railway会自动监听仓库变化
   - 每次push自动部署

2. **配置分支**
   - main分支 → 生产环境
   - dev分支 → 测试环境

3. **部署触发**
```bash
git add .
git commit -m "Update code"
git push origin main
# Railway自动部署
```

---

## 📊 监控与日志

### 查看应用状态
```bash
railway status
```

### 查看资源使用
```bash
railway metrics
```

### 查看日志
```bash
# 实时日志
railway logs --follow

# 最近100行
railway logs --tail 100
```

---

## 🔐 安全建议

1. **使用强密钥**
```bash
# 生成随机SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **不要提交敏感信息**
- 使用 `.gitignore` 忽略 `.env` 文件
- 敏感信息只存在Railway环境变量中

3. **启用HTTPS**
- Railway自动提供HTTPS
- 确保前端只通过HTTPS访问后端

4. **限制CORS**
- 只允许你的前端域名访问后端
- 不要使用 `*` 通配符

---

## 📞 获取帮助

### Railway文档
https://docs.railway.app

### Railway Discord
https://discord.gg/railway

### Railway状态
https://status.railway.app

---

## 🎉 部署完成后

部署成功后，你将拥有：

✅ **后端API**: `https://你的域名.railway.app`
✅ **前端应用**: `https://你的域名.railway.app`
✅ **PostgreSQL数据库**: 自动配置
✅ **Redis缓存**: 自动配置
✅ **自动HTTPS**: Railway提供
✅ **自动部署**: GitHub集成

---

**下一步**：
1. 等待Agent完成代码准备
2. 推送代码到GitHub
3. 在Railway中部署
4. 配置环境变量
5. 测试应用

---

**预计15-20分钟后，你的AURUM系统就可以在线访问了！** 🚀
