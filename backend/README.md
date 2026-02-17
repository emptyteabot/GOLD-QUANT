# AURUM Backend API

完整的FastAPI后端实现，包含认证、用户管理、策略管理、交易管理等功能。

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置文件
│   ├── database.py          # 数据库连接
│   ├── dependencies.py      # 依赖注入
│   ├── models/              # SQLAlchemy模型
│   │   ├── user.py
│   │   ├── strategy.py
│   │   ├── order.py
│   │   ├── position.py
│   │   └── api_key.py
│   ├── schemas/             # Pydantic模型
│   │   ├── user.py
│   │   ├── strategy.py
│   │   ├── order.py
│   │   ├── position.py
│   │   └── response.py
│   ├── api/                 # API路由
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── strategies.py
│   │   ├── trading.py
│   │   └── market.py
│   ├── services/            # 业务逻辑
│   │   ├── auth_service.py
│   │   └── strategy_service.py
│   └── utils/               # 工具函数
│       └── security.py
├── init_db.py               # 数据库初始化
├── requirements.txt         # 依赖包
├── .env.example            # 环境变量示例
└── README.md               # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，修改数据库连接等配置
```

### 3. 初始化数据库

```bash
python init_db.py
```

### 4. 启动服务

```bash
# 开发模式
python -m app.main

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出
- `POST /api/v1/auth/refresh` - 刷新Token

### 用户管理
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新用户信息
- `POST /api/v1/users/me/password` - 修改密码

### 策略管理
- `POST /api/v1/strategies` - 创建策略
- `GET /api/v1/strategies` - 获取策略列表
- `GET /api/v1/strategies/{id}` - 获取策略详情
- `PUT /api/v1/strategies/{id}` - 更新策略
- `DELETE /api/v1/strategies/{id}` - 删除策略
- `POST /api/v1/strategies/{id}/start` - 启动策略
- `POST /api/v1/strategies/{id}/stop` - 停止策略

### 交易管理
- `GET /api/v1/positions` - 获取持仓列表
- `POST /api/v1/positions/{id}/close` - 平仓
- `GET /api/v1/orders` - 获取订单列表
- `POST /api/v1/orders` - 手动下单
- `DELETE /api/v1/orders/{id}` - 撤销订单

### 市场数据
- `GET /api/v1/market/klines` - 获取K线数据
- `GET /api/v1/market/ticker` - 获取实时价格
- `GET /api/v1/market/macro` - 获取宏观数据

## 数据库设计

使用PostgreSQL存储业务数据，包含以下表：

- `users` - 用户表
- `api_keys` - API密钥表
- `strategies` - 策略表
- `orders` - 订单表
- `positions` - 持仓表

## 认证机制

使用JWT (JSON Web Token)进行认证：

1. 用户登录后获取access_token
2. 后续请求在Header中携带: `Authorization: Bearer {token}`
3. Token有效期24小时（可配置）

## 安全特性

- 密码使用bcrypt加密存储
- API密钥使用AES-256加密存储
- JWT签名验证
- CORS跨域保护
- SQL注入防护（SQLAlchemy ORM）

## 开发说明

### 添加新的API端点

1. 在`app/api/`下创建新的路由文件
2. 在`app/main.py`中注册路由
3. 如需数据库操作，在`app/models/`添加模型
4. 在`app/schemas/`添加Pydantic验证模型

### 数据库迁移

使用Alembic进行数据库版本控制：

```bash
# 初始化
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 生产部署

1. 修改`.env`中的密钥为随机值
2. 设置`DEBUG=False`
3. 使用Gunicorn + Uvicorn部署
4. 配置Nginx反向代理
5. 启用HTTPS

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 技术栈

- FastAPI 0.109 - Web框架
- SQLAlchemy 2.0 - ORM
- Pydantic 2.5 - 数据验证
- PostgreSQL - 数据库
- Redis - 缓存
- JWT - 认证
- Uvicorn - ASGI服务器
