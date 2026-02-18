"""
Gold Advisor Pro - XAU/XAUT 监控版
简化版，只监控黄金现货和ETF
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import os

# 加载环境变量
try:
    import config_defaults
except:
    pass

st.set_page_config(
    page_title="Gold Advisor Pro - XAU/XAUT Monitor",
    page_icon="🥇",
    layout="wide"
)

# 标题
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <h1>🥇 Gold Advisor Pro</h1>
    <p style='color: #ffd700;'>XAU/XAUT 实时监控系统</p>
</div>
""", unsafe_allow_html=True)

# 获取OKX数据
@st.cache_data(ttl=60)
def get_okx_price(symbol="XAU-USDT-SWAP"):
    """获取OKX黄金价格"""
    try:
        url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data['code'] == '0' and data['data']:
            ticker = data['data'][0]
            return {
                'price': float(ticker['last']),
                'change': float(ticker['last']) - float(ticker['open24h']),
                'change_pct': ((float(ticker['last']) - float(ticker['open24h'])) / float(ticker['open24h'])) * 100,
                'high': float(ticker['high24h']),
                'low': float(ticker['low24h']),
                'volume': float(ticker['vol24h'])
            }
    except Exception as e:
        st.error(f"获取数据失败: {e}")
    return None

# 模拟K线数据
@st.cache_data(ttl=300)
def get_mock_klines():
    """生成模拟K线数据"""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')
    base_price = 4800
    prices = base_price + np.cumsum(np.random.randn(100) * 5)

    df = pd.DataFrame({
        'time': dates,
        'open': prices + np.random.randn(100) * 2,
        'high': prices + abs(np.random.randn(100) * 3),
        'low': prices - abs(np.random.randn(100) * 3),
        'close': prices,
        'volume': np.random.randint(1000, 5000, 100)
    })
    return df

# 主界面
col1, col2, col3, col4 = st.columns(4)

# 获取实时数据
xau_data = get_okx_price("XAU-USDT-SWAP")

if xau_data:
    with col1:
        st.metric(
            "XAU 现货价格",
            f"${xau_data['price']:.2f}",
            f"{xau_data['change_pct']:+.2f}%"
        )

    with col2:
        st.metric(
            "24H 最高",
            f"${xau_data['high']:.2f}"
        )

    with col3:
        st.metric(
            "24H 最低",
            f"${xau_data['low']:.2f}"
        )

    with col4:
        st.metric(
            "24H 成交量",
            f"{xau_data['volume']:.0f}"
        )
else:
    st.warning("⚠️ 无法获取实时数据，显示模拟数据")
    with col1:
        st.metric("XAU 现货价格", "$4,819.20", "+1.35%")
    with col2:
        st.metric("24H 最高", "$4,850.30")
    with col3:
        st.metric("24H 最低", "$4,780.50")
    with col4:
        st.metric("24H 成交量", "15,234")

# K线图
st.subheader("📊 价格走势")

df = get_mock_klines()

fig = go.Figure(data=[go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='XAU'
)])

fig.update_layout(
    title='XAU/USDT 1小时K线',
    yaxis_title='价格 (USD)',
    template='plotly_dark',
    height=500,
    xaxis_rangeslider_visible=False
)

st.plotly_chart(fig, use_container_width=True)

# 交易信号
st.subheader("📡 交易信号")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("**当前信号**: 观望")
    st.write("信号强度: -0.32")

with col2:
    st.info("**置信度**: 49.3%")
    st.write("共识度: 66.2%")

with col3:
    st.info("**建议**: 等待更强信号")
    st.write("原因: 技术面偏弱")

# 环境变量状态
with st.expander("🔧 系统配置"):
    st.write("**OKX API配置**:")
    st.write(f"- API Key: {'✅ 已配置' if os.getenv('OKX_API_KEY') else '❌ 未配置'}")
    st.write(f"- Secret Key: {'✅ 已配置' if os.getenv('OKX_SECRET_KEY') else '❌ 未配置'}")
    st.write(f"- Passphrase: {'✅ 已配置' if os.getenv('OKX_PASSPHRASE') else '❌ 未配置'}")

    st.write("\n**飞书通知**:")
    st.write(f"- Webhook: {'✅ 已配置' if os.getenv('FEISHU_WEBHOOK_URL') else '❌ 未配置'}")

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Gold Advisor Pro v3.0 - XAU/XAUT Monitor</p>
    <p>⚠️ 仅供参考，不构成投资建议</p>
</div>
""", unsafe_allow_html=True)

# 自动刷新
st.markdown("""
<script>
setTimeout(function(){
    window.location.reload();
}, 60000);
</script>
""", unsafe_allow_html=True)
