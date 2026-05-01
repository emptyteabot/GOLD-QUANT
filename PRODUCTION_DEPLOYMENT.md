# 🚀 AURUM 黄金量化系统 - 生产部署指南
## 投入真金白银前的完整检查清�?
---

## 📋 第一步：环境准备

### 1.1 系统要求
- [ ] Python 3.9+ 已安�?- [ ] pip 已安�?- [ ] Git 已安�?- [ ] 网络连接正常（能访问OKX API�?
### 1.2 安装依赖
```bash
cd ~/Desktop/GOLD-QUANT
pip install -r requirements.txt
```

**关键依赖检查：**
```bash
python -c "import streamlit; import pandas; import numpy; import sklearn; import xgboost; print('�?所有依赖已安装')"
```

---

## 🔐 第二步：API密钥配置

### 2.1 获取OKX API密钥

1. 访问 https://www.okx.com/account/my-api
2. 创建新的API密钥，权限设置：
   - �?交易权限（Trade�?   - �?账户权限（Account�?   - �?持仓权限（Position�?   - �?提现权限（不需要）

3. 复制以下信息�?   - API Key
   - Secret Key
   - Passphrase

### 2.2 配置环境变量

**方式一：编�?.env.trading 文件**
```bash
# 复制模板
cp .env.trading.example .env.trading

# 编辑文件，填入你的API密钥
# 使用你喜欢的编辑器打开 .env.trading
```

**方式二：直接设置环境变量**
```bash
# Windows PowerShell
$env:OKX_API_KEY="your_api_key"
$env:OKX_SECRET_KEY="your_secret_key"
$env:OKX_PASSPHRASE="your_passphrase"

# Linux/Mac
export OKX_API_KEY="your_api_key"
export OKX_SECRET_KEY="your_secret_key"
export OKX_PASSPHRASE="your_passphrase"
```

### 2.3 验证API连接
```bash
python -c "
from okx_client import OKXClient
import asyncio

async def test():
    client = OKXClient()
    await client.initialize()
    account = await client.get_account_balance()
    print(f'�?账户连接成功�?)
    print(f'   总权�? \${account[\"total_equity\"]:.2f}')
    print(f'   可用资金: \${account[\"available\"]:.2f}')

asyncio.run(test())
"
```

---

## ⚠️ 第三步：风险管理配置

### 3.1 关键风险参数

| 参数 | 推荐�?| 说明 |
|------|--------|------|
| RISK_PER_TRADE | 0.01 | 每笔交易风险 = 账户权益�?% |
| POSITION_SIZE_PCT | 0.15 | 单笔仓位 = 账户权益�?5% |
| MAX_TOTAL_POSITION | 0.75 | 最大总仓�?= 账户权益�?5% |
| STOP_LOSS_PCT | 0.10 | 止损 = 入场价的10% |
| MAX_LEVERAGE | 20 | 最大杠�?= 20�?|
| MAX_DAILY_LOSS | 0.05 | 最大日损失 = 账户权益�?% |

### 3.2 风险等级选择

**保守型（推荐新手�?*
```
RISK_PER_TRADE=0.005      # 0.5%
POSITION_SIZE_PCT=0.10    # 10%
MAX_LEVERAGE=5            # 5�?MAX_DAILY_LOSS=0.03       # 3%
```

**平衡型（推荐�?*
```
RISK_PER_TRADE=0.01       # 1%
POSITION_SIZE_PCT=0.15    # 15%
MAX_LEVERAGE=10           # 10�?MAX_DAILY_LOSS=0.05       # 5%
```

**激进型（高风险�?*
```
RISK_PER_TRADE=0.02       # 2%
POSITION_SIZE_PCT=0.25    # 25%
MAX_LEVERAGE=20           # 20�?MAX_DAILY_LOSS=0.10       # 10%
```

### 3.3 验证风险管理
```bash
python -c "
from risk_manager import RiskManager
import config

rm = RiskManager()
account = {
    'total_equity': 10000,
    'available': 9000
}

result = rm.calculate_position_size(account, price=2000, leverage=10)
print(f'�?风险管理验证成功�?)
print(f'   仓位大小: {result[\"size\"]} �?)
print(f'   所需保证�? \${result[\"margin\"]:.2f}')
print(f'   止损价格: \${result[\"stop_loss\"]:.2f}')
print(f'   止盈价格: \${result[\"take_profit\"]:.2f}')
"
```

---

## 🧪 第四步：回测验证

### 4.1 运行回测
```bash
# 运行完整回测
python backtest_engine.py

# 或运行优化版回测
python backtest_optimized.py
```

### 4.2 检查回测结�?
**关键指标�?*
- �?收益�?> 0%
- �?最大回�?< 15%
- �?胜率 > 30%
- �?盈亏�?> 1.5:1

**示例输出�?*
```
回测结果�?  初始资金: $1,000
  最终资�? $1,019.21
  收益�? +1.92%
  最大回�? 1.64%
  胜率: 40%
  交易次数: 5
  年化收益: ~23%
```

---

## 🎯 第五步：模拟盘测�?
### 5.1 启用模拟盘模�?
编辑 `config.py`，确保以下设置：
```python
# 模拟盘模式（不执行真实交易）
TEST_MODE = True

# 信号模式（只发送信号，不自动交易）
SIGNAL_ONLY = True
```

### 5.2 运行模拟�?```bash
python main.py
```

### 5.3 监控模拟盘表�?
- 运行至少 **7 �?*
- 观察信号质量
- 检查风险管理是否有�?- 记录所有交易信�?
---

## 🔴 第六步：切换到实�?
### ⚠️ 重要提示

**在切换到实盘前，请确保：**

- [ ] 已完成至�?天的模拟盘测�?- [ ] 回测结果满足预期
- [ ] 所有API密钥已正确配�?- [ ] 风险参数已根据账户大小调�?- [ ] 已阅读并理解所有风险提�?- [ ] 只投入可承受全部损失的资�?
### 6.1 切换到实�?
编辑 `config.py`�?```python
# 关闭模拟盘模�?TEST_MODE = False

# 关闭信号模式（启用自动交易）
SIGNAL_ONLY = False
```

### 6.2 启动实盘系统
```bash
python main.py
```

### 6.3 实时监控

**监控清单�?*
- [ ] 系统正常运行
- [ ] 飞书通知正常接收
- [ ] 交易信号正确生成
- [ ] 风险管理有效执行
- [ ] 账户权益变化正常

---

## 📊 第七步：持续监控

### 7.1 每日检�?
```bash
# 查看系统日志
tail -f _tmp/feishu_zh.log

# 查看交易记录
python -c "
from okx_client import OKXClient
import asyncio

async def check():
    client = OKXClient()
    await client.initialize()

    # 获取账户信息
    account = await client.get_account_balance()
    print(f'账户权益: \${account[\"total_equity\"]:.2f}')

    # 获取持仓
    positions = await client.get_all_positions()
    print(f'当前持仓: {len(positions[\"swap_positions\"])} �?)

asyncio.run(check())
"
```

### 7.2 周报�?
每周检查：
- 总收益率
- 最大回�?- 交易次数
- 胜率
- 风险指标

### 7.3 月报�?
每月检查：
- 月度收益
- 年化收益估算
- 策略有效�?- 是否需要调整参�?
---

## 🚨 故障排查

### 问题1：API连接失败
```
错误: "无法连接到OKX API"

解决方案�?1. 检查网络连�?2. 验证API密钥是否正确
3. 检查API密钥权限是否足够
4. 检查IP白名单设�?```

### 问题2：账户余额不�?```
错误: "账户可用资金不足"

解决方案�?1. 检查账户余�?2. 减少仓位大小
3. 降低杠杆倍数
4. 等待之前的交易平�?```

### 问题3：交易信号不生成
```
错误: "没有交易信号"

解决方案�?1. 检查市场行�?2. 验证技术指标计�?3. 检查决策阈值设�?4. 查看系统日志
```

---

## 📞 紧急联�?
如遇到严重问题：

1. **立即停止系统**
   ```bash
   # �?Ctrl+C 停止程序
   ```

2. **检查账户状�?*
   - 登录OKX官网
   - 查看持仓和余�?   - 手动平仓（如需要）

3. **查看日志**
   ```bash
   cat _tmp/feishu_zh.log
   ```

4. **联系支持**
   - GitHub Issues
   - 飞书群组
   - 邮件支持

---

## �?最终检查清�?
在启动实盘前，请确保所有项目都已完成：

- [ ] Python环境已安�?- [ ] 所有依赖已安装
- [ ] OKX API密钥已配�?- [ ] API连接已验�?- [ ] 风险参数已设�?- [ ] 回测已运行并通过
- [ ] 模拟盘已测试7天以�?- [ ] 实盘参数已配�?- [ ] 监控系统已准�?- [ ] 已阅读所有风险提�?- [ ] 只投入可承受损失的资�?
---

## 🎯 成功标志

系统正常运行的标志：

�?系统启动无错�?�?API连接成功
�?账户信息正确显示
�?交易信号正常生成
�?飞书通知正常接收
�?风险管理有效执行
�?账户权益稳定增长

---

**祝你交易顺利！🚀💰**

*最后更新：2026-03-20*
