# AURUM量化交易系统 - 系统架构设计文档

**文档版本**: v1.0
**编写人**: 系统架构师
**日期**: 2026-02-16
**状态**: 待评审

---

## 1. 架构概述

### 1.1 当前架构评估

#### 现状
- **架构模式**: 单体应用（Monolithic）
- **部署方式**: 单机Python脚本
- **数据存储**: 无持久化（内存）
- **可扩展性**: ❌ 差
- **高可用性**: ❌ 无
- **监控告警**: ⚠️ 仅飞书推送

#### 问题
1. **单点故障**: 进程崩溃 = 系统停止
2. **无法扩展**: 不支持多用户
3. **数据丢失**: 重启后历史数据丢失
4. **难以维护**: 所有逻辑耦合在一起

### 1.2 目标架构

#### 设计原则
- **微服务化**: 按业务领域拆分服务
- **高可用**: 无单点故障，自动故障转移
- **可扩展**: 支持水平扩展
- **可观测**: 完善的监控、日志、追踪
- **安全**: 多层安全防护

---

## 2. 整体架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户层 (User Layer)                      │
├─────────────────────────────────────────────────────────────────┤
│  Web Dashboard  │  Mobile App  │  API Client  │  Admin Panel   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      接入层 (Gateway Layer)                      │
├─────────────────────────────────────────────────────────────────┤
│  Nginx/Traefik  │  API Gateway  │  Load Balancer  │  WAF       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      应用层 (Application Layer)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ User Service │  │ Auth Service │  │ Notification │         │
│  │  (用户管理)  │  │  (认证授权)  │  │   Service    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Strategy Svc │  │ Backtest Svc │  │ Trading Svc  │         │
│  │  (策略管理)  │  │  (回测引擎)  │  │  (交易执行)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Data Svc    │  │  Risk Svc    │  │ Analytics Svc│         │
│  │  (数据服务)  │  │  (风控服务)  │  │  (分析服务)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据层 (Data Layer)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ PostgreSQL   │  │ TimescaleDB  │  │    Redis     │         │
│  │ (用户/配置)  │  │ (时序数据)   │  │   (缓存)     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   RabbitMQ   │  │     S3       │  │  ClickHouse  │         │
│  │  (消息队列)  │  │  (对象存储)  │  │  (日志分析)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    外部服务层 (External Layer)                   │
├─────────────────────────────────────────────────────────────────┤
│  OKX API  │  Tushare  │  Alpha Vantage  │  Feishu  │  Email   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    监控层 (Monitoring Layer)                     │
├─────────────────────────────────────────────────────────────────┤
│  Prometheus  │  Grafana  │  ELK Stack  │  Jaeger  │  Sentry   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心服务设计

### 3.1 User Service (用户服务)

**职责**:
- 用户注册/登录
- 用户信息管理
- API密钥管理
- 账户余额查询

**技术栈**:
- FastAPI + SQLAlchemy
- PostgreSQL
- JWT认证

**API设计**:
```python
POST   /api/v1/users/register      # 注册
POST   /api/v1/users/login         # 登录
GET    /api/v1/users/me            # 获取当前用户信息
PUT    /api/v1/users/me            # 更新用户信息
POST   /api/v1/users/api-keys      # 创建API密钥
DELETE /api/v1/users/api-keys/{id} # 删除API密钥
```

---

### 3.2 Trading Service (交易服务)

**职责**:
- 交易信号生成
- 订单执行
- 持仓管理
- 风险控制

**技术栈**:
- FastAPI + Celery
- RabbitMQ (消息队列)
- Redis (缓存)

**核心流程**:
```
1. 数据采集 (每5分钟)
   ↓
2. Multi-Agent分析
   ↓
3. 信号生成
   ↓
4. 风险检查
   ↓
5. 订单执行
   ↓
6. 持仓监控
   ↓
7. 止损/止盈
```

**API设计**:
```python
GET    /api/v1/trading/positions        # 获取持仓
POST   /api/v1/trading/orders           # 下单
DELETE /api/v1/trading/orders/{id}      # 撤单
GET    /api/v1/trading/signals          # 获取交易信号
POST   /api/v1/trading/strategies/start # 启动策略
POST   /api/v1/trading/strategies/stop  # 停止策略
```

---

### 3.3 Backtest Service (回测服务)

**职责**:
- 历史数据回测
- 策略性能评估
- 参数优化

**技术栈**:
- FastAPI + Pandas + NumPy
- TimescaleDB (时序数据)
- Celery (异步任务)

**API设计**:
```python
POST   /api/v1/backtest/run            # 运行回测
GET    /api/v1/backtest/results/{id}   # 获取回测结果
GET    /api/v1/backtest/history        # 回测历史
POST   /api/v1/backtest/optimize       # 参数优化
```

---

### 3.4 Data Service (数据服务)

**职责**:
- 市场数据采集
- 宏观数据采集
- 数据清洗和存储
- 数据API

**技术栈**:
- FastAPI + Pandas
- TimescaleDB
- Redis (缓存)

**数据流**:
```
OKX/Tushare/Alpha Vantage
         ↓
    数据采集器 (Celery定时任务)
         ↓
    数据清洗 & 验证
         ↓
    TimescaleDB (持久化)
         ↓
    Redis (缓存热数据)
         ↓
    API (对外提供)
```

---

### 3.5 Risk Service (风控服务)

**职责**:
- 实时风险监控
- VaR/CVaR计算
- 杠杆控制
- 熔断机制

**技术栈**:
- FastAPI + NumPy
- Redis (实时数据)
- RabbitMQ (告警)

**风控规则**:
```python
# 1. 仓位限制
max_position_ratio = 0.8  # 最大仓位80%

# 2. 杠杆限制
max_leverage = 10  # 最大杠杆10倍（降低风险）

# 3. 单日亏损限制
max_daily_loss = 0.05  # 单日最大亏损5%

# 4. 最大回撤限制
max_drawdown = 0.15  # 最大回撤15%

# 5. 连续止损限制
max_consecutive_losses = 3  # 连续止损3次暂停
```

---

## 4. 数据库设计

### 4.1 PostgreSQL (关系型数据库)

#### 用户表 (users)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### API密钥表 (api_keys)
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    exchange VARCHAR(20) NOT NULL,  -- 'okx', 'binance'
    api_key_encrypted TEXT NOT NULL,
    secret_key_encrypted TEXT NOT NULL,
    passphrase_encrypted TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 策略表 (strategies)
```sql
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,  -- 策略配置
    status VARCHAR(20) DEFAULT 'stopped',  -- 'running', 'stopped'
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 4.2 TimescaleDB (时序数据库)

#### K线数据表 (klines)
```sql
CREATE TABLE klines (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- '1m', '5m', '15m', '1h'
    open NUMERIC(20, 8),
    high NUMERIC(20, 8),
    low NUMERIC(20, 8),
    close NUMERIC(20, 8),
    volume NUMERIC(20, 8),
    PRIMARY KEY (time, symbol, timeframe)
);

-- 创建超表
SELECT create_hypertable('klines', 'time');
```

#### 交易记录表 (trades)
```sql
CREATE TABLE trades (
    time TIMESTAMPTZ NOT NULL,
    user_id INTEGER NOT NULL,
    strategy_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'buy', 'sell'
    price NUMERIC(20, 8),
    quantity NUMERIC(20, 8),
    pnl NUMERIC(20, 8),
    PRIMARY KEY (time, user_id, strategy_id)
);

SELECT create_hypertable('trades', 'time');
```

---

### 4.3 Redis (缓存)

#### 数据结构
```python
# 1. 实时价格缓存
redis.set('price:XAU-USDT-SWAP', '4819.20', ex=60)

# 2. 用户会话
redis.setex(f'session:{user_id}', 3600, jwt_token)

# 3. 交易信号缓存
redis.lpush('signals:XAU-USDT-SWAP', signal_json)
redis.ltrim('signals:XAU-USDT-SWAP', 0, 99)  # 保留最近100条

# 4. 风控指标
redis.hset(f'risk:{user_id}', {
    'daily_pnl': -0.03,
    'max_drawdown': 0.05,
    'position_ratio': 0.6
})
```

---

## 5. 部署架构

### 5.1 容器化部署 (Docker Compose)

#### docker-compose.yml
```yaml
version: '3.8'

services:
  # API网关
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - user-service
      - trading-service

  # 用户服务
  user-service:
    build: ./services/user
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/aurum
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  # 交易服务
  trading-service:
    build: ./services/trading
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/aurum
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672
    depends_on:
      - postgres
      - redis
      - rabbitmq

  # 回测服务
  backtest-service:
    build: ./services/backtest
    environment:
      - TIMESCALE_URL=postgresql://user:pass@timescaledb:5432/aurum
    depends_on:
      - timescaledb

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=aurum
    volumes:
      - postgres-data:/var/lib/postgresql/data

  # TimescaleDB
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=aurum
    volumes:
      - timescale-data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

  # RabbitMQ
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "15672:15672"  # 管理界面
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  postgres-data:
  timescale-data:
  redis-data:
  rabbitmq-data:
  prometheus-data:
  grafana-data:
```

---

### 5.2 Kubernetes部署 (生产环境)

#### 架构
```
┌─────────────────────────────────────────┐
│         Ingress (Nginx/Traefik)         │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│  Service A    │       │  Service B    │
│  (3 replicas) │       │  (3 replicas) │
└───────────────┘       └───────────────┘
        │                       │
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │  StatefulSet          │
        │  (PostgreSQL/Redis)   │
        └───────────────────────┘
```

#### 关键配置
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trading-service
  template:
    metadata:
      labels:
        app: trading-service
    spec:
      containers:
      - name: trading-service
        image: aurum/trading-service:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## 6. 安全架构

### 6.1 多层安全防护

```
┌─────────────────────────────────────────┐
│  Layer 1: 网络层                         │
│  - WAF (Web应用防火墙)                   │
│  - DDoS防护                              │
│  - IP白名单                              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Layer 2: 应用层                         │
│  - JWT认证                               │
│  - API限流 (Rate Limiting)               │
│  - HTTPS/TLS加密                         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Layer 3: 数据层                         │
│  - 数据库加密 (AES-256)                  │
│  - API密钥加密存储                       │
│  - 敏感字段脱敏                          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Layer 4: 审计层                         │
│  - 操作日志记录                          │
│  - 异常行为检测                          │
│  - 安全事件告警                          │
└─────────────────────────────────────────┘
```

### 6.2 API密钥管理

```python
# 加密存储
from cryptography.fernet import Fernet

# 1. 生成主密钥（存储在环境变量或密钥管理服务）
MASTER_KEY = os.getenv('MASTER_KEY')
cipher = Fernet(MASTER_KEY)

# 2. 加密用户API密钥
encrypted_api_key = cipher.encrypt(user_api_key.encode())

# 3. 存储到数据库
db.execute(
    "INSERT INTO api_keys (user_id, api_key_encrypted) VALUES (?, ?)",
    (user_id, encrypted_api_key)
)

# 4. 使用时解密
decrypted_api_key = cipher.decrypt(encrypted_api_key).decode()
```

---

## 7. 监控与告警

### 7.1 监控指标

#### 系统指标
- CPU使用率
- 内存使用率
- 磁盘I/O
- 网络流量

#### 应用指标
- API响应时间
- 请求成功率
- 错误率
- 并发用户数

#### 业务指标
- 交易成功率
- 平均盈亏
- 风险指标（VaR/回撤）
- 用户活跃度

### 7.2 告警规则

```yaml
# prometheus-alerts.yml
groups:
  - name: aurum-alerts
    rules:
      # API响应时间告警
      - alert: HighAPILatency
        expr: http_request_duration_seconds{quantile="0.95"} > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API响应时间过高"

      # 交易失败率告警
      - alert: HighTradeFailureRate
        expr: rate(trade_failures_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "交易失败率超过10%"

      # 风险告警
      - alert: HighDrawdown
        expr: max_drawdown > 0.15
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "最大回撤超过15%"
```

---

## 8. 技术选型总结

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| **后端框架** | FastAPI | 高性能、异步、自动文档 |
| **数据库** | PostgreSQL | 成熟稳定、ACID保证 |
| **时序数据库** | TimescaleDB | PostgreSQL扩展、SQL友好 |
| **缓存** | Redis | 高性能、丰富数据结构 |
| **消息队列** | RabbitMQ | 可靠性高、功能丰富 |
| **容器化** | Docker | 标准化、易部署 |
| **编排** | Kubernetes | 自动扩缩容、高可用 |
| **监控** | Prometheus + Grafana | 开源、生态完善 |
| **日志** | ELK Stack | 强大的日志分析能力 |
| **追踪** | Jaeger | 分布式追踪 |

---

## 9. 性能优化

### 9.1 数据库优化
- 索引优化（B-Tree/Hash索引）
- 分区表（按时间分区）
- 连接池（pgbouncer）
- 读写分离（主从复制）

### 9.2 缓存策略
- 热数据缓存（Redis）
- CDN加速（静态资源）
- 查询结果缓存
- 缓存预热

### 9.3 异步处理
- Celery异步任务
- WebSocket实时推送
- 消息队列解耦

---

## 10. 下一步行动

### 立即行动
1. ✅ 完成架构设计文档（本文档）
2. 🔄 数据库工程师设计详细表结构
3. 🔄 DevOps工程师搭建CI/CD
4. 🔄 后端工程师开始API开发

### 短期行动（2周）
1. 完成微服务拆分
2. 搭建开发环境（Docker Compose）
3. 实现核心API
4. 建立监控体系

### 中期行动（1个月）
1. 完成所有服务开发
2. 集成测试
3. 性能测试
4. 安全测试

---

**文档状态**: ✅ 初稿完成，待团队评审
**下一步**: 数据库工程师输出详细表结构，DevOps搭建环境
