"""
环境变量配置 - 默认值
如果Streamlit Secrets未配置，使用这些默认值
"""
import os

# ==================== 授权配置 ====================
os.environ.setdefault('AUTO_ACTIVATE', '1')
os.environ.setdefault('DEFAULT_TIER', 'PRO')

# ==================== OKX API配置 ====================
os.environ.setdefault('OKX_API_KEY', 'd82bdcdb-fdd1-432f-bf53-8e22a010b1a4')
os.environ.setdefault('OKX_SECRET_KEY', '672D88347AC17326E1726EC1DCAA225C')
os.environ.setdefault('OKX_PASSPHRASE', 'Cyh20060817.')

# ==================== 飞书Webhook ====================
os.environ.setdefault('FEISHU_WEBHOOK_URL', 'https://open.feishu.cn/open-apis/bot/v2/hook/00a2b2ea-2d3d-4ae4-aee2-89c71663b31c')
os.environ.setdefault('FEISHU_MSG_TYPE', 'text')

# ==================== AI配置 ====================
os.environ.setdefault('GEMINI_API_KEY', 'sk-8CIztQDwnxAM1GnClTsC0v79188tF7HqGAXb3ev2G9QKkLLS')
os.environ.setdefault('GEMINI_BASE_URL', 'https://hk.12ai.org/v1')
os.environ.setdefault('GEMINI_MODEL', 'gemini-3-pro-preview')

os.environ.setdefault('GROK_API_KEY', 'sk-cfC41IpV5W4t9ok1SK1tyH60i1L0L9yvmRIyS8b5lNfTzbif')
os.environ.setdefault('GROK_BASE_URL', 'https://api.x.ai/v1')

os.environ.setdefault('DEEPSEEK_API_KEY', 'sk-f3402e91bf494300856892bc7e79854b')
os.environ.setdefault('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')

os.environ.setdefault('AI_PROVIDER', 'grok')

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
