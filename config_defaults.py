"""
环境变量配置 - 默认值
如果Streamlit Secrets未配置，使用这些默认值
"""
import os

# ==================== 授权配置 ====================
os.environ.setdefault('AUTO_ACTIVATE', '1')
os.environ.setdefault('DEFAULT_TIER', 'PRO')

# ==================== OKX API配置 ====================
os.environ.setdefault('OKX_API_KEY', '')
os.environ.setdefault('OKX_SECRET_KEY', '')
os.environ.setdefault('OKX_PASSPHRASE', '')

# ==================== 飞书Webhook ====================
os.environ.setdefault('FEISHU_WEBHOOK_URL', '')
os.environ.setdefault('FEISHU_MSG_TYPE', 'text')

# ==================== AI配置 ====================
os.environ.setdefault('GEMINI_API_KEY', '')
os.environ.setdefault('GEMINI_BASE_URL', '')
os.environ.setdefault('GEMINI_MODEL', 'gemini-3-pro-preview')

os.environ.setdefault('GROK_API_KEY', '')
os.environ.setdefault('GROK_BASE_URL', '')

os.environ.setdefault('DEEPSEEK_API_KEY', '')
os.environ.setdefault('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
os.environ.setdefault('OPENAI_API_KEY', '')
os.environ.setdefault('OPENAI_BASE_URL', '')
os.environ.setdefault('OPENAI_MODEL', 'gpt-5.4')
os.environ.setdefault('OPENAI_REASONING_EFFORT', 'medium')
os.environ.setdefault('ENABLE_FINAL_REASONER', '1')
os.environ.setdefault('FINAL_REASONER_PROVIDER', 'openai_compat')
os.environ.setdefault('FINAL_REASONER_TIMEOUT_SEC', '45')

os.environ.setdefault('AI_PROVIDER', 'openai_compat')

# ==================== 交易配置 ====================
os.environ.setdefault('POSITION_SIZE_PCT', '0.15')
os.environ.setdefault('MAX_TOTAL_POSITION', '0.75')
os.environ.setdefault('STOP_LOSS_PCT', '0.10')
os.environ.setdefault('TAKE_PROFIT_PCT', '0.30')
os.environ.setdefault('BASE_LEVERAGE', '15')
os.environ.setdefault('MAX_LEVERAGE', '20')

# ==================== 信号配置 ====================
os.environ.setdefault('MIN_CONFIDENCE', '0.60')
os.environ.setdefault('MIN_SIGNAL', '0.25')
os.environ.setdefault('MIN_CONSENSUS', '0.60')

# ==================== 时间框架 ====================
os.environ.setdefault('ENTRY_TIMEFRAME', '3m')
os.environ.setdefault('EXIT_TIMEFRAME', '15m')
os.environ.setdefault('PUSH_INTERVAL', '5m')

print("✅ 环境变量已加载（使用默认配置）")
