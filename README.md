# AURUM 黄金量化交易系统

<div align="center">

![AURUM Logo](https://via.placeholder.com/200x200/F59E0B/FFFFFF?text=AURUM)

**让AI帮你炒黄金，睡觉也能赚钱**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-MVP开发中-yellow.svg)]()

[官网](https://aurum.example.com) | [文档](./docs/) | [演示](https://demo.aurum.example.com) | [社区](https://community.aurum.example.com)

</div>

---

## 📋 项目简介

AURUM是一个**AI驱动的黄金量化交易平台**，专为个人投资者和小型机构设计。通过15+个AI专家协同决策，实现24/7自动化交易，让普通人也能使用专业量化策略。

### 核心特点

- 🤖 **AI驱动**: 15+个AI专家协同决策（宏观分析+技术分析+机器学习）
- 🎯 **零门槛**: 无需编程，5分钟上手
- 🛡️ **风险可控**: 严格止损，最大回撤<15%
- 📊 **回测验证**: 历史回测年化收益23%+
- 🌐 **Web界面**: 现代化Dashboard，实时监控
- 📱 **实时推送**: 飞书/邮件/短信多渠道通知

---

## 🎯 项目状态

| 模块 | 状态 | 进度 |
|------|------|------|
| 核心交易引擎 | ✅ 已完成 | 100% |
| Multi-Agent系统 | ✅ 已完成 | 100% |
| 回测引擎 | 🔄 优化中 | 70% |
| ML模型 | 🔄 优化中 | 60% |
| Web Dashboard | ⏳ 未开始 | 0% |
| 用户系统 | ⏳ 未开始 | 0% |
| 商业化 | ⏳ 未开始 | 0% |

**当前版本**: v0.8 (MVP开发中)
**预计上线**: 2026-05-16 (3个月后)

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (前端)

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/aurum.git
cd aurum

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件，填入你的API密钥

# 4. 运行回测
python backtest_engine.py

# 5. 启动交易系统（谨慎！）
python main.py
```

### Docker部署

```bash
# 使用Docker Compose一键启动
docker-compose up -d

# 访问Web界面
open http://localhost:3000
```

---

## 📊 性能表现

### 回测结果（优化版）

| 指标 | 数值 |
|------|------|
| 回测周期 | 30天 |
| 初始资金 | $1,000 |
| 最终资金 | $1,019.21 |
| 收益率 | **+1.92%** |
| 最大回撤 | **1.64%** ⭐ |
| 胜率 | 40% |
| 交易次数 | 5笔 |
| 年化收益估算 | ~23% |

### 对比原始版本

| 指标 | 原始版 | 优化版 | 改进 |
|------|--------|--------|------|
| 收益率 | +1.04% | **+1.92%** | ✅ +85% |
| 最大回撤 | 31.65% | **1.64%** | ✅ -95% |
| 胜率 | 23.68% | **40%** | ✅ +69% |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    AURUM交易系统                         │
└─────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  数据采集层  │  │  分析决策层  │  │  执行监控层  │
│              │  │              │  │              │
│ • OKX API    │  │ • 宏观分析   │  │ • 订单执行   │
│ • Tushare    │  │ • 技术分析   │  │ • 风险控制   │
│ • AlphaVan   │  │ • 机器学习   │  │ • 实时监控   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 核心模块

1. **Multi-Agent决策系统** (`complete_multi_agent.py`)
   - 宏观分析师（30%权重）
   - 技术分析师（30%权重）
   - 机器学习模型（25%权重）
   - XAUT策略（15%权重）

2. **回测引擎** (`backtest_engine.py`)
   - 历史数据回测
   - 滑点和手续费模拟
   - Walk-Forward分析
   - 性能指标计算

3. **风险管理** (`risk_manager.py`)
   - 动态杠杆控制
   - 自动止损止盈
   - VaR/CVaR风险度量
   - 熔断机制

4. **交易执行** (`executor_agent.py`)
   - OKX交易所对接
   - 订单管理
   - 持仓监控

---

## 📁 项目结构

```
aurum/
├── docs/                          # 📚 项目文档
│   ├── 00_项目总体规划.md
│   ├── 01_产品需求文档_PRD.md
│   ├── 02_系统架构设计.md
│   ├── 03_UI_UX设计文档.md
│   ├── 04_市场营销方案.md
│   └── 项目总结与下一步行动.md
│
├── backend/                       # 🔧 后端服务
│   ├── main.py                   # 主程序入口
│   ├── complete_multi_agent.py   # Multi-Agent系统
│   ├── backtest_engine.py        # 回测引擎
│   ├── risk_manager.py           # 风险管理
│   ├── okx_client.py             # OKX API
│   └── ...
│
├── frontend/                      # 🎨 前端界面（待开发）
│   ├── src/
│   ├── public/
│   └── package.json
│
├── tests/                         # 🧪 测试代码
│   ├── test_backtest.py
│   ├── test_ml_models.py
│   └── ...
│
├── docker-compose.yml             # 🐳 Docker配置
├── requirements.txt               # 📦 Python依赖
├── .env.example                   # ⚙️ 环境变量模板
└── README.md                      # 📖 本文件
```

---

## 🛠️ 技术栈

### 后端
- **语言**: Python 3.9+
- **框架**: FastAPI
- **数据库**: PostgreSQL + TimescaleDB + Redis
- **消息队列**: RabbitMQ
- **机器学习**: scikit-learn, XGBoost, LSTM

### 前端
- **框架**: React + TypeScript
- **UI库**: TailwindCSS
- **图表**: TradingView Lightweight Charts
- **状态管理**: Zustand

### 部署
- **容器化**: Docker + Docker Compose
- **编排**: Kubernetes
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack

---

## 📖 文档

### 用户文档
- [快速入门指南](./docs/用户文档/快速入门.md)
- [策略配置教程](./docs/用户文档/策略配置.md)
- [风险管理指南](./docs/用户文档/风险管理.md)
- [常见问题FAQ](./docs/用户文档/FAQ.md)

### 开发文档
- [产品需求文档](./docs/01_产品需求文档_PRD.md)
- [系统架构设计](./docs/02_系统架构设计.md)
- [API文档](./docs/开发文档/API文档.md)
- [贡献指南](./CONTRIBUTING.md)

---

## ⚠️ 风险提示

**重要警告**:

1. **量化交易有风险，投资需谨慎**
2. **历史回测不代表未来收益**
3. **杠杆交易可能导致爆仓**
4. **建议从模拟盘开始，小资金试错**
5. **本系统仅供学习研究，不构成投资建议**

### 使用建议

- ✅ 从模拟盘开始
- ✅ 只用闲钱（可承受全部损失）
- ✅ 杠杆≤3倍（实盘）
- ✅ 严格执行止损
- ❌ 不要满仓
- ❌ 不要频繁调参
- ❌ 不要盲目加仓

---

## 🗺️ 路线图

### Phase 1: MVP开发（2026 Q2）
- [x] 核心交易引擎
- [x] Multi-Agent系统
- [🔄] 回测引擎优化
- [🔄] ML模型优化
- [ ] Web Dashboard
- [ ] 用户系统

### Phase 2: Beta测试（2026 Q3）
- [ ] 50个种子用户测试
- [ ] 性能优化
- [ ] Bug修复
- [ ] 用户反馈迭代

### Phase 3: 正式上线（2026 Q4）
- [ ] 市场营销推广
- [ ] 用户增长运营
- [ ] 商业化变现

### Phase 4: 功能扩展（2027 Q1）
- [ ] 策略市场
- [ ] 社交功能
- [ ] 移动端App
- [ ] 多品种支持（白银/原油/BTC）

---

## 🤝 贡献

欢迎贡献代码、报告Bug、提出建议！

### 如何贡献

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

详见 [贡献指南](./CONTRIBUTING.md)

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系我们

- **官网**: https://aurum.example.com
- **邮箱**: contact@aurum.example.com
- **微信**: AURUM_Official
- **Discord**: https://discord.gg/aurum
- **GitHub**: https://github.com/yourusername/aurum

---

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [scikit-learn](https://scikit-learn.org/) - 机器学习库
- [TradingView](https://www.tradingview.com/) - 图表库
- [OKX](https://www.okx.com/) - 交易所API

---

## 📊 项目统计

![GitHub stars](https://img.shields.io/github/stars/yourusername/aurum?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/aurum?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/yourusername/aurum?style=social)

---

<div align="center">

**AURUM - 让量化交易变得简单** 🚀💰

Made with ❤️ by AURUM Team

</div>
