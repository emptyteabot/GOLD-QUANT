# AURUM Railway 部署检查清单

## 📋 部署前检查

### 账号和工具
- [ ] Railway账号已注册并登录
- [ ] Railway CLI已安装（`railway --version`）
- [ ] Git已安装并配置
- [ ] 已登录Railway CLI（`railway login`）

### 项目文件
- [ ] `main.py` 存在且可运行
- [ ] `config.py` 配置正确
- [ ] `requirements.txt` 包含所有依赖
- [ ] `railway.json` 配置文件存在
- [ ] `nixpacks.toml` 构建配置存在
- [ ] `Procfile` 进程配置存在
- [ ] `.gitignore` 已配置（不提交密钥）

### API密钥准备
- [ ] OKX API密钥（API Key, Secret, Passphrase）
- [ ] 飞书Webhook URL
- [ ] Gemini API密钥
- [ ] Tushare Token
- [ ] Alpha Vantage API密钥

---

## 🚀 部署步骤

### 1. 初始化项目
```bash
cd /c/Users/陈盈桦/Desktop/Desktop_整理_2026-02-09_172732/Folders/黄金
railway init
```
- [ ] 项目创建成功
- [ ] 环境选择正确（production）

### 2. 配置环境变量
在Railway Dashboard中添加：
- [ ] OKX_API_KEY
- [ ] OKX_SECRET_KEY
- [ ] OKX_PASSPHRASE
- [ ] FEISHU_WEBHOOK_URL
- [ ] GEMINI_API_KEY
- [ ] TUSHARE_TOKEN
- [ ] ALPHAVANTAGE_API_KEY
- [ ] 其他配置参数（见.env.railway）

### 3. 部署代码
```bash
railway up
```
- [ ] 代码上传成功
- [ ] 构建成功
- [ ] 部署成功

### 4. 验证部署
```bash
railway logs
```
- [ ] 服务启动成功
- [ ] 无错误日志
- [ ] 连接OKX成功
- [ ] 连接Tushare成功
- [ ] 飞书推送正常

---

## ✅ 部署后验证

### 服务状态
- [ ] 服务运行中（`railway status`）
- [ ] CPU使用率正常（< 50%）
- [ ] 内存使用率正常（< 80%）
- [ ] 无崩溃记录

### 功能测试
- [ ] OKX API连接正常
- [ ] 数据获取正常（K线、宏观数据）
- [ ] Multi-Agent决策正常
- [ ] 飞书推送正常
- [ ] 风控系统正常

### 日志检查
- [ ] 无Python错误
- [ ] 无API连接错误
- [ ] 无数据获取错误
- [ ] 推送消息正常

---

## 🔧 配置优化

### 交易参数
- [ ] POSITION_SIZE_PCT=0.30（仓位30%）
- [ ] BASE_LEVERAGE=5（基础杠杆5倍）
- [ ] STOP_LOSS_PCT=0.015（止损1.5%）
- [ ] MIN_CONFIDENCE=0.50（最低置信度50%）
- [ ] MIN_SIGNAL=0.20（最低信号强度20%）

### 风控参数
- [ ] MAX_DAILY_LOSS=0.05（最大日亏损5%）
- [ ] SIGNAL_ONLY=1（仅信号模式）
- [ ] PYRAMIDING_ENABLED=1（允许加仓）

### 技术指标
- [ ] ADX_RANGE_THRESHOLD=15
- [ ] RSI_OVERSOLD=30
- [ ] RSI_OVERBOUGHT=70

---

## 📊 监控设置

### Railway Dashboard
- [ ] 打开Dashboard（`railway open`）
- [ ] 查看Metrics（CPU、内存、网络）
- [ ] 设置告警通知

### 告警配置
- [ ] CPU > 80% 告警
- [ ] 内存 > 90% 告警
- [ ] 服务崩溃告警
- [ ] 部署失败告警

### 日志监控
- [ ] 设置日志保留时间
- [ ] 配置日志过滤规则
- [ ] 定期检查错误日志

---

## 🔒 安全检查

### 密钥安全
- [ ] 密钥未提交到Git
- [ ] 使用Railway环境变量
- [ ] 定期轮换密钥
- [ ] 使用只读API（如可能）

### 访问控制
- [ ] 启用2FA认证
- [ ] 限制团队成员访问
- [ ] 配置IP白名单（如需要）

### 数据安全
- [ ] 定期备份交易记录
- [ ] 加密敏感数据
- [ ] 监控异常交易

---

## 💰 成本监控

### 资源使用
- [ ] 查看当前用量（Dashboard）
- [ ] 预估月度成本
- [ ] 设置预算告警

### 优化建议
- [ ] 使用免费额度（$5/月）
- [ ] 优化代码减少资源使用
- [ ] 按需扩展资源

---

## 🐛 故障排查

### 常见问题检查
- [ ] requirements.txt是否完整
- [ ] 环境变量是否正确
- [ ] Python版本是否兼容（3.11）
- [ ] 依赖包是否安装成功

### 日志分析
- [ ] 查看启动日志
- [ ] 查看错误日志
- [ ] 查看API调用日志
- [ ] 查看交易日志

### 性能优化
- [ ] 减少API调用频率
- [ ] 使用缓存
- [ ] 优化数据库查询
- [ ] 减少内存使用

---

## 📚 文档和备份

### 文档完整性
- [ ] Railway部署指南已阅读
- [ ] 系统技术文档已了解
- [ ] 快速参考卡片已保存

### 备份计划
- [ ] 代码已推送到Git
- [ ] 配置文件已备份
- [ ] 环境变量已记录（安全位置）
- [ ] 交易记录已导出

---

## 🎯 下一步行动

### 短期（1周内）
- [ ] 监控系统运行状态
- [ ] 收集交易数据
- [ ] 分析策略表现
- [ ] 调整参数优化

### 中期（1月内）
- [ ] 根据实盘数据优化策略
- [ ] 增加新的技术指标
- [ ] 改进风控系统
- [ ] 扩展功能

### 长期（3月内）
- [ ] 引入机器学习优化
- [ ] 多策略组合
- [ ] 自动化参数调优
- [ ] 跨品种套利

---

## ✨ 成功标准

### 技术指标
- [ ] 服务可用性 > 99%
- [ ] 响应时间 < 1秒
- [ ] 错误率 < 0.1%
- [ ] 数据准确率 100%

### 交易指标
- [ ] 月收益率 > 1.5%
- [ ] 最大回撤 < 2%
- [ ] 胜率 > 40%
- [ ] 盈亏比 > 2

### 风控指标
- [ ] 无爆仓事件
- [ ] 止损执行率 100%
- [ ] 单日最大亏损 < 5%
- [ ] 总仓位 < 75%

---

## 📞 支持和帮助

### 遇到问题？
1. 查看[Railway部署指南](./docs/Railway部署指南.md)
2. 查看[常见问题](./docs/Railway部署指南.md#常见问题)
3. 查看Railway日志：`railway logs`
4. 访问Railway文档：https://docs.railway.app/

### 紧急情况
1. 立即停止服务：`railway down`
2. 检查日志找出问题
3. 修复后重新部署：`railway up`

---

**检查完成后，开始部署：**
```bash
./deploy-to-railway.sh
```

**祝部署成功！** 🚀
