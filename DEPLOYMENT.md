# 黄金价格预测系统 - 部署指南

## 快速部署到 Streamlit Cloud

### 部署步骤

1. 访问 https://share.streamlit.io/
2. 登录GitHub账号
3. 点击 "New app"
4. 填写:
   - Repository: emptyteabot/GOLD-QUANT
   - Branch: main
   - Main file: app_gold_prediction.py
5. 点击 Deploy

### 功能测试

- 黄金预测: 默认页面,查看实时金价和AI预测
- A股预测: 侧边栏切换,输入股票代码(如600519)

### 本地开发

```bash
git clone https://github.com/emptyteabot/GOLD-QUANT.git
cd GOLD-QUANT
pip install -r requirements.txt
streamlit run app_gold_prediction.py
```

访问 http://localhost:8501

---

**版本**: v2.0 | **更新**: 2026-02-18
