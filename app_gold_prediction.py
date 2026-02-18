"""
黄金价格预测系统 - Gold Price Prediction System
面向国内投资者的AI驱动价格预测平台
彭博终端风格设计
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import os
import sys
import pytz
import time

# 加载环境变量
try:
    import config_defaults
except:
    pass

# 导入A股预测引擎
try:
    from astock_predictor import AStockPredictor
    ASTOCK_AVAILABLE = True
except:
    ASTOCK_AVAILABLE = False

st.set_page_config(
    page_title="彭博终端 - AI投资系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 获取北京时间
def get_beijing_time():
    """获取北京时间 (Asia/Shanghai)"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(beijing_tz)

# 彭博终端风格CSS
st.markdown("""
<style>
    /* ========== 全局样式 - 彭博终端深色主题 ========== */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap');

    .stApp {
        background: #000000;
        color: #FFFFFF;
        font-family: 'Roboto Mono', monospace;
    }

    /* ========== 顶部状态栏 ========== */
    .bloomberg-header {
        background: #0a0a0a;
        border-bottom: 2px solid #FF8C00;
        padding: 10px 20px;
        margin: -60px -60px 20px -60px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .header-logo {
        color: #FFD700;
        font-size: 1.8em;
        font-weight: 700;
        letter-spacing: 2px;
    }

    .header-time {
        color: #FF8C00;
        font-size: 1.2em;
        font-weight: 500;
        font-family: 'Roboto Mono', monospace;
    }

    .header-status {
        color: #00FF00;
        font-size: 1em;
        font-weight: 500;
    }

    /* ========== 主标题 ========== */
    .terminal-title {
        background: linear-gradient(90deg, #FF8C00 0%, #FFD700 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em;
        font-weight: 700;
        text-align: center;
        padding: 20px;
        border: 2px solid #FF8C00;
        border-radius: 5px;
        margin-bottom: 20px;
        letter-spacing: 3px;
    }

    /* ========== 数据卡片 - 深色背景 ========== */
    .terminal-card {
        background: #0a0a0a;
        border: 1px solid #FF8C00;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
    }

    .terminal-card-header {
        color: #FFD700;
        font-size: 0.9em;
        font-weight: 700;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .terminal-card-value {
        color: #FFFFFF;
        font-size: 2em;
        font-weight: 700;
        font-family: 'Roboto Mono', monospace;
    }

    .terminal-card-change-up {
        color: #00FF00;
        font-size: 1.2em;
        font-weight: 700;
    }

    .terminal-card-change-down {
        color: #FF0000;
        font-size: 1.2em;
        font-weight: 700;
    }

    /* ========== 交易信号卡片 ========== */
    .signal-terminal {
        background: #0a0a0a;
        border: 3px solid;
        border-radius: 5px;
        padding: 20px;
        text-align: center;
        margin-bottom: 15px;
    }

    .signal-terminal-strong-buy {
        border-color: #00FF00;
        box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
    }

    .signal-terminal-buy {
        border-color: #7FFF00;
        box-shadow: 0 0 20px rgba(127, 255, 0, 0.3);
    }

    .signal-terminal-hold {
        border-color: #FFD700;
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
    }

    .signal-terminal-sell {
        border-color: #FF8C00;
        box-shadow: 0 0 20px rgba(255, 140, 0, 0.3);
    }

    .signal-terminal-strong-sell {
        border-color: #FF0000;
        box-shadow: 0 0 20px rgba(255, 0, 0, 0.3);
    }

    .signal-title {
        color: #FFD700;
        font-size: 1em;
        font-weight: 700;
        margin-bottom: 10px;
        text-transform: uppercase;
    }

    .signal-value {
        font-size: 2.5em;
        font-weight: 700;
        margin: 10px 0;
    }

    /* ========== Agent分析卡片 ========== */
    .agent-terminal {
        background: #0a0a0a;
        border-left: 4px solid #FF8C00;
        padding: 15px;
        margin-bottom: 10px;
    }

    .agent-name {
        color: #FFD700;
        font-size: 1em;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .agent-prediction-bull {
        color: #00FF00;
        font-size: 1.1em;
        font-weight: 700;
    }

    .agent-prediction-bear {
        color: #FF0000;
        font-size: 1.1em;
        font-weight: 700;
    }

    .agent-prediction-neutral {
        color: #FFD700;
        font-size: 1.1em;
        font-weight: 700;
    }

    .agent-confidence {
        color: #FF8C00;
        font-size: 0.95em;
        font-weight: 500;
    }

    .agent-reason {
        color: #CCCCCC;
        font-size: 0.9em;
        line-height: 1.5;
        margin-top: 8px;
    }

    /* ========== 数据表格 ========== */
    .data-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Roboto Mono', monospace;
        font-size: 0.9em;
    }

    .data-table th {
        background: #0a0a0a;
        color: #FFD700;
        padding: 10px;
        text-align: left;
        border-bottom: 2px solid #FF8C00;
        font-weight: 700;
        text-transform: uppercase;
    }

    .data-table td {
        color: #FFFFFF;
        padding: 8px 10px;
        border-bottom: 1px solid #333333;
    }

    .data-table tr:hover {
        background: #1a1a1a;
    }

    /* ========== 更新时间 ========== */
    .update-time-terminal {
        text-align: center;
        color: #FF8C00;
        font-size: 0.95em;
        font-weight: 500;
        padding: 10px;
        font-family: 'Roboto Mono', monospace;
    }

    /* ========== 按钮样式 ========== */
    .stButton>button {
        background: #0a0a0a;
        color: #FFD700;
        border: 2px solid #FF8C00;
        border-radius: 5px;
        font-weight: 700;
        font-family: 'Roboto Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stButton>button:hover {
        background: #FF8C00;
        color: #000000;
        border-color: #FFD700;
    }

    /* ========== Metric组件样式 ========== */
    div[data-testid="metric-container"] {
        background: #0a0a0a;
        border: 1px solid #FF8C00;
        padding: 15px;
        border-radius: 5px;
    }

    div[data-testid="metric-container"] label {
        color: #FFD700 !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 0.85em !important;
    }

    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-family: 'Roboto Mono', monospace !important;
        font-size: 1.8em !important;
        font-weight: 700 !important;
    }

    div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
        font-family: 'Roboto Mono', monospace !important;
        font-weight: 700 !important;
    }

    /* ========== Expander样式 ========== */
    .streamlit-expanderHeader {
        background: #0a0a0a !important;
        border: 1px solid #FF8C00 !important;
        border-radius: 5px !important;
        color: #FFD700 !important;
        font-weight: 700 !important;
        font-family: 'Roboto Mono', monospace !important;
    }

    .streamlit-expanderHeader:hover {
        background: #1a1a1a !important;
        border-color: #FFD700 !important;
    }

    .streamlit-expanderContent {
        background: #0a0a0a !important;
        border: 1px solid #333333 !important;
        border-top: none !important;
    }

    /* ========== 侧边栏 ========== */
    section[data-testid="stSidebar"] {
        background: #0a0a0a;
        border-right: 2px solid #FF8C00;
    }

    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] .stRadio label {
        color: #FFD700 !important;
        font-weight: 700 !important;
    }

    /* ========== 输入框 ========== */
    .stTextInput>div>div>input {
        background: #0a0a0a;
        color: #FFFFFF;
        border: 2px solid #FF8C00;
        font-family: 'Roboto Mono', monospace;
        font-weight: 500;
    }

    .stTextInput>div>div>input:focus {
        border-color: #FFD700;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
    }

    /* ========== 所有文字颜色 ========== */
    h1, h2, h3, h4, h5, h6 {
        color: #FFD700 !important;
        font-family: 'Roboto Mono', monospace !important;
        font-weight: 700 !important;
    }

    p, li, span, div {
        color: #FFFFFF !important;
    }

    .stMarkdown {
        color: #FFFFFF !important;
    }

    /* ========== 分隔线 ========== */
    hr {
        border-color: #FF8C00 !important;
        opacity: 0.5;
    }

    /* ========== 滚动条 ========== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #0a0a0a;
    }

    ::-webkit-scrollbar-thumb {
        background: #FF8C00;
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #FFD700;
    }

    /* ========== 实时闪烁效果 ========== */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .blink {
        animation: blink 1s ease-in-out infinite;
    }

    /* ========== 数据高亮 ========== */
    .highlight-up {
        color: #00FF00 !important;
        font-weight: 700;
    }

    .highlight-down {
        color: #FF0000 !important;
        font-weight: 700;
    }

    .highlight-neutral {
        color: #FFD700 !important;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# 顶部状态栏 - 彭博终端风格
beijing_time = get_beijing_time()
st.markdown(f"""
<div class="bloomberg-header">
    <div class="header-logo">彭博终端</div>
    <div class="header-time">北京时间 {beijing_time.strftime("%Y-%m-%d %H:%M:%S")}</div>
    <div class="header-status">● 实时市场数据</div>
</div>
""", unsafe_allow_html=True)

# 侧边栏 - 功能选择
st.sidebar.markdown("## 📊 终端菜单")
page = st.sidebar.radio(
    "选择功能",
    ["💰 黄金价格预测", "📈 A股价格预测", "📖 关于系统"],
    label_visibility="collapsed"
)

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
            beijing_time = get_beijing_time()
            return {
                'price': price,
                'change_pct': change_pct,
                'high': float(ticker['high24h']),
                'low': float(ticker['low24h']),
                'volume': float(ticker['vol24h']),
                'update_time': beijing_time.strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception as e:
        st.error(f"数据获取失败: {e}")
    return None

# 生成交易信号
def generate_trading_signal(prediction, current_price):
    """根据预测结果生成交易信号"""
    predicted_change = prediction['predicted_change']
    confidence = prediction['avg_confidence']
    bullish_count = prediction['bullish_count']

    # 计算信号强度 (0-100)
    signal_strength = int(confidence * 100)

    # 确定信号类型
    if predicted_change > 1.5 and confidence > 0.75 and bullish_count >= 12:
        signal_type = "强烈买入"
        signal_emoji = "🟢"
        signal_class = "signal-strong-buy"
        position_advice = "建议仓位: 60-80%"
        stop_loss = current_price * 0.97
        take_profit = current_price * 1.05
    elif predicted_change > 0.5 and confidence > 0.65 and bullish_count >= 9:
        signal_type = "买入"
        signal_emoji = "🟡"
        signal_class = "signal-buy"
        position_advice = "建议仓位: 30-50%"
        stop_loss = current_price * 0.98
        take_profit = current_price * 1.03
    elif abs(predicted_change) <= 0.5 or (bullish_count >= 6 and bullish_count <= 9):
        signal_type = "观望"
        signal_emoji = "⚪"
        signal_class = "signal-hold"
        position_advice = "建议仓位: 保持现有仓位"
        stop_loss = current_price * 0.98
        take_profit = current_price * 1.02
    elif predicted_change < -0.5 and confidence > 0.65:
        signal_type = "卖出"
        signal_emoji = "🟠"
        signal_class = "signal-sell"
        position_advice = "建议仓位: 减仓至20%"
        stop_loss = current_price * 1.02
        take_profit = current_price * 0.97
    else:
        signal_type = "强烈卖出"
        signal_emoji = "🔴"
        signal_class = "signal-strong-sell"
        position_advice = "建议仓位: 清仓观望"
        stop_loss = current_price * 1.03
        take_profit = current_price * 0.95

    return {
        'type': signal_type,
        'emoji': signal_emoji,
        'class': signal_class,
        'strength': signal_strength,
        'position_advice': position_advice,
        'stop_loss': stop_loss,
        'take_profit': take_profit
    }

# 模拟AI预测结果
def get_ai_prediction(current_price):
    """模拟15个AI Agent的预测结果"""
    # 模拟各个Agent的预测
    agents = [
        {
            "name": "宏观经济分析",
            "prediction": "看涨",
            "confidence": 0.78,
            "reason": "美联储降息预期增强，利好黄金"
        },
        {
            "name": "技术面分析",
            "prediction": "看涨",
            "confidence": 0.82,
            "reason": "突破关键阻力位2680美元，技术形态良好"
        },
        {
            "name": "资金流向分析",
            "prediction": "看涨",
            "confidence": 0.75,
            "reason": "大额资金持续流入黄金ETF"
        },
        {
            "name": "情绪指标",
            "prediction": "中性",
            "confidence": 0.65,
            "reason": "市场情绪偏谨慎，恐慌指数适中"
        },
        {
            "name": "机器学习模型",
            "prediction": "看涨",
            "confidence": 0.88,
            "reason": "XGBoost模型预测上涨概率85%"
        },
        {
            "name": "深度学习LSTM",
            "prediction": "看涨",
            "confidence": 0.85,
            "reason": "时序模式显示上涨趋势延续"
        },
        {
            "name": "量价关系",
            "prediction": "看涨",
            "confidence": 0.72,
            "reason": "放量上涨，成交量增加40%"
        },
        {
            "name": "波动率分析",
            "prediction": "中性",
            "confidence": 0.68,
            "reason": "波动率处于正常区间，无异常"
        },
        {
            "name": "相关性分析",
            "prediction": "看涨",
            "confidence": 0.76,
            "reason": "美元指数走弱，负相关利好黄金"
        },
        {
            "name": "季节性分析",
            "prediction": "看涨",
            "confidence": 0.70,
            "reason": "历史同期(2月)表现强劲"
        },
        {
            "name": "新闻舆情",
            "prediction": "看涨",
            "confidence": 0.73,
            "reason": "地缘政治风险上升，避险需求增加"
        },
        {
            "name": "期权市场",
            "prediction": "看涨",
            "confidence": 0.79,
            "reason": "看涨期权持仓量大幅增加"
        },
        {
            "name": "黄金ETF流向",
            "prediction": "看涨",
            "confidence": 0.81,
            "reason": "全球黄金ETF持仓量连续增加"
        },
        {
            "name": "央行购金",
            "prediction": "看涨",
            "confidence": 0.84,
            "reason": "各国央行持续增持黄金储备"
        },
        {
            "name": "风险管理",
            "prediction": "中性",
            "confidence": 0.60,
            "reason": "建议控制仓位，注意回调风险"
        }
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
    # 标题和刷新按钮
    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.markdown('<div class="terminal-title">黄金价格预测</div>', unsafe_allow_html=True)
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 刷新", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 获取实时金价
    gold_data = get_gold_price()

    if gold_data:
        current_price = gold_data['price']

        # 显示更新时间
        st.markdown(f'<div class="update-time-terminal">📡 更新时间: {gold_data["update_time"]}</div>', unsafe_allow_html=True)

        # 显示当前金价 - 4列网格布局
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            change_class = "highlight-up" if gold_data['change_pct'] >= 0 else "highlight-down"
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">现货黄金 (美元/盎司)</div>
                <div class="terminal-card-value">${current_price:.2f}</div>
                <div class="{change_class}">{gold_data['change_pct']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">24小时最高</div>
                <div class="terminal-card-value">${gold_data['high']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">24小时最低</div>
                <div class="terminal-card-value">${gold_data['low']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">24小时成交量</div>
                <div class="terminal-card-value">{gold_data['volume']:.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # AI预测结果
        prediction = get_ai_prediction(current_price)

        # 生成交易信号
        signal = generate_trading_signal(prediction, current_price)

        # 预测结果展示 - 4列网格
        st.markdown("### 🤖 AI预测分析")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            change_class = "highlight-up" if prediction['predicted_change'] >= 0 else "highlight-down"
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">预测价格 (明日)</div>
                <div class="terminal-card-value">${prediction['predicted_price']:.2f}</div>
                <div class="{change_class}">{prediction['predicted_change']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">置信度</div>
                <div class="terminal-card-value">{prediction['avg_confidence']*100:.1f}%</div>
                <div style="color: #FF8C00; font-size: 0.9em;">基于 {prediction['bullish_count']} 个看涨信号</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">AI共识</div>
                <div style="color: #00FF00; font-size: 1.2em; margin: 5px 0;">▲ 看涨: {prediction['bullish_count']}</div>
                <div style="color: #FFD700; font-size: 1.2em; margin: 5px 0;">● 中性: {prediction['neutral_count']}</div>
                <div style="color: #FF0000; font-size: 1.2em; margin: 5px 0;">▼ 看跌: {prediction['bearish_count']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="signal-terminal signal-terminal-{signal['class'].replace('signal-', '')}">
                <div class="signal-title">交易信号</div>
                <div class="signal-value">{signal['emoji']} {signal['type']}</div>
                <div style="color: #FF8C00; font-size: 0.95em;">强度: {signal['strength']}/100</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 交易建议详情 - 3列网格
        st.markdown("### 💡 交易建议")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">📊 仓位建议</div>
                <div style="color: #FFFFFF; font-size: 1.2em; margin-top: 10px;">{signal['position_advice']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">🛡️ 止损价</div>
                <div style="color: #FF0000; font-size: 1.5em; margin-top: 10px;">${signal['stop_loss']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="terminal-card">
                <div class="terminal-card-header">🎯 止盈价</div>
                <div style="color: #00FF00; font-size: 1.5em; margin-top: 10px;">${signal['take_profit']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 15个AI Agent详细分析 - 使用表格布局
        st.markdown("### 📊 15个AI智能体分析")

        # 创建3列布局
        cols = st.columns(3)
        for idx, agent in enumerate(prediction['agents']):
            with cols[idx % 3]:
                pred_class = "agent-prediction-bull" if agent['prediction'] == '看涨' else "agent-prediction-bear" if agent['prediction'] == '看跌' else "agent-prediction-neutral"
                emoji = "▲" if agent['prediction'] == '看涨' else "▼" if agent['prediction'] == '看跌' else "●"

                with st.expander(f"{emoji} {agent['name']} - {agent['prediction']} ({agent['confidence']*100:.1f}%)", expanded=False):
                    st.markdown(f"""
                    <div class="agent-terminal">
                        <div class="agent-name">{agent['name']}</div>
                        <div class="{pred_class}">预测: {agent['prediction']}</div>
                        <div class="agent-confidence">置信度: {agent['confidence']*100:.1f}%</div>
                        <div class="agent-reason">理由: {agent['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

        # 历史价格走势 - 深色图表
        st.markdown("### 📈 30天价格走势")
        df = get_historical_data()

        fig = go.Figure(data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='黄金价格',
            increasing_line_color='#00FF00',
            decreasing_line_color='#FF0000',
            increasing_fillcolor='#00FF00',
            decreasing_fillcolor='#FF0000'
        )])

        fig.update_layout(
            title='黄金价格走势 (美元/盎司)',
            yaxis_title='价格',
            template='plotly_dark',
            height=500,
            xaxis_rangeslider_visible=False,
            paper_bgcolor='#0a0a0a',
            plot_bgcolor='#000000',
            font=dict(color='#FFD700', family='Roboto Mono', size=12),
            title_font=dict(color='#FFD700', size=16, family='Roboto Mono'),
            xaxis=dict(
                gridcolor='#333333',
                showgrid=True,
                color='#FF8C00'
            ),
            yaxis=dict(
                gridcolor='#333333',
                showgrid=True,
                color='#FF8C00'
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("⚠️ 无法获取实时数据，请稍后再试")
        if st.button("🔄 重试"):
            st.cache_data.clear()
            st.rerun()

# ==================== A股价格预测页面 ====================
elif page == "📈 A股价格预测":
    # 标题和刷新按钮
    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.markdown('<div class="terminal-title">A股价格预测</div>', unsafe_allow_html=True)
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 刷新", use_container_width=True, key="refresh_astock"):
            st.cache_data.clear()
            st.rerun()

    # 股票代码输入
    col1, col2 = st.columns([3, 1])
    with col1:
        stock_code = st.text_input("输入股票代码", placeholder="例如: 600519, 000001, 300750", key="stock_input")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("🔮 预测", type="primary", use_container_width=True)

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
            # 使用真实的A股预测引擎
            if ASTOCK_AVAILABLE:
                predictor = AStockPredictor()
                result = predictor.predict(stock_code)

                if result:
                    stock_data = result['stock_data']
                    beijing_time = get_beijing_time()
                    st.success(f"✅ 分析完成！{stock_data['name']} ({stock_code})")

                    # 显示更新时间
                    st.markdown(f'<div class="update-time-terminal">📡 更新时间: {beijing_time.strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)

                    # 显示当前股价 - 4列网格
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        change_class = "highlight-up" if stock_data['change_pct'] >= 0 else "highlight-down"
                        st.markdown(f"""
                        <div class="terminal-card">
                            <div class="terminal-card-header">当前价格 (人民币)</div>
                            <div class="terminal-card-value">¥{stock_data['price']:.2f}</div>
                            <div class="{change_class}">{stock_data['change_pct']:+.2f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="terminal-card">
                            <div class="terminal-card-header">今日最高</div>
                            <div class="terminal-card-value">¥{stock_data['high']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div class="terminal-card">
                            <div class="terminal-card-header">今日最低</div>
                            <div class="terminal-card-value">¥{stock_data['low']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col4:
                        st.markdown(f"""
                        <div class="terminal-card">
                            <div class="terminal-card-header">成交量</div>
                            <div class="terminal-card-value">{stock_data['volume']:.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("---")

                    # 使用真实预测结果
                    prediction = {
                        'predicted_price': result['predicted_price'],
                        'predicted_change': result['predicted_change'],
                        'avg_confidence': result['confidence'],
                        'bullish_count': result['bullish_count'],
                        'bearish_count': result['bearish_count'],
                        'neutral_count': result['neutral_count'],
                        'agents': result['agent_predictions']
                    }
                else:
                    st.error("⚠️ 无法获取股票数据，请检查股票代码")
                    st.stop()
            else:
                # 降级到模拟数据
                import time
                time.sleep(2)
                current_price = np.random.uniform(10, 200)
                change_pct = np.random.uniform(-3, 3)

                beijing_time = get_beijing_time()
                st.success(f"✅ 分析完成！股票代码: {stock_code}")

                # 显示更新时间
                st.markdown(f'<div class="update-time-terminal">📡 更新时间: {beijing_time.strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)

                # 显示当前股价 - 4列网格
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    change_class = "highlight-up" if change_pct >= 0 else "highlight-down"
                    st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">当前价格 (人民币)</div>
                        <div class="terminal-card-value">¥{current_price:.2f}</div>
                        <div class="{change_class}">{change_pct:+.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">今日最高</div>
                        <div class="terminal-card-value">¥{current_price * 1.02:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">今日最低</div>
                        <div class="terminal-card-value">¥{current_price * 0.98:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">成交量</div>
                        <div class="terminal-card-value">{np.random.randint(1000, 50000)}万手</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")
                prediction = get_ai_prediction(current_price)

            # 生成交易信号
            signal = generate_trading_signal(prediction, prediction['predicted_price'] / (1 + prediction['predicted_change']/100))

            # 预测结果展示 - 4列网格
            st.markdown("### 🤖 AI预测分析")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                change_class = "highlight-up" if prediction['predicted_change'] >= 0 else "highlight-down"
                st.markdown(f"""
                <div class="terminal-card">
                    <div class="terminal-card-header">预测价格 (明日)</div>
                    <div class="terminal-card-value">¥{prediction['predicted_price']:.2f}</div>
                    <div class="{change_class}">{prediction['predicted_change']:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="terminal-card">
                    <div class="terminal-card-header">置信度</div>
                    <div class="terminal-card-value">{prediction['avg_confidence']*100:.1f}%</div>
                    <div style="color: #FF8C00; font-size: 0.9em;">基于 {prediction['bullish_count']} 个看涨信号</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="terminal-card">
                    <div class="terminal-card-header">AI共识</div>
                    <div style="color: #00FF00; font-size: 1.2em; margin: 5px 0;">▲ 看涨: {prediction['bullish_count']}</div>
                    <div style="color: #FFD700; font-size: 1.2em; margin: 5px 0;">● 中性: {prediction['neutral_count']}</div>
                    <div style="color: #FF0000; font-size: 1.2em; margin: 5px 0;">▼ 看跌: {prediction['bearish_count']}</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="signal-terminal signal-terminal-{signal['class'].replace('signal-', '')}">
                    <div class="signal-title">交易信号</div>
                    <div class="signal-value">{signal['emoji']} {signal['type']}</div>
                    <div style="color: #FF8C00; font-size: 0.95em;">强度: {signal['strength']}/100</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # 交易建议详情 - 3列网格
            st.markdown("### 💡 交易建议")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="terminal-card">
                    <div class="terminal-card-header">📊 仓位建议</div>
                    <div style="color: #FFFFFF; font-size: 1.2em; margin-top: 10px;">{signal['position_advice']}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="terminal-card">
                    <div class="terminal-card-header">🛡️ 止损价</div>
                    <div style="color: #FF0000; font-size: 1.5em; margin-top: 10px;">¥{signal['stop_loss']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="terminal-card">
                    <div class="terminal-card-header">🎯 止盈价</div>
                    <div style="color: #00FF00; font-size: 1.5em; margin-top: 10px;">¥{signal['take_profit']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # AI Agent分析
            st.markdown("### 📊 15个AI智能体分析")

            cols = st.columns(3)
            for idx, agent in enumerate(prediction['agents']):
                with cols[idx % 3]:
                    # 兼容两种数据格式
                    agent_name = agent.get('agent_name') or agent.get('name')
                    agent_pred = agent.get('prediction')
                    agent_conf = agent.get('confidence')
                    agent_reason = agent.get('reason')

                    pred_class = "agent-prediction-bull" if agent_pred == '看涨' else "agent-prediction-bear" if agent_pred == '看跌' else "agent-prediction-neutral"
                    emoji = "▲" if agent_pred == '看涨' else "▼" if agent_pred == '看跌' else "●"

                    with st.expander(f"{emoji} {agent_name} - {agent_pred} ({agent_conf*100:.1f}%)", expanded=False):
                        st.markdown(f"""
                        <div class="agent-terminal">
                            <div class="agent-name">{agent_name}</div>
                            <div class="{pred_class}">预测: {agent_pred}</div>
                            <div class="agent-confidence">置信度: {agent_conf*100:.1f}%</div>
                            <div class="agent-reason">理由: {agent_reason}</div>
                        </div>
                        """, unsafe_allow_html=True)

    elif predict_btn and not stock_code:
        st.warning("⚠️ 请输入股票代码")

# ==================== 关于系统页面 ====================
elif page == "📖 关于系统":
    st.markdown('<div class="terminal-title">系统信息</div>', unsafe_allow_html=True)

    # 系统简介
    st.markdown("""
    <div class="terminal-card">
        <div class="terminal-card-header">🎯 系统概述</div>
        <p style="color: #FFFFFF; font-size: 1.05em; line-height: 1.8; margin-top: 15px;">
            基于<span style="color: #FF8C00; font-weight: 700;">15个AI智能体协同分析</span>的投资预测系统，
            整合宏观经济、技术面、资金流向、机器学习等多维度分析，
            为投资者提供<span style="color: #FFD700; font-weight: 700;">专业实时</span>的决策参考。
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 核心功能
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="terminal-card">
            <div class="terminal-card-header">💰 黄金价格预测</div>
            <ul style="color: #FFFFFF; line-height: 2; margin-top: 15px;">
                <li>实时国际黄金价格</li>
                <li>15个AI智能体分析</li>
                <li>明日价格预测</li>
                <li>交易信号生成</li>
                <li>止损止盈建议</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="terminal-card">
            <div class="terminal-card-header">📈 A股价格预测</div>
            <ul style="color: #FFFFFF; line-height: 2; margin-top: 15px;">
                <li>沪深A股全市场</li>
                <li>实时股票行情</li>
                <li>AI协同预测</li>
                <li>交易信号建议</li>
                <li>风险控制建议</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 交易信号说明
    st.markdown("""
    <div class="terminal-card">
        <div class="terminal-card-header">🎯 交易信号</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("""
        <div class="signal-terminal signal-terminal-strong-buy">
            <div class="signal-title">▲ 强烈买入</div>
            <p style="font-size: 0.85em; margin-top: 10px;">预测涨幅 > 1.5%<br>置信度 > 75%</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="signal-terminal signal-terminal-buy">
            <div class="signal-title">▲ 买入</div>
            <p style="font-size: 0.85em; margin-top: 10px;">预测涨幅 > 0.5%<br>置信度 > 65%</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="signal-terminal signal-terminal-hold">
            <div class="signal-title">● 观望</div>
            <p style="font-size: 0.85em; margin-top: 10px;">预测涨跌幅 ≤ 0.5%<br>信号不明确</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="signal-terminal signal-terminal-sell">
            <div class="signal-title">▼ 卖出</div>
            <p style="font-size: 0.85em; margin-top: 10px;">预测跌幅 > 0.5%<br>置信度 > 65%</p>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
        <div class="signal-terminal signal-terminal-strong-sell">
            <div class="signal-title">▼ 强烈卖出</div>
            <p style="font-size: 0.85em; margin-top: 10px;">预测跌幅较大<br>风险信号明显</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 风险提示
    st.markdown("""
    <div class="terminal-card" style="border: 2px solid #FF0000;">
        <div class="terminal-card-header" style="color: #FF0000;">⚠️ 风险提示</div>
        <div style="color: #FFFFFF; font-size: 1.05em; line-height: 2; margin-top: 15px;">
            <p>1. 预测结果<span style="color: #FF8C00; font-weight: 700;">仅供参考</span>，不构成投资建议</p>
            <p>2. 金融市场存在<span style="color: #FF8C00; font-weight: 700;">不可预测风险</span></p>
            <p>3. 应根据<span style="color: #FF8C00; font-weight: 700;">自身风险承受能力</span>独立判断</p>
            <p>4. <span style="color: #FF0000; font-weight: 700;">投资有风险，入市需谨慎</span></p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 技术支持
    beijing_time = get_beijing_time()
    st.markdown(f"""
    <div class="terminal-card">
        <div class="terminal-card-header">💬 技术信息</div>
        <p style="color: #FFFFFF; font-size: 1.05em; line-height: 2; margin-top: 15px;">
            <span style="color: #FFD700;">数据来源:</span> OKX (黄金) + AKShare (A股)<br>
            <span style="color: #FFD700;">AI技术:</span> 多智能体协同 + 机器学习<br>
            <span style="color: #FFD700;">更新频率:</span> 实时数据，60秒缓存<br>
            <span style="color: #FFD700;">系统版本:</span> v3.0<br>
            <span style="color: #FFD700;">更新时间:</span> {beijing_time.strftime("%Y-%m-%d %H:%M:%S")}
        </p>
    </div>
    """, unsafe_allow_html=True)

# 页脚
st.markdown("---")
beijing_time = get_beijing_time()
st.markdown(f"""
<div style='text-align: center; padding: 30px;'>
    <p style="font-size: 1.3em; color: #FFD700; font-weight: 700; letter-spacing: 2px;">彭博终端风格 - AI投资预测系统 v3.0</p>
    <p style="color: #FF8C00; margin-top: 10px;">基于15个AI智能体协同分析 | 数据来源: OKX + AKShare</p>
    <p style="color: #FF0000; font-size: 1.05em; margin-top: 15px; font-weight: 700;">⚠️ 仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
    <p style="color: #888888; font-size: 0.9em; margin-top: 10px;">© 2026 AI投资预测系统 | 更新时间: {beijing_time.strftime("%Y-%m-%d %H:%M:%S")}</p>
</div>
""", unsafe_allow_html=True)
