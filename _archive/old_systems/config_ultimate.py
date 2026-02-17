"""
实盘配置文件 - 所有关键参数
"""
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== 交易模式 ====================

TRADING_MODE = "live"  # live/paper/backtest
# live: 实盘模式（真金白银）
# paper: 模拟盘（测试用）
# backtest: 回测模式

# ==================== 风险控制 ====================

# 仓位管理
MAX_POSITION = 0.3          # 最大仓位 30%
MIN_POSITION = 0.05         # 最小仓位 5%
POSITION_SCALE_FACTOR = 1.0 # 仓位缩放因子

# 止损止盈
STOP_LOSS = 0.02           # 止损 2%
TAKE_PROFIT = 0.05         # 止盈 5%
TRAILING_STOP = True       # 是否启用移动止损
TRAILING_STOP_DISTANCE = 0.015  # 移动止损距离 1.5%

# 风险限制
STOP_LOSS_RULES = {
    "single_trade": 0.02,      # 单笔最大亏损 2%
    "daily_max": 0.05,         # 单日最大亏损 5%
    "weekly_max": 0.10,        # 单周最大亏损 10%
    "drawdown_limit": 0.10     # 最大回撤 10%
}

# 资金管理
INITIAL_CAPITAL = 100000   # 初始资金（美元）
LEVERAGE = 1               # 杠杆倍数（1=不使用杠杆）
RESERVE_RATIO = 0.2        # 保留资金比例 20%

# ==================== 领先指标阈值 ====================

# 美元指数 (DXY)
THRESHOLD_DXY_SPIKE = 0.003      # DXY 涨 0.3% → 黄金即将跌
THRESHOLD_DXY_CRASH = -0.003     # DXY 跌 0.3% → 黄金即将涨

# 美债收益率 (US10Y)
THRESHOLD_US10Y_SPIKE = 0.02     # 收益率涨 2bp
THRESHOLD_US10Y_DROP = -0.02     # 收益率跌 2bp

# VIX 恐慌指数
THRESHOLD_VIX_SPIKE = 0.05       # VIX 涨 5%
THRESHOLD_VIX_DROP = -0.05       # VIX 跌 5%

# 订单簿失衡
THRESHOLD_ORDERBOOK_IMBALANCE = 0.7  # 订单簿失衡 70%

# 推特情绪
THRESHOLD_TWITTER_SENTIMENT = -7     # 推特情绪 -7
THRESHOLD_TWITTER_POSITIVE = 7       # 推特情绪 +7

# ==================== 信号生成 ====================

# 信号强度阈值
MIN_SIGNAL_STRENGTH = 0.5    # 最小信号强度 50%
STRONG_SIGNAL_THRESHOLD = 0.8  # 强信号阈值 80%

# 信号确认
SIGNAL_CONFIRMATION_PERIOD = 3  # 信号确认周期（分钟）
MIN_INDICATORS_AGREE = 2        # 最少需要几个指标同意

# 信号权重
INDICATOR_WEIGHTS = {
    'dxy': 0.35,           # 美元指数权重 35%
    'orderbook': 0.30,     # 订单簿权重 30%
    'us10y': 0.20,         # 美债权重 20%
    'vix': 0.15,           # VIX权重 15%
    'twitter': 0.10,       # 推特权重 10%（可选）
    'ml_prediction': 0.25  # 机器学习预测权重 25%
}

# ==================== 策略配置 ====================

# Dual Thrust 策略
DUAL_THRUST_CONFIG = {
    'k1': 0.5,              # 上轨系数
    'k2': 0.5,              # 下轨系数
    'period': 20,           # 计算周期
    'adaptive': True        # 是否自适应调整K值
}

# 均值回归策略
MEAN_REVERSION_CONFIG = {
    'lookback': 20,         # 回看周期
    'entry_threshold': 2.0, # 入场阈值（标准差）
    'exit_threshold': 0.5,  # 出场阈值（标准差）
    'use_bollinger': True   # 是否使用布林带
}

# 动量策略
MOMENTUM_CONFIG = {
    'fast_period': 12,      # 快速周期
    'slow_period': 26,      # 慢速周期
    'signal_period': 9,     # 信号周期
    'rsi_period': 14,       # RSI周期
    'rsi_overbought': 70,   # RSI超买
    'rsi_oversold': 30      # RSI超卖
}

# 策略权重（多策略投票）
STRATEGY_WEIGHTS = {
    'dual_thrust': 0.4,
    'mean_reversion': 0.3,
    'momentum': 0.3
}

# ==================== 数据源配置 ====================

# 交易所
EXCHANGES = {
    'primary': 'binance',    # 主要交易所
    'backup': ['okx', 'bybit']  # 备用交易所
}

# 交易对
TRADING_PAIRS = {
    'gold': 'XAU/USDT',
    'gold_futures': 'XAUUSDT'
}

# 数据更新频率
DATA_UPDATE_INTERVAL = 5     # 数据更新间隔（秒）
ORDERBOOK_UPDATE_INTERVAL = 2  # 订单簿更新间隔（秒）
LEADING_INDICATOR_INTERVAL = 10  # 领先指标更新间隔（秒）

# K线周期
KLINE_PERIODS = ['1m', '5m', '15m', '1h', '4h', '1d']
PRIMARY_TIMEFRAME = '5m'     # 主要时间周期

# ==================== 机器学习配置 ====================

# LSTM 价格预测
LSTM_CONFIG = {
    'sequence_length': 60,   # 序列长度
    'prediction_horizon': 5, # 预测未来5分钟
    'hidden_size': 128,      # 隐藏层大小
    'num_layers': 2,         # LSTM层数
    'dropout': 0.2,          # Dropout率
    'learning_rate': 0.001,  # 学习率
    'batch_size': 32,        # 批次大小
    'epochs': 50             # 训练轮数
}

# XGBoost 信号分类
XGBOOST_CONFIG = {
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'objective': 'multi:softmax',
    'num_class': 3,          # 3类：做多/观望/做空
    'eval_metric': 'mlogloss'
}

# 模型更新
MODEL_RETRAIN_INTERVAL = 7   # 模型重训练间隔（天）
MIN_TRAINING_SAMPLES = 1000  # 最少训练样本数

# ==================== 通知配置 ====================

# 飞书通知
FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', '')
FEISHU_ENABLED = bool(FEISHU_WEBHOOK_URL)

# 微信通知（PushPlus）
PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN', '')
WECHAT_ENABLED = bool(PUSHPLUS_TOKEN)

# 通知级别
NOTIFICATION_LEVELS = {
    'critical': True,   # 紧急通知（强信号、止损触发）
    'warning': True,    # 警告通知（中等信号）
    'info': False,      # 信息通知（系统状态）
    'debug': False      # 调试通知
}

# 通知频率限制
MAX_NOTIFICATIONS_PER_HOUR = 10  # 每小时最多通知次数
MIN_NOTIFICATION_INTERVAL = 300  # 最小通知间隔（秒）

# ==================== API 密钥 ====================

# Grok API（用于新闻分析）
GROK_API_KEY = os.getenv('GROK_API_KEY', '')
GROK_ENABLED = bool(GROK_API_KEY)

# DeepSeek API（用于情绪分析）
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_ENABLED = bool(DEEPSEEK_API_KEY)

# Twitter API（可选）
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
TWITTER_ENABLED = bool(TWITTER_BEARER_TOKEN)

# ==================== 日志配置 ====================

LOG_LEVEL = "INFO"  # DEBUG/INFO/WARNING/ERROR/CRITICAL
LOG_FILE = "logs/system.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# 日志内容
LOG_TRADES = True           # 记录交易
LOG_SIGNALS = True          # 记录信号
LOG_INDICATORS = True       # 记录指标
LOG_PERFORMANCE = True      # 记录性能

# ==================== 性能监控 ====================

# 性能指标
PERFORMANCE_METRICS = {
    'sharpe_ratio': True,       # 夏普比率
    'max_drawdown': True,       # 最大回撤
    'win_rate': True,           # 胜率
    'profit_factor': True,      # 盈亏比
    'avg_trade_duration': True  # 平均持仓时间
}

# 性能报告
DAILY_REPORT = True         # 每日报告
WEEKLY_REPORT = True        # 每周报告
MONTHLY_REPORT = True       # 每月报告

# ==================== 安全配置 ====================

# 交易限制
MAX_TRADES_PER_DAY = 20     # 每日最大交易次数
MAX_TRADES_PER_HOUR = 5     # 每小时最大交易次数
MIN_TRADE_INTERVAL = 300    # 最小交易间隔（秒）

# 异常检测
ENABLE_ANOMALY_DETECTION = True  # 启用异常检测
PRICE_SPIKE_THRESHOLD = 0.05     # 价格异常波动阈值 5%
VOLUME_SPIKE_THRESHOLD = 3.0     # 成交量异常倍数

# 熔断机制
CIRCUIT_BREAKER = {
    'enabled': True,
    'daily_loss_limit': 0.05,    # 单日亏损5%触发熔断
    'consecutive_losses': 5,      # 连续亏损5次触发熔断
    'cooldown_period': 3600       # 熔断冷却期（秒）
}

# ==================== 回测配置 ====================

BACKTEST_CONFIG = {
    'start_date': '2024-01-01',
    'end_date': '2024-12-31',
    'initial_capital': 100000,
    'commission': 0.001,         # 手续费 0.1%
    'slippage': 0.0005,          # 滑点 0.05%
}

# ==================== 高级功能 ====================

# 自适应参数调整
ADAPTIVE_PARAMETERS = True   # 根据市场状态自动调整参数
MARKET_REGIME_DETECTION = True  # 市场状态检测（趋势/震荡）

# 多时间框架分析
MULTI_TIMEFRAME_ANALYSIS = True
TIMEFRAME_WEIGHTS = {
    '1m': 0.1,
    '5m': 0.3,
    '15m': 0.3,
    '1h': 0.2,
    '4h': 0.1
}

# 相关性分析
CORRELATION_ANALYSIS = True
CORRELATION_ASSETS = ['BTC/USDT', 'ETH/USDT', 'SPX', 'DXY']

# ==================== 调试模式 ====================

DEBUG_MODE = False          # 调试模式
DRY_RUN = False            # 空运行（不实际交易）
VERBOSE_LOGGING = False    # 详细日志

# ==================== 配置验证 ====================

def validate_config():
    """验证配置是否正确"""
    errors = []
    
    # 检查必要的API密钥
    if TRADING_MODE == 'live':
        if not FEISHU_WEBHOOK_URL and not PUSHPLUS_TOKEN:
            errors.append("实盘模式必须配置飞书或微信通知")
    
    # 检查风险参数
    if MAX_POSITION > 1.0 or MAX_POSITION < 0:
        errors.append("最大仓位必须在0-1之间")
    
    if STOP_LOSS <= 0 or STOP_LOSS > 0.5:
        errors.append("止损比例必须在0-0.5之间")
    
    # 检查信号权重
    total_weight = sum(INDICATOR_WEIGHTS.values())
    if abs(total_weight - 1.0) > 0.01:
        errors.append(f"指标权重总和必须为1.0，当前为{total_weight}")
    
    if errors:
        print("❌ 配置错误:")
        for error in errors:
            print(f"  • {error}")
        return False
    
    print("✅ 配置验证通过")
    return True


def print_config_summary():
    """打印配置摘要"""
    print("=" * 70)
    print("⚙️  系统配置摘要")
    print("=" * 70)
    print()
    print(f"交易模式: {TRADING_MODE}")
    print(f"初始资金: ${INITIAL_CAPITAL:,.0f}")
    print(f"最大仓位: {MAX_POSITION*100:.0f}%")
    print(f"止损: {STOP_LOSS*100:.0f}%")
    print(f"止盈: {TAKE_PROFIT*100:.0f}%")
    print()
    print("通知渠道:")
    print(f"  • 飞书: {'✅' if FEISHU_ENABLED else '❌'}")
    print(f"  • 微信: {'✅' if WECHAT_ENABLED else '❌'}")
    print()
    print("数据源:")
    print(f"  • Grok API: {'✅' if GROK_ENABLED else '❌'}")
    print(f"  • DeepSeek API: {'✅' if DEEPSEEK_ENABLED else '❌'}")
    print(f"  • Twitter API: {'✅' if TWITTER_ENABLED else '❌'}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    validate_config()
    print_config_summary()
