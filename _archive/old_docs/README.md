# 黄金崩盘预警系统 v3.0

<div align="center">

🏆 **Gold Crash Early Warning System**

⚡ 分钟级趋势预警 | 🧠 DeepSeek AI驱动 | 📱 飞书实时通知

</div>

---

## 📖 项目简介

这是一个**硬核量化预警系统**,专为黄金交易者设计。它不是用来"拼手速"赢过华尔街高频交易的,而是帮你在**阴跌转暴跌**的关键时刻保护资金,在宏观数据发布前后的剧烈波动中及时预警。

### 核心功能

1. **市场哨兵 (Market Sentinel)**: 
   - 实时监控 Binance PAXG/USDT (黄金7×24h代理)
   - 检测1分钟/5分钟异常跌幅
   - 高频时段自动加倍监控频率

2. **舆情猎手 (News Hunter)**:
   - 抓取 ForexLive、Investing.com 等财经新闻
   - 过滤黄金相关突发消息
   - RSS 订阅,无需浏览器模拟

3. **决策引擎 (The Brain)**:
   - DeepSeek-V3 分析新闻情感 (-10到+10评分)
   - 识别重大利空事件 (美联储、非农、CPI等)
   - 智能判断紧急程度

4. **飞书推送**:
   - 富文本卡片消息
   - 价格/涨跌幅/分析结果一目了然
   - 防骚扰冷却机制

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- 稳定的网络连接 (访问 Binance API 和 DeepSeek API)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置系统

复制配置模板:

```bash
copy env.example .env
```

编辑 `.env` 文件,填入你的配置:

```env
# DeepSeek API (https://platform.deepseek.com/)
DEEPSEEK_API_KEY=sk-your-api-key-here

# 飞书 Webhook (在飞书群里添加自定义机器人)
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-here

# 预警阈值 (根据你的风险偏好调整)
THRESHOLD_PRICE_DROP_1M=-0.003  # 1分钟跌0.3%触发
THRESHOLD_PRICE_DROP_5M=-0.008  # 5分钟跌0.8%触发
THRESHOLD_SENTIMENT=-7          # AI评分低于-7触发

# 监控频率
PRICE_CHECK_INTERVAL=3          # 每3秒检查一次价格
NEWS_CHECK_INTERVAL=60          # 每60秒检查一次新闻

# 高频时段 (北京时间,美股盘前数据和开盘时段)
HIGH_FREQUENCY_PERIODS=20:00-21:00,21:30-22:30
```

### 4. 运行系统

```bash
python main.py
```

你会看到类似这样的输出:

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆 黄金崩盘预警系统 v3.0                              ║
║     Gold Crash Early Warning System                       ║
║                                                           ║
║     ⚡ 分钟级趋势预警 | 🧠 DeepSeek AI驱动                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

📊 价格监控器启动: PAXG/USDT
📰 舆情分析器启动
```

---

## 🎯 使用场景

### 场景1: 非农数据发布夜

北京时间 20:30,美国非农就业数据即将发布。系统自动进入**高频监控模式**,检查间隔从3秒缩短到1.5秒。

- 20:29:58 - 数据公布前,黄金价格平稳
- 20:30:02 - 非农数据远超预期,美元暴涨
- 20:30:15 - 系统检测到1分钟跌幅 -0.5%
- 20:30:16 - 🚨 **飞书推送**: "黄金急跌警报! 1分钟跌幅 -0.50%"

你在手机上看到推送,立即平仓,避免了后续更大的跌幅。

### 场景2: 鲍威尔突发鹰派讲话

下午3点,你在开会。ForexLive 发布突发新闻:

> "Fed Chair Powell: Inflation remains stubborn, further rate hikes likely"

- 系统抓取到新闻
- DeepSeek 分析: `{"score": -8, "summary": "鹰派讲话利空黄金", "is_urgent": true}`
- 🚨 **飞书推送**: "舆情重大利空! AI评分 -8/10"

你看到推送,打开交易软件,发现金价刚开始下跌,及时止损。

---

## 🧠 顶级量化分析师的建议

### 1. 不要只看黄金

黄金的死敌是**美元指数 (DXY)** 和 **美债收益率 (US10Y)**。

**进阶玩法**: 修改 `price_monitor.py`,同时监控 DXY。如果 DXY 1分钟内暴涨,大概率黄金随后会跳水。这比只看黄金价格更快!

```python
# 在 PriceMonitor 类中添加
self.dxy_monitor = PriceMonitor("DXY/USDT")  # 如果交易所支持
```

### 2. 关注"流动性枯竭"时刻

- **北京时间 20:30** (美股盘前数据发布): CPI、非农、零售销售
- **北京时间 22:00** (美股开盘半小时后): 流动性最活跃

系统已内置高频时段自动加速,你也可以在 `.env` 中自定义。

### 3. 避坑 Twitter

现在的 Twitter 充斥着 Crypto 圈的假消息。如果你要用爬虫,一定要加**白名单**:

- Reuters (@Reuters)
- Bloomberg (@business)
- Walter Bloomberg (@DeItaone)
- Gold Telegraph (@GoldTelegraph_)

不要全网搜"Gold",噪音会淹没你。

### 4. 回测与优化

收集一周的警报数据后,分析:

- 假阳性率 (误报): 如果太高,调高阈值
- 假阴性率 (漏报): 如果太高,调低阈值

量化交易的本质是**不断迭代**。

---

## 📁 项目结构

```
黄金/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── price_monitor.py     # 价格监控模块
├── news_analyzer.py     # 舆情分析模块
├── notifier.py          # 飞书通知模块
├── requirements.txt     # 依赖包
├── env.example          # 配置模板
└── README.md            # 本文件
```

---

## 🔧 高级配置

### 自定义新闻源

编辑 `.env` 中的 `NEWS_FEEDS`:

```env
NEWS_FEEDS=https://www.forexlive.com/feed/news,https://www.investing.com/rss/news_25.rss,https://your-custom-feed.com/rss
```

### 调整警报冷却时间

编辑 `price_monitor.py` 和 `news_analyzer.py`:

```python
self.alert_cooldown = 300  # 5分钟冷却,避免重复推送
```

### 添加更多监控标的

修改 `config.py`:

```python
GOLD_SYMBOL = "XAUUSD"  # 如果你的交易所支持现货黄金
```

---

## 🐛 故障排查

### 问题1: 无法获取价格

**错误**: `❌ 获取价格失败: Exchange not available`

**解决**: 
- 检查网络连接
- 确认 Binance API 可访问 (可能需要代理)
- 尝试更换交易所: `self.exchange = ccxt.okx()`

### 问题2: DeepSeek API 调用失败

**错误**: `❌ DeepSeek API 调用失败: Invalid API key`

**解决**:
- 检查 `.env` 中的 `DEEPSEEK_API_KEY` 是否正确
- 访问 https://platform.deepseek.com/ 确认 API Key 有效
- 检查账户余额是否充足

### 问题3: 飞书推送失败

**错误**: `❌ 飞书推送失败: {"code": 19001}`

**解决**:
- 检查 Webhook URL 是否正确
- 确认机器人的**安全设置**中添加了关键词 `⚠️`
- 测试 Webhook: `curl -X POST -H "Content-Type: application/json" -d '{"msg_type":"text","content":{"text":"test"}}' YOUR_WEBHOOK_URL`

---

## 📊 性能指标

在标准配置下 (3秒价格检查 + 60秒新闻检查):

- **CPU 占用**: < 5%
- **内存占用**: < 100MB
- **网络流量**: < 10MB/小时
- **API 调用成本**: 
  - DeepSeek: ~0.01元/小时 (假设每小时分析5条新闻)
  - Binance: 免费
  - 飞书: 免费

**24小时运行成本**: < 0.5元 (主要是 DeepSeek API)

---

## ⚠️ 免责声明

本系统仅供**学习和研究**使用,不构成任何投资建议。

- 金融市场有风险,投资需谨慎
- 系统可能存在延迟、误报、漏报
- 作者不对使用本系统造成的任何损失负责
- 请在充分理解代码逻辑后使用

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

如果这个项目帮到了你,请给个 ⭐ Star!

---

## 📜 许可证

MIT License

---

## 💬 联系方式

有问题? 欢迎在 Issue 中讨论!

---

<div align="center">

**Built with ❤️ by 量化交易者**

*让 AI 成为你的交易助手*

</div>




