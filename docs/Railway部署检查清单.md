# Railway部署检查清单

## 📋 部署前检查

### 后端准备
- [ ] `backend/requirements.txt` 包含所有依赖
- [ ] `backend/railway.json` 配置正确
- [ ] `backend/app.py` 使用 `$PORT` 环境变量
- [ ] CORS配置支持生产域名
- [ ] 健康检查端点 `/health` 正常工作

### 前端准备
- [ ] `frontend/package.json` 配置正确
- [ ] `frontend/railway.json` 配置正确
- [ ] `.env.production` 配置生产环境API地址
- [ ] API客户端支持环境变量切换
- [ ] 错误处理完善

---

## 🚀 部署步骤

### 1. 部署后端

```bash
cd backend
railway login
railway init
railway up
```

**获取后端URL**
```bash
railway domain
# 输出: https://gold-advisor-backend.railway.app
```

### 2. 配置后端环境变量

在Railway Dashboard设置：
```
ENVIRONMENT=production
ALLOWED_ORIGINS=https://your-frontend.railway.app
PORT=8000
```

### 3. 测试后端

```bash
curl https://gold-advisor-backend.railway.app/health
# 应返回: {"status":"healthy",...}
```

### 4. 更新前端配置

编辑 `frontend/.env.production`:
```bash
NEXT_PUBLIC_API_URL=https://gold-advisor-backend.railway.app
```

### 5. 部署前端

```bash
cd frontend
railway init
railway up
```

### 6. 验证部署

访问前端URL，检查：
- [ ] 页面正常加载
- [ ] API请求成功（F12查看Network）
- [ ] 数据正常显示
- [ ] 无CORS错误

---

## 🔍 部署后验证

### 后端验证
```bash
# 健康检查
curl https://your-backend.railway.app/health

# API测试
curl https://your-backend.railway.app/api/ping
curl https://your-backend.railway.app/api/market-status
```

### 前端验证
1. 打开浏览器开发者工具（F12）
2. 访问前端URL
3. 检查Console无错误
4. 检查Network请求成功
5. 验证数据显示正常

---

## ⚠️ 常见问题

### 1. 后端启动失败
- 检查 `requirements.txt` 是否完整
- 查看Railway日志
- 确认Python版本兼容

### 2. CORS错误
- 检查 `ALLOWED_ORIGINS` 环境变量
- 确认前端域名正确
- 重启后端服务

### 3. 前端构建失败
- 检查 `package.json` 依赖
- 确认Node版本兼容
- 查看构建日志

### 4. API请求失败
- 确认后端URL正确
- 检查环境变量配置
- 验证后端服务运行中

---

## 📊 监控设置

### Railway监控
- 启用健康检查
- 设置告警通知
- 监控资源使用

### 日志查看
```bash
# Railway CLI
railway logs

# 或在Dashboard查看
```

---

## 🔄 更新部署

### 后端更新
```bash
cd backend
git pull
railway up
```

### 前端更新
```bash
cd frontend
git pull
railway up
```

---

## 💾 备份建议

- 定期备份环境变量配置
- 保存Railway项目配置
- 记录部署域名和设置

---

## ✅ 部署完成

部署成功后：
- [ ] 记录前后端URL
- [ ] 更新文档
- [ ] 通知团队
- [ ] 设置监控告警

---

**最后更新**: 2026-02-17
