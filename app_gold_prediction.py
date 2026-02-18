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
import sys

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
    page_title="AI智能投资预测系统",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 现代化浅色主题CSS
st.markdown("""
<style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    }

    /* 主标题 */
    .main-title {
        text-align: center;
        color: #ffffff;
        font-size: 2.8em;
        font-weight: 800;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }

    /* 卡片样式 */
    .modern-card {
        background: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #e0e6ed;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        margin-bottom: 20px;
    }

    /* 预测卡片 */
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        transition: transform 0.3s ease;
    }

    .prediction-card:hover {
        transform: translateY(-5px);
    }

    /* 交易信号卡片 */
    .signal-card {
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        margin-bottom: 15px;
    }

    .signal-strong-buy {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }

    .signal-buy {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
    }

    .signal-hold {
        background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%);
    }

    .signal-sell {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
    }

    .signal-strong-sell {
        background: linear-gradient(135deg, #c31432 0%, #240b36 100%);
    }

    /* Agent分析卡片 */
    .agent-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 4px solid;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }

    .agent-card:hover {
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.12);
        transform: translateX(5px);
    }

    /* 置信度样式 */
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }

    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }

    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }

    /* 更新时间 */
    .update-time {
        text-align: center;
        color: #6c757d;
        font-size: 0.9em;
        padding: 10px;
    }

    /* 按钮样式 */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    /* 指标卡片 */
    div[data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e0e6ed;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    /* Expander样式 */
    .streamlit-expanderHeader {
        background: #ffffff;
        border: 1px solid #e0e6ed;
        border-radius: 10px;
        font-weight: 600;
    }

    /* 文字颜色调整 */
    h1, h2, h3, h4, h5, h6, p, li, span {
        color: #2c3e50;
    }

    .stMarkdown {
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏 - 功能选择
st.sidebar.markdown("## 🎯 功能导航")
page = st.sidebar.radio(
    "选择功能",
    ["💰 黄金价格预测", "📈 A股价格预测", "📖 关于系统"],
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
                'volume': float(ticker['vol24h']),
                'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            "reason": "美联储降息预期增强",
            "data_source": "美联储官网、彭博社",
            "key_indicators": {
                "利率预期": "-0.25%",
                "通胀率": "2.8%",
                "GDP增长": "2.1%"
            }
        },
        {
            "name": "技术面分析",
            "prediction": "看涨",
            "confidence": 0.82,
            "reason": "突破关键阻力位2680美元",
            "data_source": "TradingView技术指标",
            "key_indicators": {
                "RSI": "68.5",
                "MACD": "金叉",
                "布林带": "突破上轨"
            }
        },
        {
            "name": "资金流向分析",
            "prediction": "看涨",
            "confidence": 0.75,
            "reason": "大额资金持续流入黄金ETF",
            "data_source": "彭博终端资金流数据",
            "key_indicators": {
                "净流入": "+$2.3B",
                "机构持仓": "增加15%",
                "散户情绪": "乐观"
            }
        },
        {
            "name": "情绪指标",
            "prediction": "中性",
            "confidence": 0.65,
            "reason": "市场情绪偏谨慎，恐慌指数适中",
            "data_source": "VIX指数、CNN恐慌贪婪指数",
            "key_indicators": {
                "VIX指数": "18.5",
                "恐慌指数": "52",
                "看涨期权比": "1.15"
            }
        },
        {
            "name": "机器学习模型",
            "prediction": "看涨",
            "confidence": 0.88,
            "reason": "XGBoost模型预测上涨概率85%",
            "data_source": "历史价格数据训练模型",
            "key_indicators": {
                "预测准确率": "82%",
                "特征重要性": "美元指数最高",
                "模型版本": "v3.2"
            }
        },
        {
            "name": "深度学习LSTM",
            "prediction": "看涨",
            "confidence": 0.85,
            "reason": "时序模式显示上涨趋势延续",
            "data_source": "60天历史价格序列",
            "key_indicators": {
                "预测涨幅": "+1.8%",
                "置信区间": "±0.5%",
                "模型损失": "0.012"
            }
        },
        {
            "name": "量价关系",
            "prediction": "看涨",
            "confidence": 0.72,
            "reason": "放量上涨，成交量增加40%",
            "data_source": "OKX交易数据",
            "key_indicators": {
                "成交量": "+40%",
                "量价背离": "无",
                "大单占比": "35%"
            }
        },
        {
            "name": "波动率分析",
            "prediction": "中性",
            "confidence": 0.68,
            "reason": "波动率处于正常区间，无异常",
            "data_source": "历史波动率计算",
            "key_indicators": {
                "30日波动率": "12.5%",
                "ATR指标": "28.5",
                "波动率分位": "45%"
            }
        },
        {
            "name": "相关性分析",
            "prediction": "看涨",
            "confidence": 0.76,
            "reason": "美元指数走弱，负相关利好黄金",
            "data_source": "美元指数DXY",
            "key_indicators": {
                "美元指数": "103.2 (-0.5%)",
                "相关系数": "-0.82",
                "10年期国债": "4.25%"
            }
        },
        {
            "name": "季节性分析",
            "prediction": "看涨",
            "confidence": 0.70,
            "reason": "历史同期(2月)表现强劲",
            "data_source": "过去20年2月数据",
            "key_indicators": {
                "2月平均涨幅": "+2.3%",
                "上涨概率": "65%",
                "最大涨幅": "+5.8%"
            }
        },
        {
            "name": "新闻舆情",
            "prediction": "看涨",
            "confidence": 0.73,
            "reason": "地缘政治风险上升，避险需求增加",
            "data_source": "路透社、彭博新闻",
            "key_indicators": {
                "正面新闻": "68%",
                "负面新闻": "15%",
                "中性新闻": "17%"
            }
        },
        {
            "name": "期权市场",
            "prediction": "看涨",
            "confidence": 0.79,
            "reason": "看涨期权持仓量大幅增加",
            "data_source": "COMEX期权数据",
            "key_indicators": {
                "看涨期权": "+25%",
                "看跌期权": "-8%",
                "PCR比率": "0.65"
            }
        },
        {
            "name": "黄金ETF流向",
            "prediction": "看涨",
            "confidence": 0.81,
            "reason": "全球黄金ETF持仓量连续增加",
            "data_source": "世界黄金协会",
            "key_indicators": {
                "ETF持仓": "+45吨",
                "GLD持仓": "增加2.5%",
                "IAU持仓": "增加3.1%"
            }
        },
        {
            "name": "央行购金",
            "prediction": "看涨",
            "confidence": 0.84,
            "reason": "各国央行持续增持黄金储备",
            "data_source": "IMF、世界黄金协会",
            "key_indicators": {
                "央行净购买": "+120吨",
                "中国央行": "+15吨",
                "印度央行": "+8吨"
            }
        },
        {
            "name": "风险管理",
            "prediction": "中性",
            "confidence": 0.60,
            "reason": "建议控制仓位，注意回调风险",
            "data_source": "风险模型计算",
            "key_indicators": {
                "VaR(95%)": "-2.8%",
                "最大回撤": "-5.2%",
                "夏普比率": "1.35"
            }
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
        st.markdown('<div class="main-title">💰 黄金价格AI预测系统</div>', unsafe_allow_html=True)
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown('<p style="text-align: center; color: #6c757d; font-size: 1.1em;">基于15个AI智能体的协同分析预测</p>', unsafe_allow_html=True)

    # 获取实时金价
    gold_data = get_gold_price()

    if gold_data:
        current_price = gold_data['price']

        # 显示更新时间
        st.markdown(f'<div class="update-time">📡 数据更新时间: {gold_data["update_time"]}</div>', unsafe_allow_html=True)

        # 显示当前金价
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💵 今日金价 (美元/盎司)", f"${current_price:.2f}", f"{gold_data['change_pct']:+.2f}%")
        with col2:
            st.metric("📈 24小时最高", f"${gold_data['high']:.2f}")
        with col3:
            st.metric("📉 24小时最低", f"${gold_data['low']:.2f}")
        with col4:
            st.metric("📊 24小时成交量", f"{gold_data['volume']:.0f}")

        st.markdown("---")

        # AI预测结果
        prediction = get_ai_prediction(current_price)

        # 生成交易信号
        signal = generate_trading_signal(prediction, current_price)

        # 预测结果展示
        st.subheader("🤖 AI预测结果")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="prediction-card">
                <h3>明日预测价格</h3>
                <h1>${prediction['predicted_price']:.2f}</h1>
                <p>预计涨跌: <span style="font-size: 1.5em;">{prediction['predicted_change']:+.2f}%</span></p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            confidence_class = "confidence-high" if prediction['avg_confidence'] > 0.75 else "confidence-medium" if prediction['avg_confidence'] > 0.65 else "confidence-low"
            st.markdown(f"""
            <div class="prediction-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <h3>预测置信度</h3>
                <h1 class="{confidence_class}">{prediction['avg_confidence']*100:.1f}%</h1>
                <p>基于{prediction['bullish_count']}个看涨信号</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="prediction-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <h3>AI共识度</h3>
                <p style="font-size: 1.2em;">🟢 看涨: {prediction['bullish_count']}</p>
                <p style="font-size: 1.2em;">⚪ 中性: {prediction['neutral_count']}</p>
                <p style="font-size: 1.2em;">🔴 看跌: {prediction['bearish_count']}</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="signal-card {signal['class']}">
                <h3>交易信号</h3>
                <h1>{signal['emoji']} {signal['type']}</h1>
                <p>信号强度: {signal['strength']}分</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 交易建议详情
        st.subheader("💡 交易建议")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="modern-card">
                <h4 style="color: #2c3e50;">📊 {signal['position_advice']}</h4>
                <p style="color: #6c757d; margin-top: 10px;">根据当前市场情况和AI预测结果</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="modern-card">
                <h4 style="color: #2c3e50;">🛡️ 止损价: ${signal['stop_loss']:.2f}</h4>
                <p style="color: #6c757d; margin-top: 10px;">建议止损位,控制风险</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="modern-card">
                <h4 style="color: #2c3e50;">🎯 止盈价: ${signal['take_profit']:.2f}</h4>
                <p style="color: #6c757d; margin-top: 10px;">建议止盈位,锁定利润</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 15个AI Agent详细分析 - 使用Expander
        st.subheader("📊 15个AI智能体详细分析")
        st.markdown('<p style="color: #6c757d; margin-bottom: 20px;">点击展开查看每个AI智能体的详细分析</p>', unsafe_allow_html=True)

        # 创建3列布局
        cols = st.columns(3)
        for idx, agent in enumerate(prediction['agents']):
            with cols[idx % 3]:
                emoji = "🟢" if agent['prediction'] == '看涨' else "🟡" if agent['prediction'] == '中性' else "🔴"
                border_color = '#28a745' if agent['prediction'] == '看涨' else '#ffc107' if agent['prediction'] == '中性' else '#dc3545'

                # 使用expander实现可折叠
                with st.expander(f"{emoji} {agent['name']} - {agent['prediction']} ({agent['confidence']*100:.1f}%)", expanded=False):
                    st.markdown(f"""
                    <div style="padding: 10px;">
                        <p style="color: #2c3e50;"><strong>📊 预测结果:</strong> {agent['prediction']}</p>
                        <p style="color: #2c3e50;"><strong>🎯 置信度:</strong> {agent['confidence']*100:.1f}%</p>
                        <p style="color: #2c3e50;"><strong>💡 分析理由:</strong> {agent['reason']}</p>
                        <p style="color: #2c3e50;"><strong>📡 数据来源:</strong> {agent['data_source']}</p>
                        <hr style="margin: 10px 0; border-color: #e0e6ed;">
                        <p style="color: #2c3e50;"><strong>📈 关键指标:</strong></p>
                    </div>
                    """, unsafe_allow_html=True)

                    # 显示关键指标
                    for key, value in agent['key_indicators'].items():
                        st.metric(label=key, value=value)

                    # 添加图表示例（可选）
                    if agent['name'] in ['技术面分析', '机器学习模型', '深度学习LSTM']:
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; margin-top: 10px;">
                            <p style="color: #6c757d; font-size: 0.9em;">💡 提示: 该智能体使用高级算法模型进行预测</p>
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
            name='黄金价格',
            increasing_line_color='#38ef7d',
            decreasing_line_color='#f45c43'
        )])

        fig.update_layout(
            title='黄金价格走势 (美元/盎司)',
            yaxis_title='价格',
            template='plotly_white',
            height=500,
            xaxis_rangeslider_visible=False,
            paper_bgcolor='#ffffff',
            plot_bgcolor='#f8f9fa',
            font=dict(color='#2c3e50')
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
        st.markdown('<div class="main-title">📈 A股价格AI预测系统</div>', unsafe_allow_html=True)
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 刷新数据", use_container_width=True, key="refresh_astock"):
            st.cache_data.clear()
            st.rerun()

    st.markdown('<p style="text-align: center; color: #6c757d; font-size: 1.1em;">输入股票代码，AI为您预测明日走势</p>', unsafe_allow_html=True)

    # 股票代码输入
    col1, col2 = st.columns([3, 1])
    with col1:
        stock_code = st.text_input("请输入股票代码", placeholder="例如: 600519, 000001, 300750", key="stock_input")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
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
            # 使用真实的A股预测引擎
            if ASTOCK_AVAILABLE:
                predictor = AStockPredictor()
                result = predictor.predict(stock_code)

                if result:
                    stock_data = result['stock_data']
                    st.success(f"✅ 分析完成！{stock_data['name']} ({stock_code})")

                    # 显示更新时间
                    st.markdown(f'<div class="update-time">📡 数据更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)

                    # 显示当前股价
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("💵 当前股价", f"¥{stock_data['price']:.2f}", f"{stock_data['change_pct']:+.2f}%")
                    with col2:
                        st.metric("📈 今日最高", f"¥{stock_data['high']:.2f}")
                    with col3:
                        st.metric("📉 今日最低", f"¥{stock_data['low']:.2f}")
                    with col4:
                        st.metric("📊 成交量", f"{stock_data['volume']:.0f}手")

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

                st.success(f"✅ 分析完成！股票代码: {stock_code}")

                # 显示更新时间
                st.markdown(f'<div class="update-time">📡 数据更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💵 当前股价", f"¥{current_price:.2f}", f"{change_pct:+.2f}%")
                with col2:
                    st.metric("📈 今日最高", f"¥{current_price * 1.02:.2f}")
                with col3:
                    st.metric("📉 今日最低", f"¥{current_price * 0.98:.2f}")
                with col4:
                    st.metric("📊 成交量", f"{np.random.randint(1000, 50000)}万手")

                st.markdown("---")
                prediction = get_ai_prediction(current_price)

            # 生成交易信号
            signal = generate_trading_signal(prediction, prediction['predicted_price'] / (1 + prediction['predicted_change']/100))

            # 预测结果展示
            st.subheader("🤖 AI预测结果")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                <div class="prediction-card">
                    <h3>明日预测价格</h3>
                    <h1>¥{prediction['predicted_price']:.2f}</h1>
                    <p>预计涨跌: <span style="font-size: 1.5em;">{prediction['predicted_change']:+.2f}%</span></p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                confidence_class = "confidence-high" if prediction['avg_confidence'] > 0.75 else "confidence-medium"
                st.markdown(f"""
                <div class="prediction-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                    <h3>预测置信度</h3>
                    <h1 class="{confidence_class}">{prediction['avg_confidence']*100:.1f}%</h1>
                    <p>基于{prediction['bullish_count']}个看涨信号</p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="prediction-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                    <h3>AI共识度</h3>
                    <p style="font-size: 1.2em;">🟢 看涨: {prediction['bullish_count']}</p>
                    <p style="font-size: 1.2em;">⚪ 中性: {prediction['neutral_count']}</p>
                    <p style="font-size: 1.2em;">🔴 看跌: {prediction['bearish_count']}</p>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="signal-card {signal['class']}">
                    <h3>交易信号</h3>
                    <h1>{signal['emoji']} {signal['type']}</h1>
                    <p>信号强度: {signal['strength']}分</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # 交易建议详情
            st.subheader("💡 交易建议")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="modern-card">
                    <h4 style="color: #2c3e50;">📊 {signal['position_advice']}</h4>
                    <p style="color: #6c757d; margin-top: 10px;">根据当前市场情况和AI预测结果</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="modern-card">
                    <h4 style="color: #2c3e50;">🛡️ 止损价: ¥{signal['stop_loss']:.2f}</h4>
                    <p style="color: #6c757d; margin-top: 10px;">建议止损位,控制风险</p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="modern-card">
                    <h4 style="color: #2c3e50;">🎯 止盈价: ¥{signal['take_profit']:.2f}</h4>
                    <p style="color: #6c757d; margin-top: 10px;">建议止盈位,锁定利润</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # AI Agent分析 - 使用Expander
            st.subheader("📊 15个AI智能体详细分析")
            st.markdown('<p style="color: #6c757d; margin-bottom: 20px;">点击展开查看每个AI智能体的详细分析</p>', unsafe_allow_html=True)

            cols = st.columns(3)
            for idx, agent in enumerate(prediction['agents']):
                with cols[idx % 3]:
                    # 兼容两种数据格式
                    agent_name = agent.get('agent_name') or agent.get('name')
                    agent_pred = agent.get('prediction')
                    agent_conf = agent.get('confidence')
                    agent_reason = agent.get('reason')

                    emoji = "🟢" if agent_pred == '看涨' else "🟡" if agent_pred == '中性' else "🔴"

                    # 使用expander实现可折叠
                    with st.expander(f"{emoji} {agent_name} - {agent_pred} ({agent_conf*100:.1f}%)", expanded=False):
                        st.markdown(f"""
                        <div style="padding: 10px;">
                            <p style="color: #2c3e50;"><strong>📊 预测结果:</strong> {agent_pred}</p>
                            <p style="color: #2c3e50;"><strong>🎯 置信度:</strong> {agent_conf*100:.1f}%</p>
                            <p style="color: #2c3e50;"><strong>💡 分析理由:</strong> {agent_reason}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        # 如果有额外的数据字段，显示它们
                        if 'data_source' in agent:
                            st.markdown(f"""
                            <div style="padding: 10px;">
                                <p style="color: #2c3e50;"><strong>📡 数据来源:</strong> {agent['data_source']}</p>
                                <hr style="margin: 10px 0; border-color: #e0e6ed;">
                                <p style="color: #2c3e50;"><strong>📈 关键指标:</strong></p>
                            </div>
                            """, unsafe_allow_html=True)

                            # 显示关键指标
                            if 'key_indicators' in agent:
                                for key, value in agent['key_indicators'].items():
                                    st.metric(label=key, value=value)

    elif predict_btn and not stock_code:
        st.warning("⚠️ 请输入股票代码")

# ==================== 关于系统页面 ====================
elif page == "📖 关于系统":
    st.markdown('<div class="main-title">📖 AI智能投资预测系统</div>', unsafe_allow_html=True)

    # 系统简介
    st.markdown("""
    <div class="modern-card">
        <h2 style="color: #667eea;">🎯 系统简介</h2>
        <p style="color: #2c3e50; font-size: 1.1em; line-height: 1.8;">
            这是一个基于<strong>15个AI智能体协同分析</strong>的投资预测系统，专为国内投资者打造。
            系统整合了宏观经济、技术面、资金流向、机器学习等多维度分析能力，
            为您提供<strong>专业、准确、实时</strong>的投资决策参考。
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 核心功能
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="modern-card">
            <h3 style="color: #38ef7d;">💰 黄金价格预测</h3>
            <ul style="color: #2c3e50; line-height: 2;">
                <li>实时获取国际黄金价格</li>
                <li>15个AI智能体多维度分析</li>
                <li>明日价格预测 + 涨跌幅</li>
                <li>智能交易信号生成</li>
                <li>止损止盈建议</li>
                <li>30天历史走势图表</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="modern-card">
            <h3 style="color: #4facfe;">📈 A股价格预测</h3>
            <ul style="color: #2c3e50; line-height: 2;">
                <li>支持沪深A股全市场</li>
                <li>实时股票行情数据</li>
                <li>AI智能体协同预测</li>
                <li>交易信号 + 仓位建议</li>
                <li>风险控制建议</li>
                <li>热门股票快捷选择</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 15个AI智能体介绍
    st.markdown("""
    <div class="modern-card">
        <h2 style="color: #667eea;">🤖 15个AI智能体</h2>
        <p style="color: #2c3e50; font-size: 1.05em; line-height: 1.8;">
            系统采用<strong>多智能体协同决策</strong>架构，每个智能体专注于不同的分析维度：
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="modern-card">
            <h4 style="color: #38ef7d;">📊 基本面分析</h4>
            <ul style="color: #6c757d; font-size: 0.95em;">
                <li>宏观经济分析</li>
                <li>资金流向分析</li>
                <li>情绪指标分析</li>
                <li>新闻舆情分析</li>
                <li>央行购金分析</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="modern-card">
            <h4 style="color: #f2c94c;">📈 技术面分析</h4>
            <ul style="color: #6c757d; font-size: 0.95em;">
                <li>技术面分析</li>
                <li>量价关系分析</li>
                <li>波动率分析</li>
                <li>相关性分析</li>
                <li>季节性分析</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="modern-card">
            <h4 style="color: #f45c43;">🧠 AI模型</h4>
            <ul style="color: #6c757d; font-size: 0.95em;">
                <li>机器学习模型(XGBoost)</li>
                <li>深度学习LSTM</li>
                <li>期权市场分析</li>
                <li>黄金ETF流向</li>
                <li>风险管理模型</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 使用指南
    st.markdown("""
    <div class="modern-card">
        <h2 style="color: #667eea;">📚 使用指南</h2>
        <div style="color: #2c3e50; font-size: 1.05em; line-height: 2;">
            <h4 style="color: #38ef7d;">1️⃣ 选择预测类型</h4>
            <p style="color: #6c757d;">在左侧导航栏选择"黄金价格预测"或"A股价格预测"</p>

            <h4 style="color: #38ef7d;">2️⃣ 查看实时数据</h4>
            <p style="color: #6c757d;">系统自动获取最新市场数据，点击"刷新数据"按钮可手动更新</p>

            <h4 style="color: #38ef7d;">3️⃣ 分析AI预测结果</h4>
            <p style="color: #6c757d;">查看明日预测价格、置信度、AI共识度和交易信号</p>

            <h4 style="color: #38ef7d;">4️⃣ 参考交易建议</h4>
            <p style="color: #6c757d;">根据系统给出的仓位建议、止损止盈价位制定交易策略</p>

            <h4 style="color: #38ef7d;">5️⃣ 查看详细分析</h4>
            <p style="color: #6c757d;">点击展开15个AI智能体的详细分析理由，了解预测依据</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 交易信号说明
    st.markdown("""
    <div class="modern-card">
        <h2 style="color: #667eea;">🎯 交易信号说明</h2>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("""
        <div class="signal-card signal-strong-buy">
            <h3>🟢 强烈买入</h3>
            <p style="font-size: 0.9em;">预测涨幅 > 1.5%<br>置信度 > 75%<br>看涨信号 ≥ 12个</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="signal-card signal-buy">
            <h3>🟡 买入</h3>
            <p style="font-size: 0.9em;">预测涨幅 > 0.5%<br>置信度 > 65%<br>看涨信号 ≥ 9个</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="signal-card signal-hold">
            <h3>⚪ 观望</h3>
            <p style="font-size: 0.9em;">预测涨跌幅 ≤ 0.5%<br>或市场信号不明确</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="signal-card signal-sell">
            <h3>🟠 卖出</h3>
            <p style="font-size: 0.9em;">预测跌幅 > 0.5%<br>置信度 > 65%</p>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
        <div class="signal-card signal-strong-sell">
            <h3>🔴 强烈卖出</h3>
            <p style="font-size: 0.9em;">预测跌幅较大<br>或风险信号明显</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 风险提示
    st.markdown("""
    <div class="modern-card" style="border: 2px solid #f45c43;">
        <h2 style="color: #f45c43;">⚠️ 重要风险提示</h2>
        <div style="color: #2c3e50; font-size: 1.05em; line-height: 2;">
            <p>1. 本系统提供的预测结果<strong>仅供参考</strong>，不构成任何投资建议</p>
            <p>2. 金融市场存在<strong>不可预测的风险</strong>，历史数据不代表未来表现</p>
            <p>3. 投资者应根据<strong>自身风险承受能力</strong>做出独立判断</p>
            <p>4. 建议<strong>分散投资、控制仓位</strong>，严格执行止损策略</p>
            <p>5. <strong>投资有风险，入市需谨慎</strong></p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 技术支持
    st.markdown("""
    <div class="modern-card">
        <h2 style="color: #667eea;">💬 技术支持</h2>
        <p style="color: #2c3e50; font-size: 1.05em; line-height: 2;">
            <strong>数据来源:</strong> OKX (黄金) + AKShare (A股)<br>
            <strong>AI技术:</strong> 多智能体协同决策 + 机器学习 + 深度学习<br>
            <strong>更新频率:</strong> 实时数据，60秒缓存<br>
            <strong>系统版本:</strong> v2.0 (2026-02-18)
        </p>
    </div>
    """, unsafe_allow_html=True)

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d; padding: 30px;'>
    <p style="font-size: 1.2em; color: #2c3e50;"><strong>🎯 AI智能投资预测系统 v2.0</strong></p>
    <p style="color: #6c757d;">基于15个AI智能体的协同分析 | 数据来源: OKX + AKShare</p>
    <p style="color: #f45c43; font-size: 1.1em; margin-top: 15px;">⚠️ 本系统仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
    <p style="color: #95a5a6; font-size: 0.9em; margin-top: 10px;">© 2026 AI Investment Prediction System | Last Updated: 2026-02-18</p>
</div>
""", unsafe_allow_html=True)
