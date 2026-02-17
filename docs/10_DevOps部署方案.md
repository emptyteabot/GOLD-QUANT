# AURUM DevOps部署方案文档

## 📋 文档概述

**项目名称**: AURUM黄金量化交易系统
**文档版本**: v1.0
**编写日期**: 2026-02-16
**编写人**: DevOps团队

---

## 🎯 部署架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      AURUM生产环境                           │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   前端层     │    │   后端层     │    │   数据层     │
│              │    │              │    │              │
│ • Nginx      │───▶│ • FastAPI    │───▶│ • PostgreSQL │
│ • React      │    │ • Python3.9  │    │ • Redis      │
│              │    │ • RabbitMQ   │    │ • TimescaleDB│
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │   监控层     │
                    │              │
                    │ • Prometheus │
                    │ • Grafana    │
                    │ • Alerting   │
                    └──────────────┘
```

---

## 🐳 Docker容器化

### 1. 后端Dockerfile

**文件**: `Dockerfile.backend`

**特点**:
- 基于Python 3.9-slim镜像
- 多阶段构建优化镜像大小
- 内置健康检查
- 支持环境变量配置

**构建命令**:
```bash
docker build -f Dockerfile.backend -t aurum-backend:latest .
```

### 2. 前端Dockerfile

**文件**: `Dockerfile.frontend`

**特点**:
- 基于Node.js 18构建
- Nginx作为Web服务器
- Gzip压缩优化传输
- 支持SPA路由

**构建命令**:
```bash
docker build -f Dockerfile.frontend -t aurum-frontend:latest .
```

### 3. Docker Compose编排

**文件**: `docker-compose.yml`

**服务清单**:

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| postgres | timescale/timescaledb:latest-pg15 | 5432 | 时序数据库 |
| redis | redis:7-alpine | 6379 | 缓存服务 |
| rabbitmq | rabbitmq:3-management | 5672, 15672 | 消息队列 |
| backend | aurum-backend:latest | 8000 | 后端API |
| frontend | aurum-frontend:latest | 3000 | 前端界面 |
| prometheus | prom/prometheus:latest | 9090 | 监控采集 |
| grafana | grafana/grafana:latest | 3001 | 可视化 |
| node-exporter | prom/node-exporter:latest | 9100 | 系统指标 |

**启动命令**:
```bash
docker-compose up -d
```

---

## 🚀 CI/CD流水线

### GitHub Actions工作流

**文件**: `.github/workflows/ci.yml`

### 流水线阶段

#### 1. 代码质量检查 (Lint)
- **工具**: Flake8, Black, Pylint
- **触发**: 每次Push/PR
- **时长**: ~2分钟

```yaml
- Flake8代码规范检查
- Black代码格式化检查
- Pylint静态分析
```

#### 2. 单元测试 (Test)
- **框架**: Pytest
- **覆盖率**: 目标>80%
- **环境**: PostgreSQL + Redis测试容器

```yaml
- 运行所有单元测试
- 生成覆盖率报告
- 上传到Codecov
```

#### 3. 回测验证 (Backtest)
- **目的**: 验证策略性能
- **指标**: 最大回撤<20%, 夏普比率>0.5

```yaml
- 运行30天历史回测
- 验证关键指标
- 失败则阻止部署
```

#### 4. 镜像构建 (Build)
- **仓库**: GitHub Container Registry
- **标签**: branch名, commit SHA, 版本号
- **缓存**: GitHub Actions缓存

```yaml
- 构建后端镜像
- 构建前端镜像
- 推送到容器仓库
```

#### 5. 安全扫描 (Security)
- **工具**: Trivy
- **扫描**: 依赖漏洞、镜像漏洞

```yaml
- 扫描代码依赖
- 扫描Docker镜像
- 上传SARIF报告
```

#### 6. 生产部署 (Deploy)
- **触发**: main分支Push
- **方式**: SSH远程部署
- **验证**: 健康检查

```yaml
- SSH连接生产服务器
- 拉取最新镜像
- 滚动更新服务
- 健康检查验证
```

### 部署流程图

```
代码提交 → Lint → Test → Backtest → Build → Security → Deploy
   ↓        ↓      ↓        ↓         ↓        ↓         ↓
 GitHub   通过   通过     通过      推送     通过     生产环境
          ↓      ↓        ↓         ↓        ↓         ↓
        失败   失败     失败      失败     失败      回滚
          ↓      ↓        ↓         ↓        ↓         ↓
        通知   通知     通知      通知     通知      通知
```

---

## 📊 监控体系

### 1. Prometheus监控

**配置文件**: `monitoring/prometheus.yml`

**监控目标**:
- 系统指标 (CPU/内存/磁盘)
- 应用指标 (API响应时间/错误率)
- 业务指标 (交易次数/盈亏/回撤)
- 数据库指标 (连接数/查询性能)

**采集间隔**: 15秒

### 2. Grafana可视化

**配置文件**: `monitoring/grafana/dashboards/aurum-dashboard.json`

**仪表盘面板**:

| 面板 | 指标 | 说明 |
|------|------|------|
| 系统概览 | 服务状态 | 各服务运行状态 |
| CPU使用率 | node_cpu | 实时CPU使用 |
| 内存使用率 | node_memory | 实时内存使用 |
| 交易盈亏 | aurum_total_pnl | 累计盈亏曲线 |
| 最大回撤 | aurum_max_drawdown | 实时回撤监控 |
| 交易次数 | aurum_trades_total | 交易统计 |
| API响应时间 | http_request_duration | P95响应时间 |
| 数据库连接 | pg_stat_activity | 连接池状态 |

**访问地址**: http://localhost:3001
**默认账号**: admin / admin_2026

### 3. 告警规则

**配置文件**: `monitoring/alerts.yml`

**告警级别**:

| 级别 | 触发条件 | 通知方式 |
|------|----------|----------|
| Critical | 服务宕机、回撤>15% | 短信+电话 |
| Warning | CPU>80%、内存>85% | 邮件+Slack |
| Info | 磁盘<15%、连接数高 | Slack |

**告警示例**:
```yaml
- 服务宕机超过2分钟
- CPU使用率超过80%持续5分钟
- 内存使用率超过85%持续5分钟
- 磁盘剩余空间低于15%
- 最大回撤超过15%
- 交易错误率>0.1/秒
- API响应时间P95>2秒
```

---

## 🛠️ 部署脚本

### 1. 一键部署脚本

**文件**: `scripts/deploy.sh`

**功能**:
- 环境检查 (Docker/Docker Compose)
- 环境变量配置
- 目录结构创建
- 数据库初始化
- 镜像拉取
- 服务启动
- 健康检查

**使用方法**:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**执行流程**:
```
[1/7] 检查系统环境
[2/7] 配置环境变量
[3/7] 创建目录结构
[4/7] 初始化数据库
[5/7] 拉取Docker镜像
[6/7] 启动服务
[7/7] 健康检查
```

### 2. 数据备份脚本

**文件**: `scripts/backup.sh`

**备份内容**:
- PostgreSQL数据库 (压缩SQL)
- Redis数据 (RDB快照)
- 配置文件 (tar.gz)

**备份策略**:
- 每日自动备份
- 保留30天
- 自动清理旧备份

**使用方法**:
```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
```

**Crontab配置**:
```bash
# 每天凌晨2点自动备份
0 2 * * * /opt/aurum/scripts/backup.sh >> /var/log/aurum-backup.log 2>&1
```

### 3. 数据恢复脚本

**文件**: `scripts/restore.sh`

**功能**:
- 列出可用备份
- 选择恢复时间点
- 恢复PostgreSQL
- 恢复Redis
- 服务重启

**使用方法**:
```bash
chmod +x scripts/restore.sh
./scripts/restore.sh
```

### 4. 系统监控脚本

**文件**: `scripts/monitor.sh`

**功能**:
- 服务状态检查
- 资源使用监控
- 错误日志查看
- 交易状态查询

**使用方法**:
```bash
# 单次检查
./scripts/monitor.sh

# 循环监控（每30秒刷新）
./scripts/monitor.sh --watch
```

---

## 🔐 安全配置

### 1. 环境变量管理

**文件**: `.env`

**敏感信息**:
```bash
# 数据库密码
POSTGRES_PASSWORD=强密码
REDIS_PASSWORD=强密码
RABBITMQ_PASSWORD=强密码

# OKX API密钥
OKX_API_KEY=真实密钥
OKX_SECRET_KEY=真实密钥
OKX_PASSPHRASE=真实密码

# Grafana密码
GRAFANA_PASSWORD=强密码
```

**安全建议**:
- 使用强密码（16位+大小写+数字+符号）
- 定期轮换密钥
- 不要提交到Git
- 使用密钥管理服务（如AWS Secrets Manager）

### 2. 网络安全

**防火墙规则**:
```bash
# 只开放必要端口
- 80/443: HTTP/HTTPS
- 22: SSH (限制IP)
- 其他端口: 仅内网访问
```

**Docker网络隔离**:
- 使用自定义网络
- 服务间通信限制
- 禁止容器访问宿主机

### 3. SSL/TLS配置

**Nginx SSL配置**:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/aurum.crt;
    ssl_certificate_key /etc/ssl/private/aurum.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

---

## 📈 性能优化

### 1. 数据库优化

**PostgreSQL配置**:
```sql
-- 连接池
max_connections = 100
shared_buffers = 256MB

-- 查询优化
work_mem = 16MB
maintenance_work_mem = 128MB

-- 时序数据压缩
SELECT add_compression_policy('trades', INTERVAL '7 days');
```

### 2. Redis缓存策略

**缓存内容**:
- 市场行情数据 (TTL: 5秒)
- 用户会话 (TTL: 24小时)
- API响应 (TTL: 60秒)

**内存限制**:
```bash
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### 3. 应用优化

**后端优化**:
- 异步IO (asyncio)
- 连接池复用
- 批量数据处理
- 定时任务调度

**前端优化**:
- 代码分割 (Code Splitting)
- 懒加载 (Lazy Loading)
- CDN加速
- Gzip压缩

---

## 🔄 运维流程

### 1. 日常运维

**每日检查**:
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f --tail=100

# 查看资源使用
docker stats

# 运行监控脚本
./scripts/monitor.sh
```

**每周维护**:
- 检查磁盘空间
- 清理旧日志
- 更新依赖包
- 安全补丁

### 2. 故障处理

**服务宕机**:
```bash
# 重启单个服务
docker-compose restart backend

# 重启所有服务
docker-compose restart

# 查看错误日志
docker-compose logs backend --tail=200
```

**数据库问题**:
```bash
# 进入数据库
docker exec -it aurum-postgres psql -U aurum_user aurum

# 检查连接数
SELECT count(*) FROM pg_stat_activity;

# 杀死慢查询
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';
```

**性能问题**:
```bash
# 查看资源占用
docker stats

# 清理Docker缓存
docker system prune -af

# 重启服务
docker-compose restart
```

### 3. 版本更新

**更新流程**:
```bash
# 1. 备份数据
./scripts/backup.sh

# 2. 拉取最新代码
git pull origin main

# 3. 构建新镜像
docker-compose build

# 4. 滚动更新
docker-compose up -d --no-deps --build backend

# 5. 健康检查
curl http://localhost:8000/health

# 6. 如有问题，回滚
docker-compose down
./scripts/restore.sh
```

---

## 📝 常见问题

### Q1: 服务启动失败？

**排查步骤**:
1. 检查端口占用: `netstat -tulpn | grep 8000`
2. 查看日志: `docker-compose logs backend`
3. 检查环境变量: `cat .env`
4. 验证配置文件: `docker-compose config`

### Q2: 数据库连接失败？

**解决方案**:
```bash
# 检查数据库状态
docker-compose ps postgres

# 测试连接
docker exec -it aurum-postgres pg_isready

# 重启数据库
docker-compose restart postgres
```

### Q3: 监控数据不显示？

**解决方案**:
```bash
# 检查Prometheus
curl http://localhost:9090/-/healthy

# 检查指标端点
curl http://localhost:8000/metrics

# 重启监控服务
docker-compose restart prometheus grafana
```

### Q4: 如何扩容？

**水平扩容**:
```bash
# 增加后端实例
docker-compose up -d --scale backend=3

# 配置负载均衡
# 修改nginx.conf添加upstream配置
```

---

## 🎯 最佳实践

### 1. 开发环境

```bash
# 使用docker-compose.dev.yml
docker-compose -f docker-compose.dev.yml up

# 挂载代码目录实现热重载
volumes:
  - ./backend:/app/backend
```

### 2. 测试环境

```bash
# 使用独立的测试数据库
DATABASE_URL=postgresql://test_user:test_pass@localhost:5433/aurum_test

# 运行集成测试
pytest tests/integration/
```

### 3. 生产环境

```bash
# 使用生产配置
ENVIRONMENT=production

# 启用所有监控
docker-compose --profile monitoring up -d

# 配置自动重启
restart: unless-stopped
```

---

## 📞 技术支持

### 联系方式

- **技术文档**: https://docs.aurum.example.com
- **问题反馈**: https://github.com/aurum/issues
- **邮件支持**: devops@aurum.example.com
- **紧急热线**: +86-xxx-xxxx-xxxx

### 团队分工

| 角色 | 职责 | 联系方式 |
|------|------|----------|
| DevOps工程师 | 部署运维 | devops@aurum.com |
| 后端工程师 | API开发 | backend@aurum.com |
| 前端工程师 | 界面开发 | frontend@aurum.com |
| 数据工程师 | 数据处理 | data@aurum.com |

---

## 📚 附录

### A. 端口清单

| 端口 | 服务 | 说明 |
|------|------|------|
| 3000 | Frontend | 前端界面 |
| 8000 | Backend | 后端API |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存 |
| 5672 | RabbitMQ | 消息队列 |
| 15672 | RabbitMQ管理 | Web管理界面 |
| 9090 | Prometheus | 监控采集 |
| 3001 | Grafana | 可视化 |
| 9100 | Node Exporter | 系统指标 |

### B. 目录结构

```
aurum/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD配置
├── backend/                    # 后端代码
├── frontend/                   # 前端代码
├── monitoring/                 # 监控配置
│   ├── prometheus.yml
│   ├── alerts.yml
│   └── grafana/
│       ├── dashboards/
│       └── datasources/
├── scripts/                    # 运维脚本
│   ├── deploy.sh
│   ├── backup.sh
│   ├── restore.sh
│   └── monitor.sh
├── logs/                       # 日志目录
├── data/                       # 数据目录
├── backups/                    # 备份目录
├── docker-compose.yml          # Docker编排
├── Dockerfile.backend          # 后端镜像
├── Dockerfile.frontend         # 前端镜像
├── nginx.conf                  # Nginx配置
├── .env                        # 环境变量
└── README.md                   # 项目说明
```

### C. 环境变量清单

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| POSTGRES_PASSWORD | 数据库密码 | aurum_pass_2026 |
| REDIS_PASSWORD | Redis密码 | redis_pass_2026 |
| RABBITMQ_PASSWORD | RabbitMQ密码 | rabbitmq_pass_2026 |
| OKX_API_KEY | OKX API密钥 | your_api_key |
| OKX_SECRET_KEY | OKX密钥 | your_secret_key |
| OKX_PASSPHRASE | OKX密码 | your_passphrase |
| GRAFANA_PASSWORD | Grafana密码 | admin_2026 |
| ENVIRONMENT | 运行环境 | production |

### D. 命令速查表

```bash
# Docker Compose
docker-compose up -d              # 启动所有服务
docker-compose down               # 停止所有服务
docker-compose ps                 # 查看服务状态
docker-compose logs -f [service]  # 查看日志
docker-compose restart [service]  # 重启服务
docker-compose pull               # 拉取最新镜像
docker-compose build              # 构建镜像

# 运维脚本
./scripts/deploy.sh               # 一键部署
./scripts/backup.sh               # 数据备份
./scripts/restore.sh              # 数据恢复
./scripts/monitor.sh              # 系统监控
./scripts/monitor.sh --watch      # 循环监控

# Docker
docker ps                         # 查看容器
docker logs [container]           # 查看日志
docker exec -it [container] bash  # 进入容器
docker stats                      # 资源使用
docker system prune -af           # 清理缓存

# 数据库
docker exec -it aurum-postgres psql -U aurum_user aurum
\dt                               # 列出表
\d [table]                        # 查看表结构
SELECT * FROM trades LIMIT 10;   # 查询数据
```

---

## ✅ 部署检查清单

### 部署前检查

- [ ] 服务器配置满足要求（4核8G+）
- [ ] Docker和Docker Compose已安装
- [ ] 防火墙规则已配置
- [ ] SSL证书已准备
- [ ] 域名DNS已解析
- [ ] 环境变量已配置
- [ ] OKX API密钥已获取
- [ ] 备份策略已制定

### 部署后验证

- [ ] 所有服务正常启动
- [ ] 前端界面可访问
- [ ] 后端API响应正常
- [ ] 数据库连接成功
- [ ] Redis缓存工作正常
- [ ] 监控数据正常采集
- [ ] Grafana仪表盘显示正常
- [ ] 告警规则已配置
- [ ] 备份脚本测试通过
- [ ] 恢复流程验证通过

---

## 📄 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-02-16 | 初始版本，完整DevOps体系 | DevOps团队 |

---

<div align="center">

**AURUM DevOps部署方案** 🚀

让量化交易系统稳定运行，7x24小时不间断

Made with ❤️ by AURUM DevOps Team

</div>
