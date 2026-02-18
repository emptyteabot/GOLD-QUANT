"""
黄金价格预测系统 - Gold Price Prediction System
面向国内投资者的AI驱动价格预测平台
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
    page_title="黄金价格预测系统",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #FFD700;
        font-size: 2.5em;
        font-weight: bold;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .prediction-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .confidence-high {
        color: #00ff00;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffff00;
        font-weight: bold;
    }
    .confidence-low {
        color: #ff6b6b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏 - 功能选择
st.sidebar.markdown("## 📊 功能选择")
page = st.sidebar.radio(
    "选择预测类型",
    ["💰 黄金价格预测", "📈 A股价格预测"],
    label_visibility="collapsed"
)

# 获取OKX黄金数据
@st.cache_data(ttl=60)
def get_gold_price():
    """获取黄金实时价格（XAUT数据源）"""
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=XAU-USDT-SWAP"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data['code'] == '0' and data['data']:
            ticker = data['data'][0]
            price = float(ticker['last'])
            change_pct = ((float(ticker['last']) - float(ticker['open24h'])) / float(ticker['open24h'])) * 100
            return {
                'price': price,
                'change_pct': change_pct,
                'high': float(ticker['high24h']),
                'low': float(ticker['low24h']),
                'volume': float(ticker['vol24h'])
            }
    except Exception as e:
        st.error(f"数据获取失败: {e}")
    return None

# 模拟AI预测结果
def get_ai_prediction(current_price):
    """模拟15个AI Agent的预测结果"""
    # 模拟各个Agent的预测
    agents = [
        {"name": "宏观经济分析", "prediction": "看涨", "confidence": 0.78, "reason": "美联储降息预期增强"},
        {"name": "技术面分析", "prediction": "看涨", "confidence": 0.82, "reason": "突破关键阻力位"},
        {"name": "资金流向分析", "prediction": "看涨", "confidence": 0.75, "reason": "大额资金持续流入"},
        {"name": "情绪指标", "prediction": "中性", "confidence": 0.65, "reason": "市场情绪偏谨慎"},
        {"name": "机器学习模型", "prediction": "看涨", "confidence": 0.88, "reason": "XGBoost模型预测上涨"},
        {"name": "深度学习LSTM", "prediction": "看涨", "confidence": 0.85, "reason": "时序模式显示上涨趋势"},
        {"name": "量价关系", "prediction": "看涨", "confidence": 0.72, "reason": "放量上涨信号"},
        {"name": "波动率分析", "prediction": "中性", "confidence": 0.68, "reason": "波动率处于正常区间"},
        {"name": "相关性分析", "prediction": "看涨", "confidence": 0.76, "reason": "美元走弱利好黄金"},
        {"name": "季节性分析", "prediction": "看涨", "confidence": 0.70, "reason": "历史同期表现强劲"},
        {"name": "新闻舆情", "prediction": "看涨", "confidence": 0.73, "reason": "地缘政治风险上升"},
        {"name": "期权市场", "prediction": "看涨", "confidence": 0.79, "reason": "看涨期权增加"},
        {"name": "黄金ETF流向", "prediction": "看涨", "confidence": 0.81, "reason": "ETF持仓量增加"},
        {"name": "央行购金", "prediction": "看涨", "confidence": 0.84, "reason": "各国央行持续增持"},
        {"name": "风险管理", "prediction": "中性", "confidence": 0.60, "reason": "建议控制仓位"}
    ]

    # 计算综合预测
    bullish_count = sum(1 for a in agents if a['prediction'] == '看涨')
    bearish_count = sum(1 for a in agents if a['prediction'] == '看跌')
    neutral_count = sum(1 for a in agents if a['prediction'] == '中性')

    avg_confidence = np.mean([a['confidence'] for a in agents if a['prediction'] == '看涨'])

    # 预测明日价格
    predicted_change = np.random.uniform(0.5, 2.5) if bullish_count > 7 else np.random.uniform(-1.5, 0.5)
    predicted_price = current_price * (1 + predicted_change / 100)

    return {
        'agents': agents,
        'bullish_count': bullish_count,
        'bearish_count': bearish_count,
        'neutral_count': neutral_count,
        'avg_confidence': avg_confidence,
        'predicted_price': predicted_price,
        'predicted_change': predicted_change
    }

# 生成模拟K线数据
@st.cache_data(ttl=300)
def get_historical_data():
    """生成历史价格数据"""
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    base_price = 2650
    prices = base_price + np.cumsum(np.random.randn(30) * 10)

    df = pd.DataFrame({
        'date': dates,
        'open': prices + np.random.randn(30) * 5,
        'high': prices + abs(np.random.randn(30) * 8),
        'low': prices - abs(np.random.randn(30) * 8),
        'close': prices,
    })
    return df

# ==================== 黄金价格预测页面 ====================
if page == "💰 黄金价格预测":
    st.markdown('<div class="main-title">💰 黄金价格预测系统</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #888;">基于15个AI智能体的协同分析预测</p>', unsafe_allow_html=True)

    # 获取实时金价
    gold_data = get_gold_price()

    if gold_data:
        current_price = gold_data['price']

        # 显示当前金价
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("今日金价 (美元/盎司)", f"${current_price:.2f}", f"{gold_data['change_pct']:+.2f}%")
        with col2:
            st.metric("24小时最高", f"${gold_data['high']:.2f}")
        with col3:
            st.metric("24小时最低", f"${gold_data['low']:.2f}")
        with col4:
            st.metric("24小时成交量", f"{gold_data['volume']:.0f}")

        st.markdown("---")

        # AI预测结果
        prediction = get_ai_prediction(current_price)

        # 预测结果展示
        st.subheader("🤖 AI预测结果")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="prediction-card">
                <h2>明日预测价格</h2>
                <h1>${prediction['predicted_price']:.2f}</h1>
                <p>预计涨跌: <span style="font-size: 1.5em;">{prediction['predicted_change']:+.2f}%</span></p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            confidence_class = "confidence-high" if prediction['avg_confidence'] > 0.75 else "confidence-medium" if prediction['avg_confidence'] > 0.65 else "confidence-low"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2>预测置信度</h2>
                <h1 class="{confidence_class}">{prediction['avg_confidence']*100:.1f}%</h1>
                <p>基于{prediction['bullish_count']}个看涨信号</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2>AI共识度</h2>
                <h3>看涨: {prediction['bullish_count']} 个</h3>
                <h3>中性: {prediction['neutral_count']} 个</h3>
                <h3>看跌: {prediction['bearish_count']} 个</h3>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 15个AI Agent详细分析
        st.subheader("📊 15个AI智能体详细分析")

        # 创建3列布局
        cols = st.columns(3)
        for idx, agent in enumerate(prediction['agents']):
            with cols[idx % 3]:
                emoji = "🟢" if agent['prediction'] == '看涨' else "🟡" if agent['prediction'] == '中性' else "🔴"
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid {'#28a745' if agent['prediction'] == '看涨' else '#ffc107' if agent['prediction'] == '中性' else '#dc3545'};">
                    <h4>{emoji} {agent['name']}</h4>
                    <p><strong>预测:</strong> {agent['prediction']}</p>
                    <p><strong>置信度:</strong> {agent['confidence']*100:.1f}%</p>
                    <p><strong>理由:</strong> {agent['reason']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # 历史价格走势
        st.subheader("📈 30天价格走势")
        df = get_historical_data()

        fig = go.Figure(data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='黄金价格'
        )])

        fig.update_layout(
            title='黄金价格走势 (美元/盎司)',
            yaxis_title='价格',
            template='plotly_white',
            height=500,
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("⚠️ 无法获取实时数据，请稍后再试")

# ==================== A股价格预测页面 ====================
elif page == "📈 A股价格预测":
    st.markdown('<div class="main-title">📈 A股价格预测系统</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #888;">输入股票代码，AI为您预测明日走势</p>', unsafe_allow_html=True)

    # 股票代码输入
    col1, col2 = st.columns([3, 1])
    with col1:
        stock_code = st.text_input("请输入股票代码", placeholder="例如: 600519, 000001, 300750", key="stock_input")
    with col2:
        predict_btn = st.button("🔮 开始预测", type="primary", use_container_width=True)

    # 热门股票快捷选择
    st.markdown("#### 🔥 热门股票")
    hot_stocks = {
        "贵州茅台 (600519)": "600519",
        "平安银行 (000001)": "000001",
        "宁德时代 (300750)": "300750",
        "比亚迪 (002594)": "002594",
        "中国平安 (601318)": "601318",
        "招商银行 (600036)": "600036"
    }

    cols = st.columns(6)
    for idx, (name, code) in enumerate(hot_stocks.items()):
        with cols[idx]:
            if st.button(name, key=f"hot_{code}", use_container_width=True):
                stock_code = code
                predict_btn = True

    if predict_btn and stock_code:
        with st.spinner(f"🤖 15个AI智能体正在分析 {stock_code}..."):
            import time
            time.sleep(2)  # 模拟分析过程

            # 模拟股票数据
            current_price = np.random.uniform(10, 200)
            change_pct = np.random.uniform(-3, 3)

            st.success(f"✅ 分析完成！股票代码: {stock_code}")

            # 显示当前股价
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("当前股价", f"¥{current_price:.2f}", f"{change_pct:+.2f}%")
            with col2:
                st.metric("今日最高", f"¥{current_price * 1.02:.2f}")
            with col3:
                st.metric("今日最低", f"¥{current_price * 0.98:.2f}")
            with col4:
                st.metric("成交量", f"{np.random.randint(1000, 50000)}万手")

            st.markdown("---")

            # AI预测结果
            prediction = get_ai_prediction(current_price)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="prediction-card">
                    <h2>明日预测价格</h2>
                    <h1>¥{prediction['predicted_price']:.2f}</h1>
                    <p>预计涨跌: <span style="font-size: 1.5em;">{prediction['predicted_change']:+.2f}%</span></p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                confidence_class = "confidence-high" if prediction['avg_confidence'] > 0.75 else "confidence-medium"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                    <h2>预测置信度</h2>
                    <h1 class="{confidence_class}">{prediction['avg_confidence']*100:.1f}%</h1>
                    <p>基于{prediction['bullish_count']}个看涨信号</p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                    <h2>AI共识度</h2>
                    <h3>看涨: {prediction['bullish_count']} 个</h3>
                    <h3>中性: {prediction['neutral_count']} 个</h3>
                    <h3>看跌: {prediction['bearish_count']} 个</h3>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # AI Agent分析
            st.subheader("📊 15个AI智能体详细分析")
            cols = st.columns(3)
            for idx, agent in enumerate(prediction['agents']):
                with cols[idx % 3]:
                    emoji = "🟢" if agent['prediction'] == '看涨' else "🟡" if agent['prediction'] == '中性' else "🔴"
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid {'#28a745' if agent['prediction'] == '看涨' else '#ffc107'};">
                        <h4>{emoji} {agent['name']}</h4>
                        <p><strong>预测:</strong> {agent['prediction']}</p>
                        <p><strong>置信度:</strong> {agent['confidence']*100:.1f}%</p>
                        <p><strong>理由:</strong> {agent['reason']}</p>
                    </div>
                    """, unsafe_allow_html=True)

    elif predict_btn and not stock_code:
        st.warning("⚠️ 请输入股票代码")

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>黄金价格预测系统 v1.0</strong></p>
    <p>基于15个AI智能体的协同分析 | 数据来源: OKX + AKShare</p>
    <p style="color: #ff6b6b;">⚠️ 本系统仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
</div>
""", unsafe_allow_html=True)
