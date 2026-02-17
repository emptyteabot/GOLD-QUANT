# 🚀 Streamlit Cloud 部署指南

## 快速部署（3分钟）

### 1. 访问Streamlit Cloud
```
https://share.streamlit.io
```

### 2. 登录（用GitHub账号）

### 3. 部署应用
1. 点击 "New app"
2. 选择仓库：`emptyteabot/GOLD-QUANT`
3. 选择分支：`main`
4. 主文件路径：`gold_advisor_app.py`
5. 点击 "Deploy!"

### 4. 配置环境变量（Secrets）
在App设置中添加：

```toml
# OKX API配置
OKX_API_KEY = "你的API密钥"
OKX_SECRET_KEY = "你的Secret密钥"
OKX_PASSPHRASE = "你的密码短语"

# 飞书通知
FEISHU_WEBHOOK_URL = "你的飞书Webhook"

# 授权配置（演示模式）
AUTO_ACTIVATE = "1"
DEFAULT_TIER = "PRO"

# Tushare配置（如果有）
TUSHARE_TOKEN = "你的Tushare token"
```

### 5. 等待部署完成（约2-3分钟）

### 6. 访问你的应用
```
https://你的应用名.streamlit.app
```

---

## 📝 详细步骤

### Step 1: 准备GitHub仓库
✅ 已完成 - 代码已推送到 `emptyteabot/GOLD-QUANT`

### Step 2: 登录Streamlit Cloud
1. 访问：https://share.streamlit.io
2. 点击 "Sign in with GitHub"
3. 授权Streamlit访问你的GitHub

### Step 3: 创建新应用
1. 点击右上角 "New app"
2. 填写信息：
   - **Repository**: `emptyteabot/GOLD-QUANT`
   - **Branch**: `main`
   - **Main file path**: `gold_advisor_app.py`
   - **App URL** (可选): 自定义URL

### Step 4: 配置Secrets
1. 点击 "Advanced settings"
2. 在 "Secrets" 中粘贴：

```toml
# 基础配置
AUTO_ACTIVATE = "1"
DEFAULT_TIER = "PRO"

# OKX API（如果要实盘交易）
OKX_API_KEY = "your-api-key"
OKX_SECRET_KEY = "your-secret-key"
OKX_PASSPHRASE = "your-passphrase"

# 飞书通知（可选）
FEISHU_WEBHOOK_URL = "your-webhook-url"

# Tushare（如果要A股数据）
TUSHARE_TOKEN = "your-tushare-token"
```

### Step 5: 部署
1. 点击 "Deploy!"
2. 等待构建（约2-3分钟）
3. 看到 "Your app is live!" 表示成功

---

## 🎯 部署后的URL

你的应用会部署到：
```
https://gold-quant.streamlit.app
```
或
```
https://emptyteabot-gold-quant-gold-advisor-app-xxxxx.streamlit.app
```

---

## 🔧 环境变量说明

### 必需的环境变量
```toml
AUTO_ACTIVATE = "1"          # 自动激活授权
DEFAULT_TIER = "PRO"         # 默认专业版
```

### 可选的环境变量
```toml
# OKX交易所（实盘交易需要）
OKX_API_KEY = "xxx"
OKX_SECRET_KEY = "xxx"
OKX_PASSPHRASE = "xxx"

# 飞书通知（推送通知需要）
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"

# Tushare（A股数据需要）
TUSHARE_TOKEN = "xxx"

# Alpha Vantage（美股数据需要）
ALPHA_VANTAGE_API_KEY = "xxx"
```

---

## ✅ 验证部署

### 1. 检查应用状态
访问你的应用URL，应该能看到Gold Advisor Pro界面

### 2. 检查日志
在Streamlit Cloud Dashboard中查看：
- Build logs（构建日志）
- App logs（运行日志）

### 3. 测试功能
- 查看实时行情
- 测试策略配置
- 查看交易信号

---

## 🐛 常见问题

### Q1: 部署失败？
**A**: 检查requirements.txt
- 确保所有依赖都列出
- 版本号要兼容

### Q2: 应用启动慢？
**A**: 正常现象
- 首次启动需要安装依赖（2-3分钟）
- 后续访问会快很多

### Q3: 找不到模块？
**A**: 检查文件路径
- 确保所有Python文件都在仓库中
- 检查import路径是否正确

### Q4: 环境变量不生效？
**A**: 检查Secrets配置
- 格式必须是TOML格式
- 重启应用使配置生效

---

## 💰 费用

Streamlit Cloud免费版：
- ✅ 1个公开应用
- ✅ 1GB内存
- ✅ 1个CPU核心
- ✅ 无限访问次数

如果需要更多：
- **Starter**: $20/月（3个应用）
- **Team**: $250/月（无限应用）

---

## 🔄 更新应用

### 自动更新
- 推送代码到GitHub
- Streamlit自动重新部署

```bash
git add .
git commit -m "更新应用"
git push
# Streamlit会自动检测并重新部署
```

### 手动重启
在Streamlit Cloud Dashboard中：
1. 点击应用
2. 点击 "⋮" 菜单
3. 选择 "Reboot app"

---

## 📊 监控

### 查看使用情况
在Dashboard中可以看到：
- 访问次数
- 资源使用（CPU/内存）
- 错误日志

### 设置告警
- 应用崩溃时邮件通知
- 资源使用超限提醒

---

## 🎉 部署完成后

你会得到：
- ✅ 在线访问的URL
- ✅ 自动HTTPS
- ✅ 自动重启（如果崩溃）
- ✅ 实时日志查看
- ✅ 自动更新（推送代码即更新）

---

**现在就去Streamlit Cloud部署吧！** 🚀

访问：https://share.streamlit.io
