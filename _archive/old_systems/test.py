"""
测试脚本 - 验证各模块功能
"""
import asyncio
from config import config
from notifier import notifier
from price_monitor import PriceMonitor
from news_analyzer import NewsAnalyzer


async def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("🧪 测试1: 配置加载")
    print("=" * 60)
    
    print(f"✓ DeepSeek API Key: {config.DEEPSEEK_API_KEY[:20]}..." if config.DEEPSEEK_API_KEY else "✗ 未配置")
    print(f"✓ 飞书 Webhook: {config.FEISHU_WEBHOOK[:50]}..." if config.FEISHU_WEBHOOK else "✗ 未配置")
    print(f"✓ 1分钟跌幅阈值: {config.THRESHOLD_PRICE_DROP_1M:.2%}")
    print(f"✓ 情感分数阈值: {config.THRESHOLD_SENTIMENT}")
    print(f"✓ 新闻源数量: {len(config.NEWS_FEEDS)}")
    
    is_valid = config.validate()
    print(f"\n配置验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    return is_valid


async def test_feishu():
    """测试飞书推送"""
    print("\n" + "=" * 60)
    print("🧪 测试2: 飞书推送")
    print("=" * 60)
    
    if not config.FEISHU_WEBHOOK:
        print("❌ 跳过: 未配置飞书 Webhook")
        return False
    
    print("📤 发送测试消息...")
    success = await notifier.send_alert(
        title="系统测试",
        content="这是一条测试消息,如果你看到这条消息,说明飞书推送配置正确! ✅",
        alert_type="info"
    )
    
    if success:
        print("✅ 飞书推送成功! 请检查你的飞书群")
    else:
        print("❌ 飞书推送失败,请检查 Webhook URL 和安全设置")
    
    return success


async def test_price_monitor():
    """测试价格监控"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 价格监控")
    print("=" * 60)
    
    monitor = PriceMonitor()
    
    try:
        print(f"📊 获取 {config.GOLD_SYMBOL} 价格...")
        price = await monitor.fetch_current_price()
        
        if price:
            print(f"✅ 当前价格: ${price:.2f}")
            
            # 模拟收集几个价格点
            print("\n📈 收集价格数据 (15秒)...")
            for i in range(5):
                price = await monitor.fetch_current_price()
                if price:
                    from datetime import datetime
                    monitor.price_history.append(
                        monitor.PriceData(price, datetime.now().timestamp())
                    )
                    print(f"   [{i+1}/5] ${price:.2f}")
                await asyncio.sleep(3)
            
            # 计算涨跌幅
            change = monitor.calculate_change(15)
            if change is not None:
                print(f"\n✅ 15秒涨跌幅: {change:+.2%}")
            
            return True
        else:
            print("❌ 无法获取价格")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        await monitor.close()


async def test_news_analyzer():
    """测试新闻分析"""
    print("\n" + "=" * 60)
    print("🧪 测试4: 新闻分析 (DeepSeek)")
    print("=" * 60)
    
    if not config.DEEPSEEK_API_KEY:
        print("❌ 跳过: 未配置 DeepSeek API Key")
        return False
    
    analyzer = NewsAnalyzer()
    
    # 测试用例
    test_cases = [
        ("利空", "美联储主席鲍威尔表示通胀仍然顽固,可能需要进一步加息"),
        ("利多", "地缘冲突升级,避险情绪推动黄金大涨"),
        ("中性", "黄金技术分析: 日线图显示三角形整理形态")
    ]
    
    print("📰 测试情感分析:\n")
    
    all_success = True
    for label, text in test_cases:
        print(f"[{label}] {text}")
        result = await analyzer.analyze_sentiment(text)
        
        if result:
            score = result.get('score', 0)
            summary = result.get('summary', '')
            is_urgent = result.get('is_urgent', False)
            
            emoji = "🔴" if score < -5 else "🟡" if score < 0 else "🟢"
            urgent_flag = "⚡" if is_urgent else ""
            
            print(f"   {emoji} 分数: {score:+d}/10 {urgent_flag}")
            print(f"   💬 分析: {summary}\n")
        else:
            print(f"   ❌ 分析失败\n")
            all_success = False
        
        await asyncio.sleep(1)  # 避免 API 限流
    
    return all_success


async def test_news_feed():
    """测试新闻抓取"""
    print("\n" + "=" * 60)
    print("🧪 测试5: 新闻抓取 (RSS)")
    print("=" * 60)
    
    analyzer = NewsAnalyzer()
    
    print(f"📡 抓取新闻源: {config.NEWS_FEEDS[0]}\n")
    
    news_list = await analyzer.fetch_news_from_feed(config.NEWS_FEEDS[0])
    
    if news_list:
        print(f"✅ 成功抓取 {len(news_list)} 条黄金相关新闻:\n")
        for i, (title, link, published) in enumerate(news_list[:3], 1):
            print(f"{i}. {title}")
            print(f"   🔗 {link}")
            print(f"   📅 {published}\n")
        return True
    else:
        print("❌ 未抓取到新闻 (可能是网络问题或新闻源暂无黄金相关内容)")
        return False


async def main():
    """运行所有测试"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║     🧪 黄金崩盘预警系统 - 功能测试                        ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print("\n")
    
    results = {}
    
    # 测试1: 配置
    results['config'] = await test_config()
    
    # 测试2: 飞书推送
    if results['config']:
        results['feishu'] = await test_feishu()
        await asyncio.sleep(2)
    
    # 测试3: 价格监控
    results['price'] = await test_price_monitor()
    await asyncio.sleep(2)
    
    # 测试4: 新闻分析
    if results['config']:
        results['news_analysis'] = await test_news_analyzer()
        await asyncio.sleep(2)
    
    # 测试5: 新闻抓取
    results['news_feed'] = await test_news_feed()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name.ljust(20)}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过! 系统可以正常运行")
        print("\n💡 下一步: 运行 python main.py 启动监控系统")
    else:
        print("⚠️  部分测试失败,请检查配置和网络连接")
        print("\n💡 提示:")
        print("   1. 确保 .env 文件配置正确")
        print("   2. 检查网络是否可以访问 Binance 和 DeepSeek API")
        print("   3. 验证飞书 Webhook URL 和安全设置")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())




