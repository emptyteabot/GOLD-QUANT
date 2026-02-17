"""
系统测试脚本 - 诊断和验证
"""
import asyncio
import sys
from datetime import datetime

print("=" * 70)
print("🔍 系统诊断测试")
print("=" * 70)
print()

# ==================== 测试1: Python环境 ====================
print("【测试1】Python环境")
print(f"  Python版本: {sys.version}")
print(f"  ✅ 通过")
print()

# ==================== 测试2: 依赖包 ====================
print("【测试2】依赖包检查")
required_packages = {
    'aiohttp': 'aiohttp',
    'ccxt': 'ccxt',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'dotenv': 'python-dotenv'
}

missing = []
for module, package in required_packages.items():
    try:
        __import__(module)
        print(f"  ✅ {package}")
    except ImportError:
        print(f"  ❌ {package} - 缺失")
        missing.append(package)

if missing:
    print(f"\n  ⚠️ 缺失包: {', '.join(missing)}")
    print(f"  运行: pip install {' '.join(missing)}")
else:
    print(f"\n  ✅ 所有依赖包已安装")
print()

# ==================== 测试3: 配置文件 ====================
print("【测试3】配置文件")
import os
from dotenv import load_dotenv

load_dotenv()

feishu_url = os.getenv('FEISHU_WEBHOOK_URL', '')
pushplus_token = os.getenv('PUSHPLUS_TOKEN', '')

if feishu_url:
    print(f"  ✅ 飞书Webhook已配置")
else:
    print(f"  ⚠️ 飞书Webhook未配置")

if pushplus_token:
    print(f"  ✅ PushPlus已配置")
else:
    print(f"  ⚠️ PushPlus未配置")

if not feishu_url and not pushplus_token:
    print(f"\n  ❌ 至少需要配置一个通知渠道")
else:
    print(f"\n  ✅ 通知渠道已配置")
print()

# ==================== 测试4: 网络连接 ====================
print("【测试4】网络连接")

async def test_network():
    import aiohttp
    
    test_urls = [
        ('Binance API', 'https://api.binance.com/api/v3/ping'),
        ('Yahoo Finance', 'https://query1.finance.yahoo.com/v8/finance/chart/GC=F'),
    ]
    
    async with aiohttp.ClientSession() as session:
        for name, url in test_urls:
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        print(f"  ✅ {name}")
                    else:
                        print(f"  ⚠️ {name} - 状态码: {resp.status}")
            except Exception as e:
                print(f"  ❌ {name} - {str(e)[:50]}")

asyncio.run(test_network())
print()

# ==================== 测试5: 价格获取 ====================
print("【测试5】价格获取")

async def test_price():
    import ccxt.async_support as ccxt
    
    # 测试Binance
    try:
        exchange = ccxt.binance()
        ticker = await exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        print(f"  ✅ Binance - BTC价格: ${price:,.2f}")
        await exchange.close()
    except Exception as e:
        print(f"  ❌ Binance - {str(e)[:50]}")
    
    # 测试Yahoo Finance (黄金)
    try:
        import aiohttp
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
        params = {'interval': '1m', 'range': '1d'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'chart' in data and 'result' in data['chart']:
                        result = data['chart']['result'][0]
                        if 'meta' in result and 'regularMarketPrice' in result['meta']:
                            price = result['meta']['regularMarketPrice']
                            print(f"  ✅ Yahoo Finance - 黄金价格: ${price:,.2f}")
                        else:
                            print(f"  ⚠️ Yahoo Finance - 数据格式异常")
                    else:
                        print(f"  ⚠️ Yahoo Finance - 响应格式异常")
                else:
                    print(f"  ❌ Yahoo Finance - 状态码: {resp.status}")
    except Exception as e:
        print(f"  ❌ Yahoo Finance - {str(e)[:50]}")

asyncio.run(test_price())
print()

# ==================== 测试6: 飞书推送 ====================
print("【测试6】飞书推送")

async def test_feishu():
    if not feishu_url:
        print(f"  ⚠️ 跳过 - 未配置飞书Webhook")
        return
    
    import aiohttp
    
    payload = {
        "msg_type": "text",
        "content": {
            "text": f"🧪 测试消息 - {datetime.now().strftime('%H:%M:%S')}"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(feishu_url, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get('code') == 0:
                        print(f"  ✅ 飞书推送成功 - 请检查飞书群")
                    else:
                        print(f"  ❌ 飞书推送失败 - {result}")
                else:
                    print(f"  ❌ 飞书推送失败 - 状态码: {resp.status}")
    except Exception as e:
        print(f"  ❌ 飞书推送异常 - {str(e)[:50]}")

asyncio.run(test_feishu())
print()

# ==================== 测试7: 核心模块 ====================
print("【测试7】核心模块")

modules = [
    'price_monitor',
    'wechat_notifier',
    'leading_indicators',
    'config_ultimate',
    'main_ultimate'
]

for module in modules:
    try:
        __import__(module)
        print(f"  ✅ {module}")
    except Exception as e:
        print(f"  ❌ {module} - {str(e)[:50]}")

print()

# ==================== 总结 ====================
print("=" * 70)
print("📊 诊断完成")
print("=" * 70)
print()
print("💡 建议:")
print("  1. 如果网络连接失败，检查防火墙/代理设置")
print("  2. 如果价格获取失败，系统会自动重试")
print("  3. 如果飞书推送失败，检查webhook地址是否正确")
print("  4. 如果模块导入失败，运行: pip install -r requirements.txt")
print()
print("=" * 70)
