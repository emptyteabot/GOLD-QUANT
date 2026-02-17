# AURUM API使用文档

## 📋 目录

1. [API概述](#api概述)
2. [认证授权](#认证授权)
3. [核心API](#核心api)
4. [数据API](#数据api)
5. [交易API](#交易api)
6. [策略API](#策略api)
7. [监控API](#监控api)
8. [错误处理](#错误处理)

---

## API概述

### 什么是AURUM API？

AURUM提供RESTful API，允许你通过编程方式：
- 获取市场数据
- 执行交易操作
- 管理策略配置
- 监控系统状态

### API基础信息

```
Base URL: http://localhost:8000/api/v1
Content-Type: application/json
Authentication: Bearer Token
```

### 快速开始

```python
import requests

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 获取系统状态
response = requests.get(f"{BASE_URL}/status")
print(response.json())
```

---

## 认证授权

### 获取API Token

```python
# 登录获取token
import requests

url = "http://localhost:8000/api/v1/auth/login"
data = {
    "username": "your_username",
    "password": "your_password"
}

response = requests.post(url, json=data)
token = response.json()["access_token"]

print(f"Token: {token}")
```

### 使用Token

```python
# 在请求头中添加token
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.get(
    "http://localhost:8000/api/v1/account",
    headers=headers
)
```

---

## 核心API

### 1. 系统状态

#### GET /status

获取系统运行状态

**请求：**
```bash
curl -X GET http://localhost:8000/api/v1/status
```

**响应：**
```json
{
  "status": "running",
  "mode": "live",
  "uptime": "2h 35m",
  "version": "1.0.0",
  "last_update": "2026-02-16T10:30:00Z"
}
```

### 2. 账户信息

#### GET /account

获取账户信息

**请求：**
```python
import requests

headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/account",
    headers=headers
)
```

**响应：**
```json
{
  "balance": {
    "total": 1050.25,
    "available": 850.00,
    "frozen": 200.25
  },
  "equity": 1055.30,
  "margin": 200.25,
  "margin_ratio": 0.19,
  "unrealized_pnl": 5.05
}
```

### 3. 持仓信息

#### GET /positions

获取当前持仓

**请求：**
```python
response = requests.get(
    "http://localhost:8000/api/v1/positions",
    headers=headers
)
```

**响应：**
```json
{
  "positions": [
    {
      "symbol": "XAUUSDT",
      "side": "long",
      "size": 0.5,
      "entry_price": 2050.00,
      "current_price": 2060.00,
      "unrealized_pnl": 5.00,
      "leverage": 5,
      "margin": 205.00,
      "liquidation_price": 1845.00,
      "open_time": "2026-02-16T08:00:00Z"
    }
  ]
}
```

---

## 数据API

### 1. 获取K线数据

#### GET /market/klines

获取历史K线数据

**参数：**
- `symbol`: 交易对（如XAUUSDT）
- `interval`: K线周期（1m, 5m, 15m, 1h, 4h, 1d）
- `limit`: 数量限制（默认100，最大1000）
- `start_time`: 开始时间（Unix时间戳）
- `end_time`: 结束时间（Unix时间戳）

**请求：**
```python
params = {
    "symbol": "XAUUSDT",
    "interval": "1h",
    "limit": 100
}

response = requests.get(
    "http://localhost:8000/api/v1/market/klines",
    params=params,
    headers=headers
)
```

**响应：**
```json
{
  "symbol": "XAUUSDT",
  "interval": "1h",
  "data": [
    {
      "timestamp": 1708070400000,
      "open": 2050.00,
      "high": 2055.00,
      "low": 2048.00,
      "close": 2052.00,
      "volume": 1250.5
    },
    ...
  ]
}
```

### 2. 获取实时行情

#### GET /market/ticker

获取实时价格

**请求：**
```python
params = {"symbol": "XAUUSDT"}
response = requests.get(
    "http://localhost:8000/api/v1/market/ticker",
    params=params,
    headers=headers
)
```

**响应：**
```json
{
  "symbol": "XAUUSDT",
  "last_price": 2052.50,
  "bid_price": 2052.00,
  "ask_price": 2053.00,
  "high_24h": 2065.00,
  "low_24h": 2040.00,
  "volume_24h": 125000.5,
  "change_24h": 0.0125,
  "timestamp": 1708070400000
}
```

### 3. 获取技术指标

#### GET /indicators

获取计算好的技术指标

**参数：**
- `symbol`: 交易对
- `indicators`: 指标列表（rsi,macd,bb,ema）
- `period`: 计算周期

**请求：**
```python
params = {
    "symbol": "XAUUSDT",
    "indicators": "rsi,macd,bb",
    "period": "1h"
}

response = requests.get(
    "http://localhost:8000/api/v1/indicators",
    params=params,
    headers=headers
)
```

**响应：**
```json
{
  "symbol": "XAUUSDT",
  "timestamp": 1708070400000,
  "indicators": {
    "rsi": {
      "value": 45.5,
      "period": 14,
      "overbought": 70,
      "oversold": 30
    },
    "macd": {
      "macd": 2.5,
      "signal": 1.8,
      "histogram": 0.7
    },
    "bb": {
      "upper": 2065.00,
      "middle": 2050.00,
      "lower": 2035.00,
      "bandwidth": 0.015
    }
  }
}
```

---

## 交易API

### 1. 下单

#### POST /orders

创建新订单

**请求体：**
```json
{
  "symbol": "XAUUSDT",
  "side": "buy",
  "type": "market",
  "size": 0.1,
  "leverage": 5,
  "stop_loss": 2019.25,
  "take_profit": 2111.50
}
```

**Python示例：**
```python
order_data = {
    "symbol": "XAUUSDT",
    "side": "buy",  # buy或sell
    "type": "market",  # market或limit
    "size": 0.1,
    "leverage": 5,
    "stop_loss": 2019.25,
    "take_profit": 2111.50
}

response = requests.post(
    "http://localhost:8000/api/v1/orders",
    json=order_data,
    headers=headers
)
```

**响应：**
```json
{
  "order_id": "123456789",
  "symbol": "XAUUSDT",
  "side": "buy",
  "type": "market",
  "size": 0.1,
  "price": 2050.00,
  "status": "filled",
  "filled_size": 0.1,
  "filled_price": 2050.00,
  "fee": 0.05,
  "created_at": "2026-02-16T10:00:00Z",
  "updated_at": "2026-02-16T10:00:01Z"
}
```

### 2. 查询订单

#### GET /orders/{order_id}

查询订单详情

**请求：**
```python
order_id = "123456789"
response = requests.get(
    f"http://localhost:8000/api/v1/orders/{order_id}",
    headers=headers
)
```

**响应：**
```json
{
  "order_id": "123456789",
  "symbol": "XAUUSDT",
  "side": "buy",
  "type": "market",
  "size": 0.1,
  "price": 2050.00,
  "status": "filled",
  "filled_size": 0.1,
  "filled_price": 2050.00,
  "fee": 0.05,
  "created_at": "2026-02-16T10:00:00Z",
  "updated_at": "2026-02-16T10:00:01Z"
}
```

### 3. 取消订单

#### DELETE /orders/{order_id}

取消未成交订单

**请求：**
```python
order_id = "123456789"
response = requests.delete(
    f"http://localhost:8000/api/v1/orders/{order_id}",
    headers=headers
)
```

**响应：**
```json
{
  "order_id": "123456789",
  "status": "cancelled",
  "message": "Order cancelled successfully"
}
```

### 4. 平仓

#### POST /positions/close

平掉指定持仓

**请求体：**
```json
{
  "symbol": "XAUUSDT",
  "size": 0.1  // 可选，不填则全部平仓
}
```

**Python示例：**
```python
close_data = {
    "symbol": "XAUUSDT",
    "size": 0.1  # 平仓数量，不填则全部平仓
}

response = requests.post(
    "http://localhost:8000/api/v1/positions/close",
    json=close_data,
    headers=headers
)
```

**响应：**
```json
{
  "symbol": "XAUUSDT",
  "closed_size": 0.1,
  "close_price": 2060.00,
  "pnl": 5.00,
  "status": "closed",
  "message": "Position closed successfully"
}
```

---

## 策略API

### 1. 获取策略列表

#### GET /strategies

获取所有策略

**请求：**
```python
response = requests.get(
    "http://localhost:8000/api/v1/strategies",
    headers=headers
)
```

**响应：**
```json
{
  "strategies": [
    {
      "name": "macro",
      "display_name": "宏观分析",
      "weight": 0.20,
      "enabled": true,
      "performance": {
        "win_rate": 0.45,
        "avg_return": 0.025,
        "sharpe_ratio": 1.5
      }
    },
    {
      "name": "technical",
      "display_name": "技术分析",
      "weight": 0.20,
      "enabled": true,
      "performance": {
        "win_rate": 0.40,
        "avg_return": 0.020,
        "sharpe_ratio": 1.3
      }
    }
  ]
}
```

### 2. 更新策略权重

#### PUT /strategies/weights

更新策略权重

**请求体：**
```json
{
  "weights": {
    "macro": 0.25,
    "technical": 0.25,
    "ml": 0.30,
    "xaut": 0.10,
    "rsi": 0.10
  }
}
```

**Python示例：**
```python
weights_data = {
    "weights": {
        "macro": 0.25,
        "technical": 0.25,
        "ml": 0.30,
        "xaut": 0.10,
        "rsi": 0.10
    }
}

response = requests.put(
    "http://localhost:8000/api/v1/strategies/weights",
    json=weights_data,
    headers=headers
)
```

**响应：**
```json
{
  "message": "Weights updated successfully",
  "weights": {
    "macro": 0.25,
    "technical": 0.25,
    "ml": 0.30,
    "xaut": 0.10,
    "rsi": 0.10
  }
}
```

### 3. 获取策略信号

#### GET /strategies/signals

获取当前策略信号

**请求：**
```python
response = requests.get(
    "http://localhost:8000/api/v1/strategies/signals",
    headers=headers
)
```

**响应：**
```json
{
  "timestamp": "2026-02-16T10:00:00Z",
  "signals": {
    "macro": {
      "signal": 1,
      "confidence": 0.75,
      "reason": "美元走弱，美债收益率下降"
    },
    "technical": {
      "signal": 1,
      "confidence": 0.65,
      "reason": "RSI超卖，MACD金叉"
    },
    "ml": {
      "signal": 1,
      "confidence": 0.70,
      "reason": "预测上涨概率68%"
    }
  },
  "combined": {
    "signal": 1,
    "strength": 0.85,
    "confidence": 0.70,
    "action": "buy"
  }
}
```

---

## 监控API

### 1. 获取性能指标

#### GET /performance

获取系统性能指标

**请求：**
```python
params = {
    "period": "7d"  # 1d, 7d, 30d, 90d
}

response = requests.get(
    "http://localhost:8000/api/v1/performance",
    params=params,
    headers=headers
)
```

**响应：**
```json
{
  "period": "7d",
  "metrics": {
    "total_return": 0.0385,
    "daily_return": 0.0055,
    "max_drawdown": 0.0164,
    "sharpe_ratio": 1.85,
    "win_rate": 0.40,
    "profit_factor": 2.72,
    "total_trades": 5,
    "winning_trades": 2,
    "losing_trades": 3
  },
  "equity_curve": [
    {"date": "2026-02-10", "equity": 1000.00},
    {"date": "2026-02-11", "equity": 1005.50},
    {"date": "2026-02-12", "equity": 1010.25},
    ...
  ]
}
```

### 2. 获取交易历史

#### GET /trades

获取历史交易记录

**参数：**
- `start_date`: 开始日期
- `end_date`: 结束日期
- `limit`: 数量限制
- `offset`: 偏移量

**请求：**
```python
params = {
    "start_date": "2026-02-01",
    "end_date": "2026-02-16",
    "limit": 50,
    "offset": 0
}

response = requests.get(
    "http://localhost:8000/api/v1/trades",
    params=params,
    headers=headers
)
```

**响应：**
```json
{
  "total": 5,
  "trades": [
    {
      "trade_id": "T001",
      "symbol": "XAUUSDT",
      "side": "buy",
      "entry_price": 2050.00,
      "exit_price": 2060.00,
      "size": 0.1,
      "leverage": 5,
      "pnl": 5.00,
      "pnl_pct": 0.0049,
      "fee": 0.05,
      "duration": "2h 30m",
      "entry_time": "2026-02-16T08:00:00Z",
      "exit_time": "2026-02-16T10:30:00Z",
      "exit_reason": "take_profit"
    },
    ...
  ]
}
```

### 3. 获取系统日志

#### GET /logs

获取系统日志

**参数：**
- `level`: 日志级别（INFO, WARNING, ERROR）
- `limit`: 数量限制
- `offset`: 偏移量

**请求：**
```python
params = {
    "level": "ERROR",
    "limit": 100,
    "offset": 0
}

response = requests.get(
    "http://localhost:8000/api/v1/logs",
    params=params,
    headers=headers
)
```

**响应：**
```json
{
  "total": 3,
  "logs": [
    {
      "timestamp": "2026-02-16T10:00:00Z",
      "level": "ERROR",
      "module": "okx_client",
      "message": "API rate limit exceeded",
      "details": {
        "endpoint": "/api/v5/trade/order",
        "retry_after": 60
      }
    },
    ...
  ]
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid symbol parameter",
    "details": {
      "parameter": "symbol",
      "value": "INVALID",
      "expected": "XAUUSDT"
    }
  }
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| UNAUTHORIZED | 401 | 未授权，token无效或过期 |
| FORBIDDEN | 403 | 禁止访问，权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| INVALID_PARAMETER | 400 | 参数错误 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| INSUFFICIENT_BALANCE | 400 | 余额不足 |
| ORDER_REJECTED | 400 | 订单被拒绝 |

### 错误处理示例

```python
import requests

try:
    response = requests.get(
        "http://localhost:8000/api/v1/account",
        headers=headers
    )
    response.raise_for_status()  # 检查HTTP错误
    data = response.json()

except requests.exceptions.HTTPError as e:
    error = response.json()
    print(f"HTTP Error: {error['error']['message']}")

except requests.exceptions.ConnectionError:
    print("Connection Error: Unable to connect to API")

except requests.exceptions.Timeout:
    print("Timeout Error: Request timed out")

except Exception as e:
    print(f"Unexpected Error: {str(e)}")
```

---

## 完整示例

### Python客户端

```python
import requests
from typing import Dict, List, Optional

class AURUMClient:
    """AURUM API客户端"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_account(self) -> Dict:
        """获取账户信息"""
        response = requests.get(
            f"{self.base_url}/account",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_positions(self) -> List[Dict]:
        """获取持仓"""
        response = requests.get(
            f"{self.base_url}/positions",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["positions"]

    def create_order(
        self,
        symbol: str,
        side: str,
        size: float,
        leverage: int = 5,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """创建订单"""
        order_data = {
            "symbol": symbol,
            "side": side,
            "type": "market",
            "size": size,
            "leverage": leverage
        }

        if stop_loss:
            order_data["stop_loss"] = stop_loss
        if take_profit:
            order_data["take_profit"] = take_profit

        response = requests.post(
            f"{self.base_url}/orders",
            json=order_data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def close_position(self, symbol: str, size: Optional[float] = None) -> Dict:
        """平仓"""
        close_data = {"symbol": symbol}
        if size:
            close_data["size"] = size

        response = requests.post(
            f"{self.base_url}/positions/close",
            json=close_data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_performance(self, period: str = "7d") -> Dict:
        """获取性能指标"""
        response = requests.get(
            f"{self.base_url}/performance",
            params={"period": period},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# 使用示例
if __name__ == "__main__":
    # 初始化客户端
    client = AURUMClient(
        base_url="http://localhost:8000/api/v1",
        token="your_token_here"
    )

    # 获取账户信息
    account = client.get_account()
    print(f"账户余额: ${account['balance']['total']:.2f}")

    # 获取持仓
    positions = client.get_positions()
    print(f"当前持仓数: {len(positions)}")

    # 创建订单
    order = client.create_order(
        symbol="XAUUSDT",
        side="buy",
        size=0.1,
        leverage=5,
        stop_loss=2019.25,
        take_profit=2111.50
    )
    print(f"订单ID: {order['order_id']}")

    # 获取性能
    performance = client.get_performance(period="7d")
    print(f"7日收益率: {performance['metrics']['total_return']:.2%}")
```

---

## 速率限制

### 限制规则

| 端点类型 | 限制 | 时间窗口 |
|---------|------|---------|
| 市场数据 | 100次 | 1分钟 |
| 账户查询 | 50次 | 1分钟 |
| 交易操作 | 20次 | 1分钟 |
| 策略管理 | 10次 | 1分钟 |

### 响应头

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1708070460
```

### 超限处理

```python
import time

def api_call_with_retry(func, max_retries=3):
    """带重试的API调用"""
    for i in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # 速率限制，等待后重试
                retry_after = int(e.response.headers.get('Retry-After', 60))
                print(f"Rate limited, waiting {retry_after}s...")
                time.sleep(retry_after)
            else:
                raise
    raise Exception("Max retries exceeded")
```

---

## 📞 获取帮助

- 📖 [完整用户手册](./02_完整用户手册.md)
- ❓ [常见问题FAQ](./05_常见问题FAQ.md)
- 💬 [API论坛](https://community.aurum.example.com/api)
- 📧 [技术支持](mailto:api@aurum.example.com)

---

**祝你开发顺利！** 🚀

*最后更新: 2026-02-16*
*API版本: v1.0*
