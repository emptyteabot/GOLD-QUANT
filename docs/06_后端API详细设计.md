# AURUM后端API详细设计文档

**文档版本**: v1.0
**编写人**: 后端工程师
**日期**: 2026-02-16
**状态**: 已完成

---

## 1. API概览

### 1.1 技术栈

- **框架**: FastAPI 0.109+
- **认证**: JWT (JSON Web Tokens)
- **文档**: Swagger/OpenAPI 3.0
- **实时通信**: WebSocket
- **数据验证**: Pydantic
- **ORM**: SQLAlchemy 2.0

### 1.2 API基础信息

```
Base URL: https://api.aurum.com/api/v1
WebSocket: wss://api.aurum.com/ws
文档地址: https://api.aurum.com/docs
```

### 1.3 通用响应格式

```json
{
  "code": 200,
  "message": "Success",
  "data": {},
  "timestamp": "2026-02-16T12:00:00Z"
}
```

### 1.4 错误响应格式

```json
{
  "code": 400,
  "message": "Invalid request",
  "error": "详细错误信息",
  "timestamp": "2026-02-16T12:00:00Z"
}
```

---

## 2. 认证与授权

### 2.1 用户注册

```http
POST /auth/register
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "张三"
}
```

**响应**:
```json
{
  "code": 201,
  "message": "注册成功",
  "data": {
    "user_id": 123,
    "username": "user123",
    "email": "user@example.com"
  }
}
```

### 2.2 用户登录

```http
POST /auth/login
Content-Type: application/json

{
  "username": "user123",
  "password": "SecurePass123!"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 123,
      "username": "user123",
      "email": "user@example.com"
    }
  }
}
```

### 2.3 刷新Token

```http
POST /auth/refresh
Authorization: Bearer {access_token}
```

### 2.4 登出

```http
POST /auth/logout
Authorization: Bearer {access_token}
```

---

## 3. 用户管理API

### 3.1 获取当前用户信息

```http
GET /users/me
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "id": 123,
    "username": "user123",
    "email": "user@example.com",
    "full_name": "张三",
    "role": "user",
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

### 3.2 更新用户信息

```http
PUT /users/me
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "full_name": "张三丰",
  "phone": "13800138000"
}
```

### 3.3 修改密码

```http
POST /users/me/password
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

---

## 4. API密钥管理

### 4.1 创建API密钥

```http
POST /api-keys
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "exchange": "okx",
  "api_key": "your-api-key",
  "secret_key": "your-secret-key",
  "passphrase": "your-passphrase"
}
```

**响应**:
```json
{
  "code": 201,
  "message": "API密钥创建成功",
  "data": {
    "id": 456,
    "exchange": "okx",
    "api_key_masked": "abc***xyz",
    "status": "active",
    "created_at": "2026-02-16T12:00:00Z"
  }
}
```

### 4.2 获取API密钥列表

```http
GET /api-keys
Authorization: Bearer {access_token}
```

### 4.3 删除API密钥

```http
DELETE /api-keys/{key_id}
Authorization: Bearer {access_token}
```

---

## 5. 策略管理API

### 5.1 创建策略

```http
POST /strategies
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "AURUM Multi-Agent v3.0",
  "description": "15+个AI协同决策",
  "symbol": "XAU-USDT-SWAP",
  "timeframe": "15m",
  "config": {
    "max_leverage": 10,
    "max_position_ratio": 0.8,
    "stop_loss_ratio": 0.015,
    "signal_threshold": 0.20,
    "confidence_threshold": 0.50,
    "agent_weights": {
      "macro": 0.30,
      "technical": 0.30,
      "ml": 0.25,
      "xaut": 0.15
    }
  }
}
```

**响应**:
```json
{
  "code": 201,
  "message": "策略创建成功",
  "data": {
    "id": 789,
    "name": "AURUM Multi-Agent v3.0",
    "status": "stopped",
    "created_at": "2026-02-16T12:00:00Z"
  }
}
```

### 5.2 获取策略列表

```http
GET /strategies?status=running&limit=10&offset=0
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "total": 5,
    "items": [
      {
        "id": 789,
        "name": "AURUM Multi-Agent v3.0",
        "symbol": "XAU-USDT-SWAP",
        "status": "running",
        "created_at": "2026-02-16T12:00:00Z"
      }
    ]
  }
}
```

### 5.3 获取策略详情

```http
GET /strategies/{strategy_id}
Authorization: Bearer {access_token}
```

### 5.4 更新策略配置

```http
PUT /strategies/{strategy_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "config": {
    "max_leverage": 8,
    "stop_loss_ratio": 0.02
  }
}
```

### 5.5 启动策略

```http
POST /strategies/{strategy_id}/start
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "策略已启动",
  "data": {
    "id": 789,
    "status": "running",
    "started_at": "2026-02-16T12:00:00Z"
  }
}
```

### 5.6 停止策略

```http
POST /strategies/{strategy_id}/stop
Authorization: Bearer {access_token}
```

### 5.7 删除策略

```http
DELETE /strategies/{strategy_id}
Authorization: Bearer {access_token}
```

---

## 6. 交易管理API

### 6.1 获取持仓列表

```http
GET /positions?symbol=XAU-USDT-SWAP&status=open
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "total": 1,
    "items": [
      {
        "id": 1001,
        "symbol": "XAU-USDT-SWAP",
        "side": "long",
        "quantity": 408,
        "avg_entry_price": 4754.90,
        "current_price": 4819.20,
        "leverage": 20,
        "unrealized_pnl": 26.36,
        "unrealized_pnl_ratio": 0.2759,
        "stop_loss_price": 4754.90,
        "opened_at": "2026-02-16T10:00:00Z"
      }
    ]
  }
}
```

### 6.2 获取订单列表

```http
GET /orders?status=filled&limit=20
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "total": 45,
    "items": [
      {
        "id": 2001,
        "order_id": "okx-123456",
        "symbol": "XAU-USDT-SWAP",
        "side": "buy",
        "order_type": "market",
        "price": 4754.90,
        "quantity": 408,
        "filled_quantity": 408,
        "status": "filled",
        "leverage": 20,
        "fee": 0.41,
        "created_at": "2026-02-16T10:00:00Z",
        "filled_at": "2026-02-16T10:00:01Z"
      }
    ]
  }
}
```

### 6.3 手动下单

```http
POST /orders
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "symbol": "XAU-USDT-SWAP",
  "side": "buy",
  "order_type": "market",
  "quantity": 100,
  "leverage": 10
}
```

### 6.4 撤销订单

```http
DELETE /orders/{order_id}
Authorization: Bearer {access_token}
```

### 6.5 平仓

```http
POST /positions/{position_id}/close
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "quantity": 408,  // 可选，不填则全部平仓
  "order_type": "market"
}
```

---

## 7. 数据服务API

### 7.1 获取K线数据

```http
GET /market/klines?symbol=XAU-USDT-SWAP&timeframe=15m&limit=100
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "symbol": "XAU-USDT-SWAP",
    "timeframe": "15m",
    "items": [
      {
        "time": "2026-02-16T12:00:00Z",
        "open": 4810.50,
        "high": 4820.30,
        "low": 4805.20,
        "close": 4819.20,
        "volume": 15234.5
      }
    ]
  }
}
```

### 7.2 获取实时价格

```http
GET /market/ticker?symbol=XAU-USDT-SWAP
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "symbol": "XAU-USDT-SWAP",
    "last": 4819.20,
    "bid": 4819.10,
    "ask": 4819.30,
    "volume_24h": 1234567.89,
    "change_24h": 1.35,
    "timestamp": "2026-02-16T12:00:00Z"
  }
}
```

### 7.3 获取宏观数据

```http
GET /market/macro?indicators=dxy,vix,us10y
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "dxy": {
      "value": 103.45,
      "change": -0.25,
      "timestamp": "2026-02-16T12:00:00Z"
    },
    "vix": {
      "value": 18.32,
      "change": 1.15,
      "timestamp": "2026-02-16T12:00:00Z"
    },
    "us10y": {
      "value": 4.25,
      "change": -0.05,
      "timestamp": "2026-02-16T12:00:00Z"
    }
  }
}
```

---

## 8. 回测API

### 8.1 创建回测任务

```http
POST /backtest
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "strategy_id": 789,
  "start_date": "2025-01-01",
  "end_date": "2026-01-01",
  "initial_capital": 10000,
  "config": {
    "max_leverage": 10,
    "stop_loss_ratio": 0.015
  }
}
```

**响应**:
```json
{
  "code": 202,
  "message": "回测任务已创建",
  "data": {
    "task_id": "bt-123456",
    "status": "pending",
    "created_at": "2026-02-16T12:00:00Z"
  }
}
```

### 8.2 获取回测结果

```http
GET /backtest/{task_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "task_id": "bt-123456",
    "status": "completed",
    "result": {
      "initial_capital": 10000,
      "final_capital": 10192.10,
      "total_return": 0.0192,
      "max_drawdown": 0.0164,
      "sharpe_ratio": 1.85,
      "win_rate": 0.40,
      "total_trades": 5,
      "trades": [
        {
          "entry_time": "2025-01-15T10:00:00Z",
          "exit_time": "2025-01-16T14:00:00Z",
          "side": "long",
          "entry_price": 4750.00,
          "exit_price": 4820.00,
          "quantity": 100,
          "pnl": 70.00,
          "pnl_ratio": 0.0147
        }
      ]
    },
    "completed_at": "2026-02-16T12:05:00Z"
  }
}
```

---

## 9. 监控API

### 9.1 获取账户概览

```http
GET /account/overview
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "total_equity": 1253.37,
    "available_balance": 253.37,
    "margin_used": 1000.00,
    "unrealized_pnl": 26.36,
    "daily_pnl": 15.23,
    "total_pnl": 253.37,
    "total_return": 0.2534,
    "positions_count": 1,
    "running_strategies": 2
  }
}
```

### 9.2 获取策略性能

```http
GET /strategies/{strategy_id}/performance?period=30d
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "strategy_id": 789,
    "period": "30d",
    "metrics": {
      "total_return": 0.0192,
      "max_drawdown": 0.0164,
      "sharpe_ratio": 1.85,
      "sortino_ratio": 2.15,
      "win_rate": 0.40,
      "profit_factor": 2.72,
      "total_trades": 5,
      "avg_trade_duration": "2.5 days"
    },
    "equity_curve": [
      {
        "time": "2026-01-01T00:00:00Z",
        "equity": 1000.00
      },
      {
        "time": "2026-01-02T00:00:00Z",
        "equity": 1015.50
      }
    ]
  }
}
```

### 9.3 获取交易信号

```http
GET /signals?symbol=XAU-USDT-SWAP&limit=10
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "time": "2026-02-16T12:00:00Z",
        "symbol": "XAU-USDT-SWAP",
        "signal": -0.32,
        "confidence": 0.493,
        "consensus": 0.662,
        "action": "hold",
        "reason": "信号不足，技术面偏弱",
        "agents": {
          "macro": 0.30,
          "technical": -1.00,
          "ml": 0.40,
          "xaut": -1.00
        }
      }
    ]
  }
}
```

---

## 10. WebSocket实时推送

### 10.1 连接WebSocket

```javascript
const ws = new WebSocket('wss://api.aurum.com/ws?token=YOUR_JWT_TOKEN');

ws.onopen = () => {
  console.log('WebSocket连接已建立');

  // 订阅实时价格
  ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'ticker',
    symbol: 'XAU-USDT-SWAP'
  }));

  // 订阅交易信号
  ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'signals',
    strategy_id: 789
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);
};
```

### 10.2 实时价格推送

```json
{
  "channel": "ticker",
  "symbol": "XAU-USDT-SWAP",
  "data": {
    "last": 4819.20,
    "bid": 4819.10,
    "ask": 4819.30,
    "volume": 15234.5,
    "timestamp": "2026-02-16T12:00:00Z"
  }
}
```

### 10.3 交易信号推送

```json
{
  "channel": "signals",
  "strategy_id": 789,
  "data": {
    "signal": 0.65,
    "confidence": 0.75,
    "action": "buy",
    "reason": "多重AI确认做多信号",
    "timestamp": "2026-02-16T12:00:00Z"
  }
}
```

### 10.4 持仓更新推送

```json
{
  "channel": "positions",
  "user_id": 123,
  "data": {
    "position_id": 1001,
    "symbol": "XAU-USDT-SWAP",
    "unrealized_pnl": 28.50,
    "unrealized_pnl_ratio": 0.2850,
    "current_price": 4821.50,
    "timestamp": "2026-02-16T12:00:00Z"
  }
}
```

---

## 11. 错误码定义

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 200 | 成功 | 200 |
| 201 | 创建成功 | 201 |
| 400 | 请求参数错误 | 400 |
| 401 | 未授权（Token无效或过期） | 401 |
| 403 | 禁止访问（权限不足） | 403 |
| 404 | 资源不存在 | 404 |
| 409 | 资源冲突（如用户名已存在） | 409 |
| 429 | 请求过于频繁（限流） | 429 |
| 500 | 服务器内部错误 | 500 |
| 503 | 服务暂时不可用 | 503 |

---

## 12. 限流策略

| 端点类型 | 限制 | 窗口 |
|---------|------|------|
| 认证相关 | 10次/分钟 | 1分钟 |
| 查询API | 100次/分钟 | 1分钟 |
| 交易API | 20次/分钟 | 1分钟 |
| WebSocket | 1000条消息/分钟 | 1分钟 |

---

## 13. FastAPI实现示例

### 13.1 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置文件
│   ├── dependencies.py         # 依赖注入
│   ├── models/                 # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── strategy.py
│   │   └── order.py
│   ├── schemas/                # Pydantic模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── strategy.py
│   │   └── order.py
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── strategies.py
│   │   ├── orders.py
│   │   └── market.py
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── strategy_service.py
│   │   └── trading_service.py
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── security.py
│       └── websocket.py
├── tests/
├── requirements.txt
└── README.md
```

### 13.2 main.py示例

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, strategies, orders, market

app = FastAPI(
    title="AURUM API",
    description="黄金量化交易系统API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["策略"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["交易"])
app.include_router(market.router, prefix="/api/v1/market", tags=["市场数据"])

@app.get("/")
async def root():
    return {"message": "AURUM API v1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 13.3 认证路由示例

```python
# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserLogin, Token
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/register", response_model=Token)
async def register(user: UserCreate, auth_service: AuthService = Depends()):
    """用户注册"""
    try:
        return await auth_service.register(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, auth_service: AuthService = Depends()):
    """用户登录"""
    token = await auth_service.login(credentials)
    if not token:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return token
```

---

## 14. 总结

### 14.1 API特性

- ✅ **RESTful设计**: 符合REST规范
- ✅ **JWT认证**: 安全的Token认证
- ✅ **自动文档**: Swagger/OpenAPI
- ✅ **实时推送**: WebSocket支持
- ✅ **数据验证**: Pydantic自动验证
- ✅ **限流保护**: 防止滥用
- ✅ **错误处理**: 统一错误格式

### 14.2 下一步工作

1. 实现所有API端点
2. 编写单元测试
3. 性能测试与优化
4. 部署到生产环境

---

**文档状态**: ✅ 完成
**最后更新**: 2026-02-16
