# 🏆 黄金崩盘预警系统 - 终极版 v4.0

<div align="center">

**Gold Crash Early Warning System - Ultimate Edition**

⚡ **Grok AI 驱动** | 🐦 **推特监控** | 📱 **微信推送** | 💼 **华尔街级**

</div>

---

## 🎯 终极版特性

### 🆕 相比基础版的升级

| 功能 | 基础版 | 终极版 |
|------|--------|--------|
| AI 引擎 | DeepSeek | **Grok-4.1** (xAI，更懂推特) |
| 推送方式 | 飞书 | **微信** (PushPlus/Server酱) |
| 推特监控 | ❌ | ✅ **8个华尔街顶级账号** |
| 监控频率 | 3秒 | **2秒** (做市商级) |
| 高级功能 | ❌ | ✅ 订单簿/资金流/多空比 |

---

## 🚀 一键启动 (无脑配置)

### 方式1: 双击启动脚本 (推荐)

1. **双击 `一键启动.bat`**
2. 脚本会自动:
   - ✅ 检查 Python 环境
   - ✅ 安装依赖包
   - ✅ 创建配置文件
   - ✅ 引导你配置微信推送
   - ✅ 运行测试
   - ✅ 启动系统

### 方式2: 手动配置 (3步)

```bash
# 步骤1: 安装依赖
pip install -r requirements.txt

# 步骤2: 配置微信推送
copy env.ultimate.example .env
notepad .env  # 填入 PUSHPLUS_TOKEN

# 步骤3: 启动系统
python main_ultimate.py
```

---

## 📱 微信推送配置 (必须)

### 方案1: PushPlus (推荐，最简单)

1. **访问**: https://www.pushplus.plus/
2. **微信扫码登录**
3. **复制 Token**
4. **在 `.env` 中填入**:
   ```env
   PUSHPLUS_TOKEN=你的token
   PUSH_METHOD=pushplus
   ```

**优点**: 
- ✅ 免费额度 200次/天
- ✅ 无需关注公众号
- ✅ 支持 HTML 格式
- ✅ 推送速度快

### 方案2: Server酱 (备选)

1. **访问**: https://sct.ftqq.com/
2. **微信扫码登录**
3. **复制 SendKey**
4. **在 `.env` 中填入**:
   ```env
   SERVERCHAN_KEY=你的key
   PUSH_METHOD=serverchan
   ```

**优点**: 
- ✅ 老牌服务，稳定
- ✅ 支持 Markdown

**缺点**: 
- ⚠️ 免费版 5次/天 (需关注公众号)

### 方案3: 企业微信 (最稳定)

适合有企业微信的用户，配置稍复杂但最稳定。

---

## 🧠 Grok AI 配置 (已内置)

你的 Grok API Key 已经填入配置文件:

```env
GROK_API_KEY=sk-cfC41IpV5W4t9ok1SK1tyH60i1L0L9yvmRIyS8b5lNfTzbif
```

**Grok 的优势**:
- ✅ **实时训练数据** (包含最新推特内容)
- ✅ **理解推特文化** (缩写、梗、emoji)
- ✅ **更准确的情感分析** (专为社交媒体优化)
- ✅ **成本低** (比 GPT-4 便宜 10倍)

---

## 🐦 推特监控配置 (可选)

### 为什么要监控推特?

华尔街交易员的信息来源:
1. **@DeItaone** (Walter Bloomberg) - 最快的财经快讯
2. **@FirstSquawk** - 实时市场播报
3. **@GoldTelegraph_** - 黄金专业分析
4. **@zerohedge** - 另类视角

**这些账号的推文比新闻网站快 5-30 分钟！**

### 如何配置?

1. **访问**: https://developer.twitter.com/
2. **申请开发者账号** (免费，需要填写申请表)
3. **创建 App**，获取 **Bearer Token**
4. **在 `.env` 中填入**:
   ```env
   TWITTER_BEARER_TOKEN=你的token
   ```

**注意**: 
- 免费版 API 有限制 (每月 50万次请求，足够用)
- 需要申请 **Elevated Access** 才能使用完整功能

**如果不配置推特**: 系统仍然可以正常运行，只是少了推特监控功能。

---

## 🎯 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    终极版黄金哨兵                        │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
   │ 价格监控 │        │ 舆情分析 │        │ 推特监控 │
   │ 2秒/次  │        │ 30秒/次 │        │ 15秒/次 │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                   │                   │
        │              ┌────▼────┐              │
        │              │ Grok AI │              │
        │              │ 情感分析 │              │
        │              └────┬────┘              │
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                       ┌────▼────┐
                       │ 微信推送 │
                       │ PushPlus│
                       └─────────┘
```

---

## 📊 监控内容

### 1. 价格监控 (做市商级)

- ✅ **PAXG/USDT** (黄金 7×24h 代理)
- ✅ **1分钟跌幅** > 0.2% → 警报
- ✅ **5分钟跌幅** > 0.6% → 警报
- ✅ **高频时段** (20:30, 22:00) 自动加速

### 2. 舆情分析

- ✅ **ForexLive** - 外汇实时新闻
- ✅ **Investing.com** - 财经综合
- ✅ **Grok AI 分析** - 情感评分 (-10到+10)

### 3. 推特监控 (华尔街顶级账号)

| 账号 | 类型 | 特点 |
|------|------|------|
| @DeItaone | 快讯 | 最快，华尔街必看 |
| @FirstSquawk | 快讯 | 实时播报 |
| @GoldTelegraph_ | 黄金 | 专业分析 |
| @Schuldensuehner | 宏观 | 德国商报记者 |
| @zerohedge | 另类 | 独特视角 |
| @RealVision | 策略 | 宏观策略 |

---

## 💡 使用场景

### 场景1: 非农数据夜 (20:30)

```
20:29:50 - 系统进入高频模式 (1秒检查一次)
20:30:00 - 非农数据公布
20:30:05 - @DeItaone 推文: "NFP beats expectations"
20:30:08 - Grok 分析: 利空黄金 (-8/10)
20:30:10 - 微信推送: "🚨 推特重要信息"
20:30:15 - 价格跌幅 -0.4%
20:30:16 - 微信推送: "🚨 黄金急跌警报"
```

你在 20:30:10 就收到预警，比只看价格快 5 秒！

### 场景2: 突发地缘冲突

```
15:30:00 - @zerohedge 推文: "Breaking: Conflict escalates"
15:30:15 - Grok 分析: 利多黄金 (+9/10)
15:30:16 - 微信推送: "⚡ 推特重要信息 - 地缘风险"
15:31:00 - 价格开始上涨
```

你提前 45 秒知道消息，可以抢先布局！

---

## 🔧 高级配置

### 调整阈值 (根据你的风险偏好)

编辑 `.env`:

```env
# 保守型 (频繁提醒)
THRESHOLD_PRICE_DROP_1M=-0.001   # 0.1%
THRESHOLD_SENTIMENT=-5

# 激进型 (只提醒重大事件)
THRESHOLD_PRICE_DROP_1M=-0.005   # 0.5%
THRESHOLD_SENTIMENT=-8
```

### 启用高级功能

```env
# 订单簿分析 (检测大单压盘)
ORDERBOOK_ANALYSIS=true

# 资金流向分析
FLOW_ANALYSIS=true

# 多空比监控
LONG_SHORT_RATIO=true
```

**注意**: 高级功能需要更多 API 调用，成本会增加。

---

## 📊 成本分析

### 24小时运行成本

| 项目 | 调用次数 | 单价 | 日成本 |
|------|---------|------|--------|
| Grok API (新闻) | ~50次 | ¥0.002 | ¥0.10 |
| Grok API (推特) | ~100次 | ¥0.002 | ¥0.20 |
| Binance API | 无限 | 免费 | ¥0 |
| 微信推送 | ~10次 | 免费 | ¥0 |
| **总计** | - | - | **¥0.30** |

**月成本**: < ¥10 (比一杯咖啡便宜)

---

## 🐛 故障排查

### 问题1: 微信推送失败

**错误**: `❌ PushPlus 推送失败`

**解决**:
1. 检查 `.env` 中的 `PUSHPLUS_TOKEN` 是否正确
2. 访问 https://www.pushplus.plus/ 确认 Token 有效
3. 检查是否关注了 PushPlus 公众号
4. 尝试手动测试: `python test_ultimate.py`

### 问题2: Grok API 调用失败

**错误**: `❌ Grok API 调用失败`

**解决**:
1. 你的 API Key 已经填入，应该可以直接用
2. 如果失败，访问 https://console.x.ai/ 检查余额
3. 确认网络可以访问 api.x.ai

### 问题3: 推特 API 连接失败

**错误**: `❌ 推特 API 连接失败`

**解决**:
1. 检查 `TWITTER_BEARER_TOKEN` 是否正确
2. 确认申请了 **Elevated Access** (免费版有限制)
3. 如果不需要推特监控，可以跳过此配置

### 问题4: 无法获取价格

**错误**: `❌ 获取价格失败`

**解决**:
1. 检查网络是否可以访问 Binance
2. 如果在国内，可能需要配置代理
3. 尝试更换交易所: 编辑 `price_monitor.py`

---

## 🚀 24小时运行

### Windows

**方式1: 任务计划程序**

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器: 开机时
4. 操作: 启动程序 `python.exe`
5. 参数: `main_ultimate.py`
6. 起始于: `C:\Users\陈盈桦\Desktop\黄金`

**方式2: 后台运行**

```bash
# 使用 pythonw (无窗口)
start /B pythonw main_ultimate.py
```

### Linux/Mac

```bash
# 使用 screen
screen -S gold_sentinel
python main_ultimate.py
# 按 Ctrl+A 然后 D 退出

# 重新连接
screen -r gold_sentinel
```

### 云服务器 (推荐)

- **阿里云轻量服务器**: ¥24/月
- **腾讯云**: ¥25/月
- **AWS 免费套餐**: 免费 12个月

---

## 📈 进阶玩法

### 1. 添加美元指数监控

黄金与 DXY 负相关，DXY 暴涨 → 黄金跳水。

编辑 `main_ultimate.py`:

```python
self.dxy_monitor = PriceMonitor(config.DXY_SYMBOL)
```

### 2. 记录历史数据

在 `price_monitor.py` 中添加:

```python
import sqlite3

def save_to_db(self, price, timestamp):
    conn = sqlite3.connect('gold_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prices VALUES (?, ?)", (timestamp, price))
    conn.commit()
    conn.close()
```

### 3. 接入 n8n 自动化

在 `.env` 中配置:

```env
N8N_ENABLED=true
N8N_WEBHOOK_URL=你的n8n_webhook
```

系统会将警报同时发送到 n8n，你可以在 n8n 中:
- 自动记录到 Google Sheets
- 发送到 Telegram
- 触发其他自动化流程

---

## 🎓 华尔街交易员的建议

### 1. 不要过度依赖

这是**辅助工具**，不是圣杯。重大数据发布前 (非农、CPI) 仍需手动关注。

### 2. 观察一周后调整

收集一周数据，分析:
- **假阳性率** (误报): 太高 → 提高阈值
- **假阴性率** (漏报): 太高 → 降低阈值

### 3. 关注流动性

北京时间 **20:30** 和 **22:00** 是跳水高发期，系统已自动加速监控。

### 4. 推特白名单

只看顶级账号，不要全网搜"Gold"，噪音会淹没你。

---

## ⚠️ 免责声明

- 本系统仅供**学习和研究**使用
- 不构成任何投资建议
- 金融市场有风险，投资需谨慎
- 作者不对使用本系统造成的任何损失负责

---

## 📞 获取帮助

1. **运行测试**: `python test_ultimate.py`
2. **查看日志**: 系统会打印详细错误信息
3. **检查配置**: 确认 `.env` 文件正确

---

<div align="center">

**Built with ❤️ by 华尔街量化交易员**

*让 AI 成为你的交易助手*

🚀 **现在就开始！双击 `一键启动.bat`**

</div>




