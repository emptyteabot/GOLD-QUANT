"""
AURUM 短线交易系统 - Streamlit实时监控面板
16-Agent + 5分钟K线 + 快进快出
实时显示：开仓点位、平仓点位、止盈止损、杠杆倍数
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入系统模块
try:
    from okx_client import OKXClient
    from risk_manager import RiskManager
    from agent_16_scalping_system import Agent16ScalpingSystem
    from scalping_engine import ScalpingEngine
    from feishu_notifier import send_signal_push
    import config
except ImportError as e:
    st.error(f"❌ 导入模块失败: {e}")
    st.stop()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 页面配置
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AURUM 短线交易系统",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
# 样式
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Microsoft YaHei', sans-serif !important; }

.stApp {
    background: linear-gradient(135deg, #0b0e11 0%, #1a1f2e 100%);
}

#MainMenu, footer, header { visibility: hidden; }

.metric-card {
    background: linear-gradient(135deg, #1a1f2e 0%, #12161c 100%);
    border: 1px solid rgba(255,215,0,0.1);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
}

.signal-long {
    background: rgba(34, 197, 94, 0.1);
    border-left: 4px solid #22c55e;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}

.signal-short {
    background: rgba(239, 68, 68, 0.1);
    border-left: 4px solid #ef4444;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}

.signal-neutral {
    background: rgba(107, 114, 128, 0.1);
    border-left: 4px solid #6b7280;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}

.agent-item {
    background: rgba(255,215,0,0.05);
    border: 1px solid rgba(255,215,0,0.1);
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    font-size: 13px;
}

.price-display {
    font-size: 32px;
    font-weight: 800;
    background: linear-gradient(90deg, #ffd700, #f0c030, #ffd700);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.status-active {
    color: #22c55e;
    font-weight: 600;
}

.status-inactive {
    color: #6b7280;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 会话状态初始化
# ═══════════════════════════════════════════════════════════════
if 'system_initialized' not in st.session_state:
    st.session_state.system_initialized = False
    st.session_state.okx_client = None
    st.session_state.risk_manager = None
    st.session_state.scalping_engine = None
    st.session_state.agent_system = None
    st.session_state.trade_history = []
    st.session_state.current_analysis = None
    st.session_state.last_update = None
    st.session_state.active_positions = {}

# ═══════════════════════════════════════════════════════════════
# 初始化系统
# ═══════════════════════════════════════════════════════════════
async def initialize_system():
    """初始化交易系统"""
    try:
        okx_client = OKXClient()
        await okx_client.initialize()

        risk_manager = RiskManager()
        scalping_engine = ScalpingEngine(okx_client, risk_manager)
        agent_system = Agent16ScalpingSystem()

        st.session_state.okx_client = okx_client
        st.session_state.risk_manager = risk_manager
        st.session_state.scalping_engine = scalping_engine
        st.session_state.agent_system = agent_system
        st.session_state.system_initialized = True

        return True
    except Exception as e:
        st.error(f"❌ 系统初始化失败: {e}")
        return False

# ═══════════════════════════════════════════════════════════════
# 获取实时数据
# ═══════════════════════════════════════════════════════════════
async def get_live_data():
    """获取实时行情和分析"""
    try:
        if not st.session_state.system_initialized:
            if not await initialize_system():
                return None

        okx_client = st.session_state.okx_client
        scalping_engine = st.session_state.scalping_engine

        # 获取当前价格
        ticker = await okx_client.get_ticker(config.INST_ID)
        if not ticker:
            return None

        current_price = float(ticker['last'])

        # 获取K线数据
        klines_df = await scalping_engine.get_klines(config.INST_ID, limit=100)
        if klines_df is None or len(klines_df) < 20:
            return None

        # 16-Agent分析
        analysis = st.session_state.agent_system.analyze(klines_df, current_price)

        # 获取账户信息
        account = await okx_client.get_account_balance()

        return {
            'current_price': current_price,
            'analysis': analysis,
            'account': account,
            'klines_df': klines_df,
            'timestamp': datetime.now(),
        }

    except Exception as e:
        st.error(f"❌ 获取数据失败: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# 主界面
# ═══════════════════════════════════════════════════════════════
def main():
    # 顶部标题
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("# 🥇 AURUM 短线交易系统")
        st.markdown("**16-Agent讨论 | 5分钟K线 | 快进快出**")

    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("🔄 刷新数据", key="refresh_btn", use_container_width=True):
            st.rerun()

    with col3:
        st.markdown("")
        st.markdown("")
        auto_refresh = st.checkbox("⚡ 自动刷新", value=False)

    st.divider()

    # 获取实时数据
    data = asyncio.run(get_live_data())

    if data is None:
        st.warning("⚠️ 无法获取数据，请检查API连接")
        return

    current_price = data['current_price']
    analysis = data['analysis']
    account = data['account']
    klines_df = data['klines_df']

    # ═══════════════════════════════════════════════════════════════
    # 第一行：账户信息 + 当前价格 + 决策信息
    # ═══════════════════════════════════════════════════════════════
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 💰 账户信息")
        st.metric("总权益", f"${account['total_equity']:.2f}", delta=None)
        st.metric("可用资金", f"${account['available']:.2f}", delta=None)

    with col2:
        st.markdown("### 💹 当前价格")
        st.markdown(f'<div class="price-display">${current_price:.2f}</div>', unsafe_allow_html=True)
        st.metric("24h变化", f"{(float(data.get('ticker', {}).get('change24h', 0)) * 100):.2f}%", delta=None)

    with col3:
        st.markdown("### 🎯 决策信息")

        # 决策信号
        if analysis['action'] == '做多':
            st.markdown('<div class="signal-long">', unsafe_allow_html=True)
            st.markdown(f"**🟢 做多信号**")
        elif analysis['action'] == '做空':
            st.markdown('<div class="signal-short">', unsafe_allow_html=True)
            st.markdown(f"**🔴 做空信号**")
        else:
            st.markdown('<div class="signal-neutral">', unsafe_allow_html=True)
            st.markdown(f"**⚪ 观望**")

        st.markdown(f"综合信号: **{analysis['signal']:.2f}**")
        st.markdown(f"信心度: **{analysis['confidence']:.1%}**")
        st.markdown(f"共识度: **{analysis.get('consensus_ratio', 0):.0%}**")
        st.markdown(f"策略摘要: `{analysis.get('reason_summary', '-')}`")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════
    # 第二行：交易执行信息
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 📊 交易执行信息")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("开仓点位", f"${analysis['entry_price']:.2f}")

    with col2:
        st.metric("止损点位", f"${analysis['stop_loss']:.2f}")

    with col3:
        st.metric("止盈点位", f"${analysis['take_profit']:.2f}")

    with col4:
        st.metric("杠杆倍数", f"{analysis.get('leverage', 0)}x")

    with col5:
        # 计算风险收益比
        if analysis['action'] != '观望':
            risk = abs(analysis['entry_price'] - analysis['stop_loss'])
            reward = abs(analysis['take_profit'] - analysis['entry_price'])
            ratio = reward / risk if risk > 0 else 0
            st.metric("风险收益比", f"1:{ratio:.2f}")
        else:
            st.metric("风险收益比", "-")

    with col6:
        st.metric("建议仓位", f"{analysis.get('position_size_pct', 0):.0%}")

    st.caption(
        f"入场区间 ${analysis.get('entry_min', analysis['entry_price']):.2f} - "
        f"${analysis.get('entry_max', analysis['entry_price']):.2f} | "
        f"TP1 ${analysis.get('take_profit_1', analysis['take_profit']):.2f} | "
        f"TP2 ${analysis.get('take_profit_2', analysis['take_profit']):.2f} | "
        f"预计持仓 {analysis.get('expected_hold_minutes', 0)} 分钟"
    )

    can_push = bool(getattr(config, 'FEISHU_WEBHOOK', ''))
    push_col1, push_col2 = st.columns([1, 3])
    with push_col1:
        if st.button("推送到飞书", use_container_width=True, disabled=not can_push):
            payload = {
                'signal': analysis['signal'],
                'signal_strength': analysis['confidence'],
                'entry_price': analysis['entry_price'],
                'stop_loss': analysis['stop_loss'],
                'take_profit': analysis['take_profit'],
                'position_size': analysis.get('position_size_pct', 0) * account['available'] * max(analysis.get('leverage', 1), 1) / max(analysis['entry_price'], 1),
                'leverage': analysis.get('leverage', 0),
                'risk_reward': analysis.get('risk_reward', 0),
                'max_loss': abs(analysis['entry_price'] - analysis['stop_loss']) * analysis.get('position_size_pct', 0) * account['available'] * max(analysis.get('leverage', 1), 1) / max(analysis['entry_price'], 1),
                'expected_profit': abs(analysis['take_profit'] - analysis['entry_price']) * analysis.get('position_size_pct', 0) * account['available'] * max(analysis.get('leverage', 1), 1) / max(analysis['entry_price'], 1),
                'adx': analysis.get('market_snapshot', {}).get('adx', 0),
                'rsi': analysis.get('market_snapshot', {}).get('rsi', 50),
            }
            if send_signal_push(payload):
                st.success("飞书推送已发送")
            else:
                st.error("飞书推送失败，请检查 .env.trading 的 webhook 配置")
    with push_col2:
        if not can_push:
            st.info("未配置 FEISHU_WEBHOOK_URL，按钮已禁用。")
        else:
            st.info("会推送入场、止损、止盈、杠杆、仓位和风险收益比。")

    st.divider()

    # ═══════════════════════════════════════════════════════════════
    # 第三行：Agent讨论结果
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 🤖 16个Agent讨论结果")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("做多Agent", f"{analysis['long_count']}/16")

    with col2:
        st.metric("做空Agent", f"{analysis['short_count']}/16")

    with col3:
        st.metric("中性Agent", f"{analysis['neutral_count']}/16")

    # Agent详细意见
    st.markdown("#### 各Agent意见详情")

    # 分组显示Agent
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**做多Agent**")
        long_agents = [d for d in analysis['decisions'] if d.signal > 0.3]
        for decision in long_agents:
            st.markdown(f"""
            <div class="agent-item">
            <strong>🟢 {decision.agent_name}</strong><br>
            信号: {decision.signal:.2f} | 信心: {decision.confidence:.1%}<br>
            {decision.reason}
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("**做空Agent**")
        short_agents = [d for d in analysis['decisions'] if d.signal < -0.3]
        for decision in short_agents:
            st.markdown(f"""
            <div class="agent-item">
            <strong>🔴 {decision.agent_name}</strong><br>
            信号: {decision.signal:.2f} | 信心: {decision.confidence:.1%}<br>
            {decision.reason}
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════
    # 第四行：K线图表
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 📈 5分钟K线图表")

    # 创建K线图
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )

    # K线
    fig.add_trace(
        go.Candlestick(
            x=klines_df['timestamp'],
            open=klines_df['open'],
            high=klines_df['high'],
            low=klines_df['low'],
            close=klines_df['close'],
            name='XAU-USDT',
            increasing_line_color='#22c55e',
            decreasing_line_color='#ef4444',
        ),
        row=1, col=1
    )

    # 成交量
    fig.add_trace(
        go.Bar(
            x=klines_df['timestamp'],
            y=klines_df['volume'],
            name='成交量',
            marker_color='rgba(255,215,0,0.3)',
        ),
        row=2, col=1
    )

    # 当前价格线
    fig.add_hline(
        y=current_price,
        line_dash="dash",
        line_color="yellow",
        annotation_text=f"当前: ${current_price:.2f}",
        annotation_position="right",
        row=1, col=1
    )

    # 止损线
    fig.add_hline(
        y=analysis['stop_loss'],
        line_dash="dash",
        line_color="red",
        annotation_text=f"止损: ${analysis['stop_loss']:.2f}",
        annotation_position="right",
        row=1, col=1
    )

    # 止盈线
    fig.add_hline(
        y=analysis['take_profit'],
        line_dash="dash",
        line_color="green",
        annotation_text=f"止盈: ${analysis['take_profit']:.2f}",
        annotation_position="right",
        row=1, col=1
    )

    fig.update_layout(
        title="XAU-USDT 5分钟K线",
        yaxis_title="价格 (USD)",
        xaxis_title="时间",
        template="plotly_dark",
        height=600,
        hovermode='x unified',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════
    # 第五行：性能统计
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 📈 性能统计")

    stats = st.session_state.scalping_engine.get_performance_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总交易数", stats['total_trades'])

    with col2:
        st.metric("胜率", f"{stats['win_rate']:.1%}")

    with col3:
        st.metric("总盈亏", f"${stats['total_pnl']:.2f}")

    with col4:
        st.metric("平均盈亏", f"${stats['avg_pnl_per_trade']:.2f}")

    st.divider()

    # ═══════════════════════════════════════════════════════════════
    # 底部：实时更新时间
    # ═══════════════════════════════════════════════════════════════
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown(f"**最后更新**: {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

    with col2:
        if auto_refresh:
            st.markdown("**状态**: 🟢 自动刷新中")
            st.rerun()

    with col3:
        st.markdown("**系统**: 🟢 运行中")

# ═══════════════════════════════════════════════════════════════
# 运行应用
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
