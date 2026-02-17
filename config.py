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

# Failsafe: signal-only mode (no auto trade at night)
SIGNAL_ONLY = True
