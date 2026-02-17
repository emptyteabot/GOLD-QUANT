# AURUM DevOps快速开始指南

## 🚀 5分钟快速部署

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- 4核8G内存服务器

### 部署步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/aurum.git
cd aurum

# 2. 配置环境变量
cp .env.example .env
# 编辑.env，填入OKX API密钥

# 3. 一键部署
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 4. 访问系统
# 前端: http://localhost:3000
# Grafana: http://localhost:3001 (admin/admin_2026)
```

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 数据备份
./scripts/backup.sh

# 系统监控
./scripts/monitor.sh
```

### 故障排查

**服务启动失败？**
```bash
# 查看详细日志
docker-compose logs backend

# 检查端口占用
netstat -tulpn | grep 8000

# 重新构建
docker-compose build --no-cache
```

**数据库连接失败？**
```bash
# 检查数据库状态
docker exec -it aurum-postgres pg_isready

# 重启数据库
docker-compose restart postgres
```

### 下一步

- 阅读完整文档: `docs/10_DevOps部署方案.md`
- 配置监控告警
- 设置自动备份
- 配置SSL证书

---

**需要帮助？** 联系 devops@aurum.com
