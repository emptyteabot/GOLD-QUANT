"""
诊断工具 - 检查网络和 API 连接
"""
import asyncio
import aiohttp


async def test_network():
    """测试基本网络连接"""
    print("\n🔍 诊断网络连接...\n")
    
    test_urls = [
        ("百度", "https://www.baidu.com"),
        ("Binance", "https://api.binance.com/api/v3/ping"),
        ("OKX", "https://www.okx.com"),
    ]
    
    for name, url in test_urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        print(f"✅ {name}: 连接成功")
                    else:
                        print(f"⚠️ {name}: HTTP {response.status}")
        except asyncio.TimeoutError:
            print(f"❌ {name}: 连接超时")
        except Exception as e:
            print(f"❌ {name}: {str(e)[:50]}")


async def test_binance_detailed():
    """详细测试 Binance API"""
    print("\n🔍 详细测试 Binance...\n")
    
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"
        print(f"请求 URL: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"HTTP 状态码: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"返回数据: {data}")
                    price = float(data.get("price", 0))
                    print(f"✅ 黄金价格: ${price:,.2f}/盎司")
                else:
                    text = await response.text()
                    print(f"错误响应: {text[:200]}")
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()


async def test_okx_detailed():
    """详细测试 OKX API"""
    print("\n🔍 详细测试 OKX...\n")
    
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=PAXG-USDT"
        print(f"请求 URL: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"HTTP 状态码: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"返回数据: {data}")
                    
                    if data.get("code") == "0":
                        ticker_data = data.get("data", [])
                        if ticker_data:
                            price = float(ticker_data[0].get("last", 0))
                            print(f"✅ 黄金价格: ${price:,.2f}/盎司")
                    else:
                        print(f"API 错误: {data}")
                else:
                    text = await response.text()
                    print(f"错误响应: {text[:200]}")
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("=" * 70)
    print("🔧 黄金监控系统 - 网络诊断工具")
    print("=" * 70)
    
    # 测试基本网络
    await test_network()
    
    # 详细测试 Binance
    await test_binance_detailed()
    
    # 详细测试 OKX
    await test_okx_detailed()
    
    print("\n" + "=" * 70)
    print("✅ 诊断完成！")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())



