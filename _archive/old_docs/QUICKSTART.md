# 快速开始指南

## 🚀 三步启动系统

### 第一步: 安装依赖

打开命令行 (CMD 或 PowerShell)，进入项目目录:

```bash
cd C:\Users\陈盈桦\Desktop\黄金
pip install -r requirements.txt
```

### 第二步: 配置密钥

1. **获取 DeepSeek API Key**
   - 访问: https://platform.deepseek.com/
   - 注册账号并充值 (建议充值10元，够用很久)
   - 创建 API Key

2. **配置飞书机器人**
   - 在飞书创建一个群 (可以只有你一个人)
   - 群设置 → 群机器人 → 添加机器人 → 自定义机器人
   - 安全设置选择"自定义关键词"，填入: `⚠️`
   - 复制 Webhook URL

3. **创建配置文件**
   
   复制 `env.example` 为 `.env`:
   
   ```bash
   copy env.example .env
   ```
   
   用记事本打开 `.env`，填入你的配置:
   
   ```env
   DEEPSEEK_API_KEY=sk-你的密钥
   FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook
   ```

### 第三步: 启动系统

**方式1: 使用启动脚本 (推荐)**

双击 `start.bat` 文件，按照提示操作。

**方式2: 手动启动**

```bash
# 先测试 (推荐)
python test.py

# 正式运行
python main.py
```

---

## 📱 飞书推送示例

系统启动后，你会在飞书收到类似这样的消息:

```
⚠️ 系统启动
✅ 黄金崩盘预警系统已启动

监控标的: PAXG/USDT (黄金代理)
价格检查间隔: 3秒
新闻检查间隔: 60秒
跌幅预警阈值: -0.30% (1分钟)

⏰ 2026-01-31 15:30:00
```

当检测到异常时，会收到警报:

```
⚠️ 黄金急跌警报
🚨 黄金价格急速下跌!

1分钟跌幅: -0.52%
5分钟跌幅: -0.85%

⚡ 建议立即检查持仓风险!

当前价格: $2650.50
涨跌幅: 📉 -0.52%

⏰ 2026-01-31 20:30:15
```

---

## 🎯 使用建议

### 1. 首次使用

运行 `python test.py` 进行全面测试，确保:
- ✅ 配置正确
- ✅ 飞书推送正常
- ✅ 能获取价格数据
- ✅ DeepSeek API 可用
- ✅ 新闻源可访问

### 2. 调整阈值

根据你的交易风格调整 `.env` 中的阈值:

**保守型** (频繁提醒):
```env
THRESHOLD_PRICE_DROP_1M=-0.002  # 0.2%
THRESHOLD_SENTIMENT=-5
```

**激进型** (只提醒重大事件):
```env
THRESHOLD_PRICE_DROP_1M=-0.005  # 0.5%
THRESHOLD_SENTIMENT=-8
```

### 3. 24小时运行

**Windows**: 使用任务计划程序设置开机自启

**Linux/Mac**: 使用 systemd 或 screen

```bash
# 使用 screen 后台运行
screen -S gold_sentinel
python main.py
# 按 Ctrl+A 然后按 D 退出 (程序继续运行)

# 重新连接
screen -r gold_sentinel
```

### 4. 成本控制

- **DeepSeek API**: 每条新闻分析约 0.002元，每天约 0.3元
- **Binance API**: 免费
- **飞书**: 免费

**月成本**: < 10元

---

## ⚠️ 常见问题

### Q1: 为什么用 PAXG/USDT 而不是现货黄金?

**A**: PAXG 是 Paxos 发行的黄金代币，1 PAXG = 1盎司黄金，在 Binance 上 7×24 小时交易。相比传统黄金市场:
- ✅ 实时价格 (不受交易时间限制)
- ✅ API 稳定
- ✅ 流动性好

价格走势与 XAU/USD 高度相关 (相关系数 > 0.99)。

### Q2: 系统会漏掉重要消息吗?

**A**: 可能会。这个系统的定位是**辅助工具**，不是替代你的判断。建议:
- 重大数据发布前 (非农、CPI) 手动关注
- 配合交易软件的价格提醒
- 系统主要用于捕捉"意外事件"

### Q3: 如何避免误报?

**A**: 
1. 提高阈值 (如 1分钟跌幅从 -0.3% 改为 -0.5%)
2. 增加警报冷却时间 (修改代码中的 `alert_cooldown`)
3. 观察一周后根据数据调整

### Q4: 可以监控其他品种吗?

**A**: 可以! 修改 `config.py`:

```python
# 监控白银
GOLD_SYMBOL = "PAXG/USDT"  # 改为 "XAGUSD" 或其他

# 同时监控多个品种需要修改代码架构
```

---

## 📊 进阶玩法

### 1. 添加美元指数监控

黄金与美元指数 (DXY) 负相关。当 DXY 暴涨时，黄金通常会跌。

修改 `main.py`，添加 DXY 监控器:

```python
self.dxy_monitor = PriceMonitor("DXY/USDT")  # 如果交易所支持
```

### 2. 记录历史数据

在 `price_monitor.py` 中添加数据库记录:

```python
import sqlite3

# 保存价格到数据库
def save_to_db(self, price, timestamp):
    conn = sqlite3.connect('gold_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO prices VALUES (?, ?)", 
        (timestamp, price)
    )
    conn.commit()
    conn.close()
```

### 3. 回测优化

收集一周数据后，分析最佳阈值:

```python
# 分析脚本
import pandas as pd

df = pd.read_sql("SELECT * FROM prices", conn)
df['change_1m'] = df['price'].pct_change(20)  # 假设3秒一次，20次=1分钟

# 找出最佳阈值
optimal_threshold = df['change_1m'].quantile(0.05)  # 5%分位数
print(f"建议阈值: {optimal_threshold:.2%}")
```

---

## 🛡️ 安全提示

1. **不要分享 .env 文件** (包含你的密钥)
2. **定期检查 API 余额** (避免欠费停止服务)
3. **不要过度依赖系统** (它是辅助工具，不是圣杯)
4. **测试后再实盘使用** (先观察几天，确认稳定性)

---

## 📞 获取帮助

遇到问题? 按优先级:

1. **查看 README.md** 的故障排查章节
2. **运行 `python test.py`** 诊断问题
3. **检查日志输出** (系统会打印详细错误信息)
4. **提交 Issue** (如果是 Bug)

---

**祝交易顺利! 🚀**




