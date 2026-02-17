"""
测试飞书机器人功能
"""
import asyncio
import os
from dotenv import load_dotenv
from feishu_bot import FeishuBot

load_dotenv()


async def test_all_features():
    """测试所有功能"""
    webhook = os.getenv("FEISHU_WEBHOOK_URL", "")
    
    if not webhook:
        print("❌ 未配置 FEISHU_WEBHOOK_URL")
        print("\n请在 .env 文件中添加：")
        print("FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-key")
        return
    
    bot = FeishuBot(webhook)
    
    print("🧪 开始测试飞书机器人功能\n")
    print("=" * 60)
    
    # 测试 1: 欢迎消息
    print("\n1️⃣ 测试欢迎消息...")
    success = await bot.send_welcome()
    print(f"   {'✅ 成功' if success else '❌ 失败'}")
    await asyncio.sleep(3)
    
    # 测试 2: 价格更新
    print("\n2️⃣ 测试价格更新...")
    success = await bot.send_price_update(
        symbol="BTC/USDT",
        price=95234.56,
        change_1m=-0.0023,
        change_5m=-0.0067,
        volume_24h=1234567890
    )
    print(f"   {'✅ 成功' if success else '❌ 失败'}")
    await asyncio.sleep(3)
    
    # 测试 3: 急跌预警
    print("\n3️⃣ 测试急跌预警...")
    success = await bot.send_alert(
        alert_type="price",
        title="BTC/USDT 急跌预警",
        content="""⚠️ **价格急速下跌！**

**交易对**: BTC/USDT
**当前价格**: $95,234.56
**1分钟跌幅**: -0.5%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 **建议**
• 检查持仓风险
• 关注市场动态
• 考虑止损策略
""",
        severity="danger"
    )
    print(f"   {'✅ 成功' if success else '❌ 失败'}")
    await asyncio.sleep(3)
    
    # 测试 4: 急涨预警
    print("\n4️⃣ 测试急涨预警...")
    success = await bot.send_alert(
        alert_type="price",
        title="ETH/USDT 急涨预警",
        content="""🚀 **价格快速上涨！**

**交易对**: ETH/USDT
**当前价格**: $3,456.78
**1分钟涨幅**: +0.8%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 **建议**
• 关注突破确认
• 警惕假突破回落
• 考虑止盈策略
""",
        severity="warning"
    )
    print(f"   {'✅ 成功' if success else '❌ 失败'}")
    await asyncio.sleep(3)
    
    # 测试 5: 帮助信息
    print("\n5️⃣ 测试帮助信息...")
    success = await bot.send_help()
    print(f"   {'✅ 成功' if success else '❌ 失败'}")
    await asyncio.sleep(3)
    
    # 测试 6: 每日报告
    print("\n6️⃣ 测试每日报告...")
    success = await bot.send_daily_report(
        date="2026-02-01",
        price_open=95000.00,
        price_close=95234.56,
        price_high=96500.00,
        price_low=94200.00,
        change_pct=0.0025,
        news_count=15,
        alert_count=3,
        summary="今日市场整体平稳，BTC 小幅上涨 0.25%。美联储官员讲话偏鸽派，市场情绪乐观。建议继续持有，关注周末行情。"
    )
    print(f"   {'✅ 成功' if success else '❌ 失败'}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！请检查飞书群消息")
    print("\n💡 如果所有消息都收到了，说明配置正确！")
    print("💡 接下来可以运行: python main_interactive.py")


if __name__ == "__main__":
    asyncio.run(test_all_features())
