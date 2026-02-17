# 风控系统V2 - 快速参考

## 🚀 快速开始

```python
from risk_manager_enhanced_v2 import RiskManagerEnhancedV2

# 初始化
rm = RiskManagerEnhancedV2()
rm.set_daily_start_equity(10000)

# 计算仓位（自动应用所有风控）
position = rm.calculate_position_size(
    account={'total_equity': 10000, 'available': 9000},
    price=2800,
    klines_df=klines_df
)
```

## 📊 核心功能

### 1. 杠杆限制
- **最大杠杆**: 10x（从20x降低）
- **基础杠杆**: 5x
- **动态调整**: 根据波动率自动调整

### 2. VaR/CVaR
```python
var, cvar = rm.calculate_var_cvar(returns, confidence=0.95)
# VaR: 95%置信度下的最大损失
# CVaR: 超过VaR的平均损失
```

### 3. 熔断机制
触发条件：
- ⚠️ 单日亏损 > 8%
- ⚠️ 波动率 > 5%
- ⚠️ 连续3笔亏损

```python
breaker = rm.check_circuit_breaker(account, klines_df)
if breaker['triggered']:
    print(f"熔断: {breaker['reason']}")
```

### 4. 流动性评估
```python
liquidity = rm.assess_liquidity(klines_df)
# score: 0-1评分
# risk_level: 低/中/高
# can_trade: True/False
```

### 5. 动态杠杆
| 波动率 | 杠杆 |
|--------|------|
| < 2% | 10x |
| 2-4% | 5x |
| > 4% | 2-3x |

## 🔧 关键参数

```python
# 风控阈值
MAX_LEVERAGE = 10
CIRCUIT_BREAKER_LOSS = 0.08  # 8%
CIRCUIT_BREAKER_VOLATILITY = 0.05  # 5%
MIN_LIQUIDITY_SCORE = 0.6

# VaR配置
VAR_CONFIDENCE = 0.95
VAR_WINDOW = 100
```

## 📈 使用流程

```
1. 熔断检查 → 2. 流动性检查 → 3. 计算仓位 → 4. 执行交易
     ↓              ↓                ↓              ↓
   通过           通过            获得仓位        记录交易
```

## ⚡ 常用方法

```python
# 设置每日起始权益
rm.set_daily_start_equity(equity)

# 计算仓位
position = rm.calculate_position_size(account, price, klines_df)

# 熔断检查
breaker = rm.check_circuit_breaker(account, klines_df)

# 流动性评估
liquidity = rm.assess_liquidity(klines_df)

# 移动止损
new_stop = rm.update_trailing_stop(position, current_price, klines_df)

# 记录交易
rm.record_trade(pnl, return_pct)

# 风险报告
report = rm.get_risk_report(account)
```

## 📊 返回值示例

### position 对象
```python
{
    'size': 357,              # 合约张数
    'oz_size': 0.357,         # 盎司数
    'margin': 199.92,         # 保证金
    'leverage': 5,            # 杠杆
    'stop_loss': 2760.94,     # 止损价
    'take_profit': 2917.17,   # 止盈价
    'risk_amount': 2.79,      # 风险金额
    'atr': 19.53,             # ATR值
    'var': -0.0412,           # VaR
    'cvar': -0.0523,          # CVaR
    'kelly_fraction': 0.20    # Kelly仓位
}
```

### report 对象
```python
{
    'account_equity': 10000,
    'circuit_breaker_active': False,
    'trade_count': 20,
    'position_count': 1,
    'win_rate': 0.70,
    'avg_win': 50.0,
    'avg_loss': -30.0,
    'total_pnl': 400.0,
    'var_95': -0.0412,
    'cvar_95': -0.0523
}
```

## ⚠️ 注意事项

1. **每日初始化**: 交易日开始时调用 `set_daily_start_equity()`
2. **K线数据**: 至少需要20根K线才能计算波动率和流动性
3. **熔断冷却**: 触发后需等待1小时才能恢复
4. **参数调优**: 根据实盘表现调整阈值

## 🧪 测试命令

```bash
# 单元测试
python test_risk_manager_v2.py

# 演示程序
python demo_risk_manager_v2.py
```

## 📞 支持

- 文档: `docs/07_风险管理优化方案.md`
- 集成指南: `INTEGRATION_GUIDE.py`
- 测试用例: `test_risk_manager_v2.py`
