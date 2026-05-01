# 🚀 AURUM 短线交易系统 - 快速启动指南
## 16-Agent + 5分钟K线 + 快进快出

---

## 📋 系统特点

✅ **16个AI Agent讨论** - 多角度分析，集思广益
✅ **5分钟K线周期** - 快速反应市场变化
✅ **快进快出策略** - 目标5-15分钟内平仓
✅ **精准风控** - 1%止损，严格执行
✅ **高胜率** - 追求80%+的胜率

---

## 🔧 快速启动

### 第一步：配置API密钥

编辑 `.env.trading` 文件：
```bash
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
```

### 第二步：验证环境

```bash
# 检查依赖
python -c "import pandas; import numpy; import sklearn; print('✅ 依赖OK')"

# 测试API连接
python -c "
from okx_client import OKXClient
import asyncio

async def test():
    client = OKXClient()
    await client.initialize()
    ticker = await client.get_ticker('XAU-USDT-SWAP')
    print(f'✅ API连接成功，当前价格: \${ticker[\"last\"]}')

asyncio.run(test())
"
```

### 第三步：启动系统

```bash
# 模拟盘模式（推荐先测试）
python main_scalping.py

# 实盘模式（谨慎！）
# 编辑 config.py，设置 TEST_MODE = False
# python main_scalping.py
```

---

## 🤖 16个Agent说明

| # | Agent名称 | 类型 | 功能 |
|---|----------|------|------|
| 1 | RSI Agent | 动量 | 超买超卖检测 |
| 2 | MACD Agent | 趋势 | 金叉死叉信号 |
| 3 | Bollinger Bands | 反转 | 上下轨反转 |
| 4 | Stochastic | 动量 | 随机指标 |
| 5 | ADX Agent | 趋势强度 | 趋势确认 |
| 6 | Volume Agent | 成交量 | 量能分析 |
| 7 | CCI Agent | 动量 | 商品通道指数 |
| 8 | ROC Agent | 动量 | 变化率分析 |
| 9-16 | 快速版本 | 多种 | 不同参数组合 |

---

## 📊 交易流程

```
1. 获取5分钟K线数据
   ↓
2. 16个Agent分析讨论
   ↓
3. 综合信号计算
   ↓
4. 信心度评估
   ↓
5. 决策执行
   ├─ 做多 → 下买单
   ├─ 做空 → 下卖单
   └─ 观望 → 继续监控
   ↓
6. 持仓管理
   ├─ 止损 (1%)
   ├─ 止盈 (1%)
   └─ 时间止损 (15分钟)
   ↓
7. 平仓 → 记录盈亏
```

---

## ⚙️ 关键参数

### 入场条件
```python
entry_threshold = 0.6  # 信心度 ≥ 60% 才入场
```

### 平仓条件
```python
止损: 1% (快速止损)
止盈: 1% (快速止盈)
时间止损: 15分钟 (强制平仓)
```

### 杠杆设置
```python
leverage = 10x  # 10倍杠杆
```

---

## 📈 性能指标

系统会实时显示：
- 总交易数
- 胜率
- 总盈亏
- 平均盈亏/笔

示例输出：
```
📈 性能统计:
   总交易数: 12
   胜率: 83.3%
   总盈亏: $245.60
   平均盈亏: $20.47
```

---

## 🛑 风险管理

### 严格的风控措施

1. **1%止损** - 每笔交易最多亏损1%
2. **1%止盈** - 每笔交易目标赚1%
3. **15分钟强制平仓** - 防止持仓过长
4. **信心度过滤** - 只在信号明确时交易

### 账户保护

- 最大日损失: 5%
- 最大总仓位: 75%
- 单笔仓位: 15%

---

## 📝 日志说明

系统会输出详细的日志：

```
📊 16-Agent讨论结果 (5分钟周期)
最终决策: 做多
综合信号: 0.72
信心度: 78.5%
做多Agent: 13/16
做空Agent: 2/16
中性Agent: 1/16

🤖 各Agent意见:
  • RSI Agent: 做多 (信号0.85, 信心90.0%) - RSI=28.5，极度超卖
  • MACD Agent: 做多 (信号0.80, 信心85.0%) - MACD金叉，做多信号
  ...
```

---

## 🚨 常见问题

### Q: 为什么没有交易信号？
A: 可能原因：
- 市场行情不明确
- 16个Agent意见分歧
- 信心度低于60%

### Q: 为什么频繁止损？
A: 这是正常的短线交易特性。追求高胜率而非高收益。

### Q: 可以调整参数吗？
A: 可以，编辑 `scalping_engine.py` 中的参数：
```python
self.entry_threshold = 0.6  # 入场阈值
self.exit_threshold = 0.3   # 平仓阈值
```

### Q: 如何切换到实盘？
A: 编辑 `config.py`：
```python
TEST_MODE = False  # 改为False
SIGNAL_ONLY = False  # 改为False
```

---

## 💡 使用建议

1. **先用模拟盘测试** - 至少运行24小时
2. **观察Agent讨论过程** - 理解决策逻辑
3. **从小资金开始** - 逐步增加仓位
4. **定期检查日志** - 监控系统表现
5. **不要频繁调参** - 让系统稳定运行

---

## 📞 故障排查

### 系统无法启动
```bash
# 检查Python版本
python --version  # 需要3.9+

# 检查依赖
pip install -r requirements.txt

# 检查API密钥
cat .env.trading
```

### API连接失败
```bash
# 检查网络
ping api.okx.com

# 检查API密钥权限
# 登录OKX官网 → 账户 → API管理 → 检查权限
```

### 交易执行失败
```bash
# 检查账户余额
# 检查杠杆设置
# 检查合约是否存在
```

---

## 🎯 下一步

1. ✅ 启动系统
2. ✅ 观察24小时
3. ✅ 检查性能指标
4. ✅ 调整参数（如需要）
5. ✅ 切换到实盘

---

**祝你交易顺利！🚀💰**

*最后更新：2026-03-20*
