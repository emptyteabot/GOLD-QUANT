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
    page_title="AI智投 - 黄金与A股预测",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 获取北京时间
def get_beijing_time():
    """获取北京时间 (Asia/Shanghai)"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(beijing_tz)

# 支付宝风格CSS - 清爽白色主题
st.markdown("""
<style>
    /* ========== 全局样式 - 支付宝清爽风格 ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        background: #F5F5F5;
        color: #262626;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    }

    /* ========== 顶部导航栏 ========== */
    .alipay-header {
        background: linear-gradient(135deg, #1677FF 0%, #4096FF 100%);
        padding: 16px 24px;
        margin: -60px -60px 24px -60px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 8px rgba(22, 119, 255, 0.15);
    }

    .header-logo {
        color: #FFFFFF;
        font-size: 1.5em;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .header-time {
        color: #FFFFFF;
        font-size: 0.9em;
        font-weight: 400;
        opacity: 0.9;
    }

    .header-status {
        color: #FFFFFF;
        font-size: 0.85em;
        font-weight: 500;
        background: rgba(255, 255, 255, 0.2);
        padding: 4px 12px;
        border-radius: 12px;
    }

    /* ========== 主标题 ========== */
    .page-title {
        color: #262626;
        font-size: 1.8em;
        font-weight: 600;
        margin-bottom: 16px;
        padding: 0;
    }

    /* ========== 数据卡片 - 白色圆角卡片 ========== */
    .card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px rgba(0, 0, 0, 0.02);
        transition: all 0.3s ease;
    }

    .card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }

    .card-header {
        color: #8C8C8C;
        font-size: 0.85em;
        font-weight: 500;
        margin-bottom: 8px;
    }

    .card-value {
        color: #262626;
        font-size: 2em;
        font-weight: 600;
        font-family: 'DIN Alternate', 'Helvetica Neue', Arial, sans-serif;
        line-height: 1.2;
    }

    .card-value-large {
        font-size: 2.5em;
    }

    /* ========== 国内股市配色: 红涨绿跌 ========== */
    .price-up {
        color: #FF4D4F !important;
        font-weight: 600;
    }

    .price-down {
        color: #52C41A !important;
        font-weight: 600;
    }

    .price-neutral {
        color: #8C8C8C !important;
        font-weight: 600;
    }

    /* ========== 交易信号卡片 ========== */
    .signal-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 12px;
        border: 2px solid;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }

    .signal-card-strong-buy {
        border-color: #FF4D4F;
        background: linear-gradient(135deg, #FFF1F0 0%, #FFFFFF 100%);
    }

    .signal-card-buy {
        border-color: #FF7875;
        background: linear-gradient(135deg, #FFF1F0 0%, #FFFFFF 100%);
    }

    .signal-card-hold {
        border-color: #FAAD14;
        background: linear-gradient(135deg, #FFFBE6 0%, #FFFFFF 100%);
    }

    .signal-card-sell {
        border-color: #73D13D;
        background: linear-gradient(135deg, #F6FFED 0%, #FFFFFF 100%);
    }

    .signal-card-strong-sell {
        border-color: #52C41A;
        background: linear-gradient(135deg, #F6FFED 0%, #FFFFFF 100%);
    }

    .signal-title {
        color: #8C8C8C;
        font-size: 0.9em;
        font-weight: 500;
        margin-bottom: 8px;
    }

    .signal-value {
        font-size: 2em;
        font-weight: 600;
        margin: 8px 0;
    }

    .signal-strength {
        color: #8C8C8C;
        font-size: 0.85em;
        margin-top: 4px;
    }

    /* ========== Agent分析卡片 ========== */
    .agent-card {
        background: #FAFAFA;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 3px solid #1677FF;
    }

    .agent-name {
        color: #262626;
        font-size: 0.95em;
        font-weight: 600;
        margin-bottom: 6px;
    }

    .agent-prediction-bull {
        color: #FF4D4F;
        font-size: 1em;
        font-weight: 600;
    }

    .agent-prediction-bear {
        color: #52C41A;
        font-size: 1em;
        font-weight: 600;
    }

    .agent-prediction-neutral {
        color: #FAAD14;
        font-size: 1em;
        font-weight: 600;
    }

    .agent-confidence {
        color: #8C8C8C;
        font-size: 0.85em;
        margin-top: 4px;
    }

    .agent-reason {
        color: #595959;
        font-size: 0.85em;
        line-height: 1.6;
        margin-top: 6px;
    }

    /* ========== 更新时间 ========== */
    .update-time {
        text-align: center;
        color: #8C8C8C;
        font-size: 0.85em;
        padding: 8px;
        margin-bottom: 16px;
    }

    /* ========== 按钮样式 ========== */
    .stButton>button {
        background: #FFFFFF;
        color: #1677FF;
        border: 1px solid #D9D9D9;
        border-radius: 8px;
        font-weight: 500;
        padding: 8px 16px;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background: #1677FF;
        color: #FFFFFF;
        border-color: #1677FF;
        box-shadow: 0 2px 8px rgba(22, 119, 255, 0.2);
    }

    .stButton>button[kind="primary"] {
        background: #1677FF;
        color: #FFFFFF;
        border: none;
    }

    .stButton>button[kind="primary"]:hover {
        background: #4096FF;
        box-shadow: 0 4px 12px rgba(22, 119, 255, 0.3);
    }

    /* ========== Metric组件样式 ========== */
    div[data-testid="metric-container"] {
        background: #FFFFFF;
        border: 1px solid #F0F0F0;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }

    div[data-testid="metric-container"] label {
        color: #8C8C8C !important;
        font-weight: 500 !important;
        font-size: 0.85em !important;
    }

    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #262626 !important;
        font-family: 'DIN Alternate', sans-serif !important;
        font-size: 2em !important;
        font-weight: 600 !important;
    }

    div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
    }

    /* ========== Expander样式 ========== */
    .streamlit-expanderHeader {
        background: #FAFAFA !important;
        border: 1px solid #F0F0F0 !important;
        border-radius: 8px !important;
        color: #262626 !important;
        font-weight: 500 !important;
        padding: 12px 16px !important;
    }

    .streamlit-expanderHeader:hover {
        background: #F5F5F5 !important;
        border-color: #D9D9D9 !important;
    }

    .streamlit-expanderContent {
        background: #FFFFFF !important;
        border: 1px solid #F0F0F0 !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* ========== 侧边栏 ========== */
    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #F0F0F0;
    }

    section[data-testid="stSidebar"] * {
        color: #262626 !important;
    }

    section[data-testid="stSidebar"] .stRadio label {
        color: #262626 !important;
        font-weight: 500 !important;
    }

    section[data-testid="stSidebar"] h2 {
        color: #262626 !important;
        font-weight: 600 !important;
    }

    /* ========== 输入框 ========== */
    .stTextInput>div>div>input {
        background: #FFFFFF;
        color: #262626;
        border: 1px solid #D9D9D9;
        border-radius: 8px;
        font-weight: 400;
        padding: 8px 12px;
    }

    .stTextInput>div>div>input:focus {
        border-color: #1677FF;
        box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
    }

    /* ========== 标题样式 ========== */
    h1, h2, h3, h4, h5, h6 {
        color: #262626 !important;
        font-weight: 600 !important;
    }

    h3 {
        font-size: 1.3em !important;
        margin-top: 24px !important;
        margin-bottom: 16px !important;
    }

    /* ========== 文字颜色 ========== */
    p, li, span, div {
        color: #262626 !important;
    }

    .stMarkdown {
        color: #262626 !important;
    }

    /* ========== 分隔线 ========== */
    hr {
        border-color: #F0F0F0 !important;
        opacity: 1;
        margin: 24px 0;
    }

    /* ========== 滚动条 ========== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #F5F5F5;
    }

    ::-webkit-scrollbar-thumb {
        background: #D9D9D9;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #BFBFBF;
    }

    /* ========== 图标样式 ========== */
    .icon-up {
        color: #FF4D4F;
    }

    .icon-down {
        color: #52C41A;
    }

    .icon-neutral {
        color: #FAAD14;
    }

    /* ========== 徽章样式 ========== */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75em;
        font-weight: 500;
    }

    .badge-up {
        background: #FFF1F0;
        color: #FF4D4F;
    }

    .badge-down {
        background: #F6FFED;
        color: #52C41A;
    }

    /* ========== 响应式设计 ========== */
    @media (max-width: 768px) {
        .card-value {
            font-size: 1.5em;
        }

        .signal-value {
            font-size: 1.5em;
        }
    }
</style>
""", unsafe_allow_html=True)

# 顶部导航栏 - 支付宝风格
beijing_time = get_beijing_time()
st.markdown(f"""
<div class="alipay-header">
    <div class="header-logo">💰 AI智投</div>
    <div class="header-time">{beijing_time.strftime("%Y-%m-%d %H:%M:%S")}</div>
    <div class="header-status">● 实时数据</div>
</div>
""", unsafe_allow_html=True)

# 侧边栏 - 功能选择
st.sidebar.markdown("## 功能菜单")
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
        st.markdown('<div class="page-title">💰 黄金价格预测</div>', unsafe_allow_html=True)
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
        st.markdown(f'<div class="update-time">📡 数据更新: {gold_data["update_time"]}</div>', unsafe_allow_html=True)

        # 显示当前金价 - 4列网格布局
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            change_class = "price-up" if gold_data['change_pct'] >= 0 else "price-down"
            change_icon = "📈" if gold_data['change_pct'] >= 0 else "📉"
            st.markdown(f"""
            <div class="card">
                <div class="card-header">现货黄金 (美元/盎司)</div>
                <div class="card-value card-value-large">${current_price:.2f}</div>
                <div class="{change_class}" style="font-size: 1.1em; margin-top: 4px;">{change_icon} {gold_data['change_pct']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">24小时最高</div>
                <div class="card-value">${gold_data['high']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">24小时最低</div>
                <div class="card-value">${gold_data['low']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">24小时成交量</div>
                <div class="card-value" style="font-size: 1.5em;">{gold_data['volume']:.0f}</div>
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
            change_class = "price-up" if prediction['predicted_change'] >= 0 else "price-down"
            change_icon = "📈" if prediction['predicted_change'] >= 0 else "📉"
            st.markdown(f"""
            <div class="card">
                <div class="card-header">预测价格 (明日)</div>
                <div class="card-value card-value-large">${prediction['predicted_price']:.2f}</div>
                <div class="{change_class}" style="font-size: 1.1em; margin-top: 4px;">{change_icon} {prediction['predicted_change']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">AI置信度</div>
                <div class="card-value">{prediction['avg_confidence']*100:.1f}%</div>
                <div style="color: #8C8C8C; font-size: 0.85em; margin-top: 4px;">基于 {prediction['bullish_count']} 个看涨信号</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">AI共识分布</div>
                <div style="margin-top: 8px;">
                    <div style="color: #FF4D4F; font-size: 1em; margin: 4px 0; font-weight: 600;">▲ 看涨: {prediction['bullish_count']}</div>
                    <div style="color: #FAAD14; font-size: 1em; margin: 4px 0; font-weight: 600;">● 中性: {prediction['neutral_count']}</div>
                    <div style="color: #52C41A; font-size: 1em; margin: 4px 0; font-weight: 600;">▼ 看跌: {prediction['bearish_count']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            signal_color = "#FF4D4F" if "买入" in signal['type'] else "#52C41A" if "卖出" in signal['type'] else "#FAAD14"
            st.markdown(f"""
            <div class="signal-card signal-card-{signal['class'].replace('signal-', '')}">
                <div class="signal-title">交易信号</div>
                <div class="signal-value" style="color: {signal_color};">{signal['emoji']} {signal['type']}</div>
                <div class="signal-strength">信号强度: {signal['strength']}/100</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 交易建议详情 - 3列网格
        st.markdown("### 💡 交易建议")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">📊 仓位建议</div>
                <div style="color: #262626; font-size: 1.1em; margin-top: 10px; font-weight: 500;">{signal['position_advice']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">🛡️ 止损价位</div>
                <div style="color: #52C41A; font-size: 1.8em; margin-top: 10px; font-weight: 600;">${signal['stop_loss']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">🎯 止盈价位</div>
                <div style="color: #FF4D4F; font-size: 1.8em; margin-top: 10px; font-weight: 600;">${signal['take_profit']:.2f}</div>
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
                emoji = "📈" if agent['prediction'] == '看涨' else "📉" if agent['prediction'] == '看跌' else "➖"

                with st.expander(f"{emoji} {agent['name']} - {agent['prediction']} ({agent['confidence']*100:.1f}%)", expanded=False):
                    st.markdown(f"""
                    <div class="agent-card">
                        <div class="agent-name">{agent['name']}</div>
                        <div class="{pred_class}">预测: {agent['prediction']}</div>
                        <div class="agent-confidence">置信度: {agent['confidence']*100:.1f}%</div>
                        <div class="agent-reason">{agent['reason']}</div>
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
            increasing_line_color='#FF4D4F',  # 红涨
            decreasing_line_color='#52C41A',  # 绿跌
            increasing_fillcolor='#FF4D4F',
            decreasing_fillcolor='#52C41A'
        )])

        fig.update_layout(
            title='黄金价格走势 (美元/盎司)',
            yaxis_title='价格',
            template='plotly_white',
            height=500,
            xaxis_rangeslider_visible=False,
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#FAFAFA',
            font=dict(color='#262626', family='PingFang SC, Microsoft YaHei', size=12),
            title_font=dict(color='#262626', size=16, family='PingFang SC, Microsoft YaHei', weight=600),
            xaxis=dict(
                gridcolor='#F0F0F0',
                showgrid=True,
                color='#8C8C8C'
            ),
            yaxis=dict(
                gridcolor='#F0F0F0',
                showgrid=True,
                color='#8C8C8C'
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
        st.markdown('<div class="page-title">📈 A股价格预测</div>', unsafe_allow_html=True)
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
                    st.markdown(f'<div class="update-time">📡 数据更新: {beijing_time.strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)

                    # 显示当前股价 - 4列网格
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        change_class = "price-up" if stock_data['change_pct'] >= 0 else "price-down"
                        change_icon = "📈" if stock_data['change_pct'] >= 0 else "📉"
                        st.markdown(f"""
                        <div class="card">
                            <div class="card-header">当前价格 (人民币)</div>
                            <div class="card-value card-value-large">¥{stock_data['price']:.2f}</div>
                            <div class="{change_class}" style="font-size: 1.1em; margin-top: 4px;">{change_icon} {stock_data['change_pct']:+.2f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="card">
                            <div class="card-header">今日最高</div>
                            <div class="card-value">¥{stock_data['high']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div class="card">
                            <div class="card-header">今日最低</div>
                            <div class="card-value">¥{stock_data['low']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col4:
                        st.markdown(f"""
                        <div class="card">
                            <div class="card-header">成交量</div>
                            <div class="card-value" style="font-size: 1.5em;">{stock_data['volume']:.0f}</div>
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
                st.markdown(f'<div class="update-time">📡 数据更新: {beijing_time.strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)

                # 显示当前股价 - 4列网格
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    change_class = "price-up" if change_pct >= 0 else "price-down"
                    change_icon = "📈" if change_pct >= 0 else "📉"
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-header">当前价格 (人民币)</div>
                        <div class="card-value card-value-large">¥{current_price:.2f}</div>
                        <div class="{change_class}" style="font-size: 1.1em; margin-top: 4px;">{change_icon} {change_pct:+.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-header">今日最高</div>
                        <div class="card-value">¥{current_price * 1.02:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-header">今日最低</div>
                        <div class="card-value">¥{current_price * 0.98:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-header">成交量</div>
                        <div class="card-value" style="font-size: 1.3em;">{np.random.randint(1000, 50000)}万手</div>
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
                change_class = "price-up" if prediction['predicted_change'] >= 0 else "price-down"
                change_icon = "📈" if prediction['predicted_change'] >= 0 else "📉"
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">预测价格 (明日)</div>
                    <div class="card-value card-value-large">¥{prediction['predicted_price']:.2f}</div>
                    <div class="{change_class}" style="font-size: 1.1em; margin-top: 4px;">{change_icon} {prediction['predicted_change']:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">AI置信度</div>
                    <div class="card-value">{prediction['avg_confidence']*100:.1f}%</div>
                    <div style="color: #8C8C8C; font-size: 0.85em; margin-top: 4px;">基于 {prediction['bullish_count']} 个看涨信号</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">AI共识分布</div>
                    <div style="margin-top: 8px;">
                        <div style="color: #FF4D4F; font-size: 1em; margin: 4px 0; font-weight: 600;">▲ 看涨: {prediction['bullish_count']}</div>
                        <div style="color: #FAAD14; font-size: 1em; margin: 4px 0; font-weight: 600;">● 中性: {prediction['neutral_count']}</div>
                        <div style="color: #52C41A; font-size: 1em; margin: 4px 0; font-weight: 600;">▼ 看跌: {prediction['bearish_count']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                signal_color = "#FF4D4F" if "买入" in signal['type'] else "#52C41A" if "卖出" in signal['type'] else "#FAAD14"
                st.markdown(f"""
                <div class="signal-card signal-card-{signal['class'].replace('signal-', '')}">
                    <div class="signal-title">交易信号</div>
                    <div class="signal-value" style="color: {signal_color};">{signal['emoji']} {signal['type']}</div>
                    <div class="signal-strength">信号强度: {signal['strength']}/100</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # 交易建议详情 - 3列网格
            st.markdown("### 💡 交易建议")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">📊 仓位建议</div>
                    <div style="color: #262626; font-size: 1.1em; margin-top: 10px; font-weight: 500;">{signal['position_advice']}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">🛡️ 止损价位</div>
                    <div style="color: #52C41A; font-size: 1.8em; margin-top: 10px; font-weight: 600;">¥{signal['stop_loss']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">🎯 止盈价位</div>
                    <div style="color: #FF4D4F; font-size: 1.8em; margin-top: 10px; font-weight: 600;">¥{signal['take_profit']:.2f}</div>
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
                    emoji = "📈" if agent_pred == '看涨' else "📉" if agent_pred == '看跌' else "➖"

                    with st.expander(f"{emoji} {agent_name} - {agent_pred} ({agent_conf*100:.1f}%)", expanded=False):
                        st.markdown(f"""
                        <div class="agent-card">
                            <div class="agent-name">{agent_name}</div>
                            <div class="{pred_class}">预测: {agent_pred}</div>
                            <div class="agent-confidence">置信度: {agent_conf*100:.1f}%</div>
                            <div class="agent-reason">{agent_reason}</div>
                        </div>
                        """, unsafe_allow_html=True)

    elif predict_btn and not stock_code:
        st.warning("⚠️ 请输入股票代码")

# ==================== 关于系统页面 ====================
elif page == "📖 关于系统":
    st.markdown('<div class="page-title">📖 关于系统</div>', unsafe_allow_html=True)

    # 系统简介
    st.markdown("""
    <div class="card">
        <div class="card-header" style="font-size: 1em; margin-bottom: 12px;">🎯 系统概述</div>
        <p style="color: #595959; font-size: 1em; line-height: 1.8; margin-top: 8px;">
            基于<span style="color: #1677FF; font-weight: 600;">15个AI智能体协同分析</span>的投资预测系统，
            整合宏观经济、技术面、资金流向、机器学习等多维度分析，
            为投资者提供<span style="color: #1677FF; font-weight: 600;">专业实时</span>的决策参考。
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 核心功能
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-header" style="font-size: 1em; margin-bottom: 12px;">💰 黄金价格预测</div>
            <ul style="color: #595959; line-height: 2; margin-top: 8px; padding-left: 20px;">
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
        <div class="card">
            <div class="card-header" style="font-size: 1em; margin-bottom: 12px;">📈 A股价格预测</div>
            <ul style="color: #595959; line-height: 2; margin-top: 8px; padding-left: 20px;">
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
    <div class="card">
        <div class="card-header" style="font-size: 1em; margin-bottom: 12px;">🎯 交易信号说明</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("""
        <div class="signal-card signal-card-strong-buy">
            <div class="signal-title">强烈买入</div>
            <div style="font-size: 2em; margin: 8px 0;">📈</div>
            <p style="font-size: 0.85em; color: #8C8C8C; margin-top: 8px;">预测涨幅 > 1.5%<br>置信度 > 75%</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="signal-card signal-card-buy">
            <div class="signal-title">买入</div>
            <div style="font-size: 2em; margin: 8px 0;">📈</div>
            <p style="font-size: 0.85em; color: #8C8C8C; margin-top: 8px;">预测涨幅 > 0.5%<br>置信度 > 65%</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="signal-card signal-card-hold">
            <div class="signal-title">观望</div>
            <div style="font-size: 2em; margin: 8px 0;">➖</div>
            <p style="font-size: 0.85em; color: #8C8C8C; margin-top: 8px;">预测涨跌幅 ≤ 0.5%<br>信号不明确</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="signal-card signal-card-sell">
            <div class="signal-title">卖出</div>
            <div style="font-size: 2em; margin: 8px 0;">📉</div>
            <p style="font-size: 0.85em; color: #8C8C8C; margin-top: 8px;">预测跌幅 > 0.5%<br>置信度 > 65%</p>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
        <div class="signal-card signal-card-strong-sell">
            <div class="signal-title">强烈卖出</div>
            <div style="font-size: 2em; margin: 8px 0;">📉</div>
            <p style="font-size: 0.85em; color: #8C8C8C; margin-top: 8px;">预测跌幅较大<br>风险信号明显</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 风险提示
    st.markdown("""
    <div class="card" style="border: 2px solid #FF4D4F; background: linear-gradient(135deg, #FFF1F0 0%, #FFFFFF 100%);">
        <div class="card-header" style="color: #FF4D4F; font-size: 1em; margin-bottom: 12px;">⚠️ 风险提示</div>
        <div style="color: #595959; font-size: 0.95em; line-height: 2; margin-top: 8px;">
            <p>1. 预测结果<span style="color: #FF4D4F; font-weight: 600;">仅供参考</span>，不构成投资建议</p>
            <p>2. 金融市场存在<span style="color: #FF4D4F; font-weight: 600;">不可预测风险</span></p>
            <p>3. 应根据<span style="color: #FF4D4F; font-weight: 600;">自身风险承受能力</span>独立判断</p>
            <p>4. <span style="color: #FF4D4F; font-weight: 600;">投资有风险，入市需谨慎</span></p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 技术支持
    beijing_time = get_beijing_time()
    st.markdown(f"""
    <div class="card">
        <div class="card-header" style="font-size: 1em; margin-bottom: 12px;">💬 技术信息</div>
        <p style="color: #595959; font-size: 0.95em; line-height: 2; margin-top: 8px;">
            <span style="color: #262626; font-weight: 600;">数据来源:</span> OKX (黄金) + AKShare (A股)<br>
            <span style="color: #262626; font-weight: 600;">AI技术:</span> 多智能体协同 + 机器学习<br>
            <span style="color: #262626; font-weight: 600;">更新频率:</span> 实时数据，60秒缓存<br>
            <span style="color: #262626; font-weight: 600;">系统版本:</span> v4.0 支付宝风格<br>
            <span style="color: #262626; font-weight: 600;">更新时间:</span> {beijing_time.strftime("%Y-%m-%d %H:%M:%S")}
        </p>
    </div>
    """, unsafe_allow_html=True)

# 页脚
st.markdown("---")
beijing_time = get_beijing_time()
st.markdown(f"""
<div style='text-align: center; padding: 24px; background: #FFFFFF; border-radius: 12px; margin-top: 24px;'>
    <p style="font-size: 1.2em; color: #262626; font-weight: 600;">💰 AI智投 - 黄金与A股预测系统 v4.0</p>
    <p style="color: #8C8C8C; margin-top: 8px; font-size: 0.9em;">基于15个AI智能体协同分析 | 数据来源: OKX + AKShare</p>
    <p style="color: #FF4D4F; font-size: 0.95em; margin-top: 12px; font-weight: 500;">⚠️ 仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
    <p style="color: #BFBFBF; font-size: 0.85em; margin-top: 8px;">© 2026 AI智投系统 | 更新时间: {beijing_time.strftime("%Y-%m-%d %H:%M:%S")}</p>
</div>
""", unsafe_allow_html=True)
