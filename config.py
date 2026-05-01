"""
Runtime configuration for AURUM.
Loads secrets from .env.trading (OKX + Feishu).
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.trading relative to this file (robust to CWD)
_ENV_PATH = Path(__file__).resolve().parent / '.env.trading'
load_dotenv(_ENV_PATH)

# ---------- Core Trading ----------
INST_ID = os.getenv('INST_ID', 'XAU-USDT-SWAP')
DATA_SOURCE_EXCHANGE = os.getenv('DATA_SOURCE_EXCHANGE', 'OKX')
EXECUTION_EXCHANGE = os.getenv('EXECUTION_EXCHANGE', 'WEEX')
EXECUTION_SYMBOL = os.getenv('EXECUTION_SYMBOL', 'cmt_xautusdt')
DATA_INST_ID = os.getenv('DATA_INST_ID', 'XAUT-USDT')
FAIR_VALUE_INST_ID = os.getenv('FAIR_VALUE_INST_ID', 'XAU-USDT-SWAP')

# Risk sizing
RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', '0.01'))  # 1% of equity
POSITION_SIZE_PCT = float(os.getenv('POSITION_SIZE_PCT', '0.15'))
MAX_TOTAL_POSITION = float(os.getenv('MAX_TOTAL_POSITION', '0.75'))
STOP_LOSS_PCT = float(os.getenv('STOP_LOSS_PCT', '0.10'))
TAKE_PROFIT_PCT = float(os.getenv('TAKE_PROFIT_PCT', '0.30'))

# Leverage
BASE_LEVERAGE = int(os.getenv('BASE_LEVERAGE', '10'))
MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '20'))
MIN_LEVERAGE = int(os.getenv('MIN_LEVERAGE', '1'))

# Macro thresholds (used in ExecutorAgent)
MACRO_BULL_THRESHOLD = float(os.getenv('MACRO_BULL_THRESHOLD', '50'))
MACRO_NEUTRAL_THRESHOLD = float(os.getenv('MACRO_NEUTRAL_THRESHOLD', '0'))

# Execution mode
TEST_MODE = False
ENABLE_MACRO_ANALYSIS = True
PYRAMIDING_ENABLED = bool(int(os.getenv('PYRAMIDING_ENABLED', '1')))

# Decision thresholds (optimize: reduce overtrading)
MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', '0.45'))
MIN_SIGNAL = float(os.getenv('MIN_SIGNAL', '0.15'))
MIN_CONSENSUS = float(os.getenv('MIN_CONSENSUS', '0.50'))
MIN_TRADE_INTERVAL_MINUTES = int(os.getenv('MIN_TRADE_INTERVAL_MINUTES', '15'))
SKILLS_MIN_SCORE = float(os.getenv('SKILLS_MIN_SCORE', '0.0'))

# Entry/Exit timeframes
ENTRY_TIMEFRAME = os.getenv('ENTRY_TIMEFRAME', '3m')
ENTRY_LIMIT = int(os.getenv('ENTRY_LIMIT', '300'))
EXIT_TIMEFRAME = os.getenv('EXIT_TIMEFRAME', '15m')
EXIT_LIMIT = int(os.getenv('EXIT_LIMIT', '200'))
EXIT_ALT_TIMEFRAME = os.getenv('EXIT_ALT_TIMEFRAME', '1H')

# High-value signal filter (stricter, night push)
HIGH_VALUE_FILTER = bool(int(os.getenv('HIGH_VALUE_FILTER', '1')))
HIGH_VALUE_MIN_MACRO_SCORE = float(os.getenv('HIGH_VALUE_MIN_MACRO_SCORE', '50'))
HIGH_VALUE_MIN_CONFIDENCE = float(os.getenv('HIGH_VALUE_MIN_CONFIDENCE', '0.75'))
HIGH_VALUE_MIN_SIGNAL = float(os.getenv('HIGH_VALUE_MIN_SIGNAL', '0.60'))
HIGH_VALUE_MIN_CONSENSUS = float(os.getenv('HIGH_VALUE_MIN_CONSENSUS', '0.65'))

# Technical defaults (avoid missing attrs)
HURST_RANGE_THRESHOLD = float(os.getenv('HURST_RANGE_THRESHOLD', '0.45'))
HURST_TREND_THRESHOLD = float(os.getenv('HURST_TREND_THRESHOLD', '0.55'))
ADX_RANGE_THRESHOLD = float(os.getenv('ADX_RANGE_THRESHOLD', '20'))
ADX_TREND_THRESHOLD = float(os.getenv('ADX_TREND_THRESHOLD', '25'))
RSI_OVERSOLD = float(os.getenv('RSI_OVERSOLD', '30'))
RSI_OVERBOUGHT = float(os.getenv('RSI_OVERBOUGHT', '70'))

# Stop-loss proximity alerts (signal-only)
STOP_LOSS_ALERT_PRICE = float(os.getenv('STOP_LOSS_ALERT_PRICE', '0'))
STOP_LOSS_ALERT_LEVELS = os.getenv('STOP_LOSS_ALERT_LEVELS', '0.005,0.01,0.015')
STOP_LOSS_ALERT_COOLDOWN_MINUTES = int(os.getenv('STOP_LOSS_ALERT_COOLDOWN_MINUTES', '30'))

# Breakout confirmation alerts (signal-only)
BREAKOUT_ALERT_LEVELS = os.getenv('BREAKOUT_ALERT_LEVELS', '5000,5600')
BREAKOUT_CONFIRM_CANDLES = int(os.getenv('BREAKOUT_CONFIRM_CANDLES', '2'))
BREAKOUT_CONFIRM_INTERVAL = os.getenv('BREAKOUT_CONFIRM_INTERVAL', '5m')
BREAKOUT_VOL_MULTIPLIER = float(os.getenv('BREAKOUT_VOL_MULTIPLIER', '1.5'))
BREAKOUT_RSI_MIN = float(os.getenv('BREAKOUT_RSI_MIN', '55'))
BREAKOUT_ADX_MIN = float(os.getenv('BREAKOUT_ADX_MIN', '25'))
BREAKOUT_ALERT_COOLDOWN_MINUTES = int(os.getenv('BREAKOUT_ALERT_COOLDOWN_MINUTES', '30'))

# Fakeout & momentum exhaustion alerts (signal-only)
FAKEOUT_LOOKBACK_BARS = int(os.getenv('FAKEOUT_LOOKBACK_BARS', '3'))
FAKEOUT_RECLAIM_BARS = int(os.getenv('FAKEOUT_RECLAIM_BARS', '2'))
FAKEOUT_WICK_RATIO = float(os.getenv('FAKEOUT_WICK_RATIO', '2.0'))
EXHAUST_RSI_DROP = float(os.getenv('EXHAUST_RSI_DROP', '8'))
EXHAUST_VOL_RATIO = float(os.getenv('EXHAUST_VOL_RATIO', '0.7'))
EXHAUST_COOLDOWN_MINUTES = int(os.getenv('EXHAUST_COOLDOWN_MINUTES', '30'))

# Liquidation proximity alerts (signal-only)
LIQ_ALERT_LEVELS = os.getenv('LIQ_ALERT_LEVELS', '0.08,0.10')
LIQ_ALERT_COOLDOWN_MINUTES = int(os.getenv('LIQ_ALERT_COOLDOWN_MINUTES', '30'))

# Pyramid settings
PYRAMID_LEVELS = [1.0, 0.5, 0.25]
PYRAMID_MIN_PROFIT_R = float(os.getenv('PYRAMID_MIN_PROFIT_R', '1.0'))

# Day / night windows (UTC)
DAYTIME_START = int(os.getenv('DAYTIME_START', '0'))
DAYTIME_END = int(os.getenv('DAYTIME_END', '12'))
NIGHTTIME_START = int(os.getenv('NIGHTTIME_START', '13'))
NIGHTTIME_END = int(os.getenv('NIGHTTIME_END', '21'))

# Limits
MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '0.05'))  # 5%

# FX rate for reporting
CNY_RATE = float(os.getenv('CNY_RATE', '7.2'))

# Proxies (optional)
HTTP_PROXY = os.getenv('HTTP_PROXY')
HTTPS_PROXY = os.getenv('HTTPS_PROXY')

# OKX
OKX_API_KEY = os.getenv('OKX_API_KEY')
OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY')
OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE')
OKX_BASE_URL = os.getenv('OKX_BASE_URL', 'https://www.okx.com')

# WEEX
WEEX_API_KEY = os.getenv('WEEX_API_KEY')
WEEX_SECRET_KEY = os.getenv('WEEX_SECRET_KEY')
WEEX_PASSPHRASE = os.getenv('WEEX_PASSPHRASE')
WEEX_BASE_URL = os.getenv('WEEX_BASE_URL', 'https://api-contract.weex.com')
WEEX_MARGIN_MODE = int(os.getenv('WEEX_MARGIN_MODE', '1'))  # 1=cross, 3=isolated
WEEX_LOCALE = os.getenv('WEEX_LOCALE', 'zh-CN')
WEEX_AUTOTRADE_ENABLED = bool(int(os.getenv('WEEX_AUTOTRADE_ENABLED', '0')))
WEEX_MAX_POSITION_PCT = float(os.getenv('WEEX_MAX_POSITION_PCT', '0.10'))
WEEX_LIVE_MIN_CONFIDENCE = float(os.getenv('WEEX_LIVE_MIN_CONFIDENCE', '0.72'))
WEEX_MIN_RISK_REWARD = float(os.getenv('WEEX_MIN_RISK_REWARD', '1.5'))
WEEX_MIN_ABS_SIGNAL = float(os.getenv('WEEX_MIN_ABS_SIGNAL', '0.35'))
WEEX_MIN_FAIR_VALUE_Z = float(os.getenv('WEEX_MIN_FAIR_VALUE_Z', '1.2'))
WEEX_MAX_OPEN_POSITIONS = int(os.getenv('WEEX_MAX_OPEN_POSITIONS', '1'))
WEEX_MICRO_ARB_MODE = bool(int(os.getenv('WEEX_MICRO_ARB_MODE', '1')))
WEEX_MICRO_LEVERAGE = int(os.getenv('WEEX_MICRO_LEVERAGE', str(MAX_LEVERAGE)))
WEEX_FIXED_ORDER_QTY = float(os.getenv('WEEX_FIXED_ORDER_QTY', '0'))
WEEX_MICRO_TP_PCT = float(os.getenv('WEEX_MICRO_TP_PCT', '0.0030'))
WEEX_MICRO_SL_PCT = float(os.getenv('WEEX_MICRO_SL_PCT', '0.0022'))
WEEX_MICRO_MIN_SPREAD_PCT = float(os.getenv('WEEX_MICRO_MIN_SPREAD_PCT', '0.0012'))
WEEX_HARD_MAX_LEVERAGE = int(os.getenv('WEEX_HARD_MAX_LEVERAGE', str(WEEX_MICRO_LEVERAGE)))
WEEX_MIN_AVAILABLE_USDT = float(os.getenv('WEEX_MIN_AVAILABLE_USDT', '25'))
WEEX_MIN_LIQUIDATION_BUFFER_PCT = float(os.getenv('WEEX_MIN_LIQUIDATION_BUFFER_PCT', '0.01'))
WEEX_BLOCK_ON_EXISTING_POSITION = bool(int(os.getenv('WEEX_BLOCK_ON_EXISTING_POSITION', '1')))
WEEX_REQUIRE_TPSL_FOR_EXISTING_POSITION = bool(int(os.getenv('WEEX_REQUIRE_TPSL_FOR_EXISTING_POSITION', '1')))
WEEX_DAILY_RISK_STATE_PATH = os.getenv('WEEX_DAILY_RISK_STATE_PATH', '_tmp\\weex_daily_risk_state.json')

# Feishu
FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK_URL')
FEISHU_MSG_TYPE = os.getenv('FEISHU_MSG_TYPE', 'interactive')
FEISHU_FORCE_ASCII = bool(int(os.getenv('FEISHU_FORCE_ASCII', '0')))
LOCAL_CHINESE_LOG = bool(int(os.getenv('LOCAL_CHINESE_LOG', '1')))
LOCAL_CHINESE_LOG_PATH = os.getenv('LOCAL_CHINESE_LOG_PATH', '_tmp\\feishu_zh.log')

# Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL')
GEMINI_MODEL = os.getenv('GEMINI_MODEL')
PUSH_INTERVAL = os.getenv('PUSH_INTERVAL', '')
PUSH_ON_SIGNAL_ONLY = bool(int(os.getenv('PUSH_ON_SIGNAL_ONLY', '0')))

# OpenAI-compatible LLM agents
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5.4')
OPENAI_REASONING_EFFORT = os.getenv('OPENAI_REASONING_EFFORT', 'medium')
ENABLE_LLM_AGENTS = bool(int(os.getenv('ENABLE_LLM_AGENTS', '1')))
OPENAI_AGENT_TIMEOUT_SEC = int(os.getenv('OPENAI_AGENT_TIMEOUT_SEC', '25'))
OPENAI_AGENT_MAX_WORKERS = int(os.getenv('OPENAI_AGENT_MAX_WORKERS', '8'))

# Final reasoning gate
ENABLE_FINAL_REASONER = bool(int(os.getenv('ENABLE_FINAL_REASONER', '1')))
FINAL_REASONER_PROVIDER = os.getenv('FINAL_REASONER_PROVIDER', 'openai_compat').strip().lower()
FINAL_REASONER_TIMEOUT_SEC = int(os.getenv('FINAL_REASONER_TIMEOUT_SEC', os.getenv('DEEPSEEK_TIMEOUT_SEC', '45')))

# Optional legacy DeepSeek provider
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner')

# Failsafe: signal-only mode (no auto trade at night)
SIGNAL_ONLY = bool(int(os.getenv('SIGNAL_ONLY', '1')))
