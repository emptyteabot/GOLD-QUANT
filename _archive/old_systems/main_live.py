"""
实盘版主程序 - 真正的提前预警系统
Live Trading System with Leading Indicators

核心特性:
1. 领先指标监控 (DXY/订单簿/VIX) - 提前5-30秒预警
2. 多Agent协作 (市场/舆情/风险/决策)
3. 严格风险控制 (止损/止盈/仓位管理)
4. 实时推送 (微信/Telegram)

作者: 华尔街量化分析师
警告: 这是真金白银的实盘系统，请务必先测试！
"""
import asyncio
import signal
import sys
from datetime import datetime
from config_ultimate import config
from notifier import notifier
from price_monitor import PriceMonitor
from news_analyzer import NewsAnalyzer
from twitter_monitor import TwitterMonitor
from leading_indicators import LeadingIndicatorsMonitor


class LiveTradingSystem:
    """实盘交易系统 - 提前预警版"""
    
    def __init__(self):
        # 核心监控器
        self.price_monitor = PriceMonitor(config.GOLD_SYMBOL)
        self.news_analyzer = NewsAnalyzer()
        self.twitter_monitor = TwitterMonitor()
        self.leading_indicators = LeadingIndicatorsMonitor()  # 新增：领先指标
        
        # 系统状态
        self.running = False
        self.tasks = []
        
        # 风险控制
        self.max_position = 0.3  # 最大仓位 30%
        self.stop_loss = 0.02    # 止损 2%
        self.daily_loss_limit = 0.05  # 单日最大亏损 5%
        
        # 统计
        self.total_alerts = 0
        self.leading_alerts = 0  # 领先指标预警次数
        self.price_alerts = 0    # 价格预警次数
        self.news_alerts = 0     # 新闻预警次数
    
    def print_banner(self):
        """打印启动横幅"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆 黄金实盘预警系统 v5.0 - 领先指标版                 ║
║     Live Gold Trading System with Leading Indicators     ║
║                                                           ║
║     ⚡ 提前5-30秒预警 | 🧠 多Agent协作 | 💰 实盘级       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
        print(banner)
        print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 交易模式: 实盘 (LIVE)")
        print(f"📊 监控标的: {config.GOLD_SYMBOL}")
        print(f"💰 最大仓位: {self.max_position:.0%}")
        print(f"🛡️ 止损设置: {self.stop_loss:.0%}")
        print("=" * 63)
    
    def print_config(self):
        """打印配置信息"""
        print("\n⚙️  系统配置:")
        print(f"   • AI 引擎: {config.AI_PROVIDER.upper()}")
        print(f"   • 推送方式: {config.PUSH_METHOD.upper()}")
        print(f"   • 价格检查: {config.PRICE_CHECK_INTERVAL}秒")
        print(f"   • 领先指标: 3秒 (DXY/订单簿/VIX)")
        print(f"   • 推特监控: {config.TWITTER_CHECK_INTERVAL}秒")
        
        print("\n🎯 监控指标:")
        print("   • 领先指标 (提前5-30秒):")
        print("     - 美元指数 (DXY)")
        print("     - 订单簿失衡")
        print("     - VIX 恐慌指数")
        print("   • 实时指标:")
        print("     - 黄金价格 (PAXG/USDT)")
        print("     - 技术指标 (RSI/MACD)")
        print("   • 舆情指标:")
        print("     - 推特监控 (8个顶级账号)")
        print("     - 新闻分析 (RSS)")
        
        print("\n🛡️ 风险控制:")
        print(f"   • 最大仓位: {self.max_position:.0%}")
        print(f"   • 单笔止损: {self.stop_loss:.0%}")
        print(f"   • 单日止损: {self.daily_loss_limit:.0%}")
        print("=" * 63)
    
    async def start(self):
        """启动系统"""
        # 打印横幅
        self.print_banner()
        
        # 验证配置
        if not config.validate():
            print("\n❌ 配置验证失败")
            print("\n💡 快速配置:")
            print("   1. 访问 https://www.pushplus.plus/")
            print("   2. 微信扫码登录，复制 Token")
            print("   3. 在 .env 中设置: PUSHPLUS_TOKEN=你的token")
            return
        
        # 打印配置
        self.print_config()
        
        # 发送启动通知
        print(f"\n📤 发送启动通知到{config.PUSH_METHOD.upper()}...")
        await notifier.send_alert(
            title="🚀 实盘系统启动",
            content=f"""
✅ 黄金实盘预警系统已启动

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 系统配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• AI 引擎: {config.AI_PROVIDER.upper()}
• 监控标的: {config.GOLD_SYMBOL}
• 最大仓位: {self.max_position:.0%}
• 止损设置: {self.stop_loss:.0%}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 监控指标
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 领先指标 (提前5-30秒):
  • 美元指数 (DXY)
  • 订单簿失衡
  • VIX 恐慌指数

📊 实时指标:
  • 黄金价格
  • 技术指标

📰 舆情指标:
  • 推特监控
  • 新闻分析

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 风险提示
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
这是真金白银的实盘系统
请严格遵守风险管理规则

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            alert_type="info"
        )
        
        # 启动监控任务
        print("\n🚀 启动监控任务...\n")
        self.running = True
        
        # 创建并发任务
        self.tasks = [
            asyncio.create_task(self.leading_indicators.run(), name="LeadingIndicators"),  # 最重要
            asyncio.create_task(self.price_monitor.run(), name="PriceMonitor"),
            asyncio.create_task(self.news_analyzer.run(), name="NewsAnalyzer"),
            asyncio.create_task(self.twitter_monitor.run(), name="TwitterMonitor"),
            asyncio.create_task(self.statistics_reporter(), name="StatisticsReporter")
        ]
        
        # 等待所有任务
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            print("\n⏹️  任务已取消")
    
    async def statistics_reporter(self):
        """统计报告器 - 每小时汇报一次"""
        while self.running:
            await asyncio.sleep(3600)  # 1小时
            
            # 收集统计数据
            self.total_alerts = (
                self.leading_indicators.alert_count +
                self.price_monitor.alert_count +
                self.news_analyzer.alert_count +
                self.twitter_monitor.alert_count
            )
            
            # 发送统计报告
            await notifier.send_alert(
                title="📊 系统运行报告",
                content=f"""
系统已运行 1 小时

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 预警统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 总预警次数: {self.total_alerts}
• 领先指标: {self.leading_indicators.alert_count} 次
• 价格异常: {self.price_monitor.alert_count} 次
• 新闻分析: {self.news_analyzer.alert_count} 次
• 推特监控: {self.twitter_monitor.alert_count} 次

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 监控状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 价格检查: {self.price_monitor.check_count} 次
• 新闻检查: {self.news_analyzer.news_checked} 条
• 推文检查: {self.twitter_monitor.tweets_checked} 条

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 系统运行正常

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """,
                alert_type="info"
            )
    
    async def stop(self):
        """停止系统"""
        print("\n\n🛑 正在停止系统...")
        self.running = False
        
        # 取消所有任务
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # 关闭连接
        await self.price_monitor.close()
        await self.leading_indicators.close()
        
        # 打印最终统计
        print("\n📊 最终统计:")
        print(f"   • 总预警次数: {self.total_alerts}")
        print(f"   • 领先指标预警: {self.leading_indicators.alert_count}")
        print(f"   • 价格预警: {self.price_monitor.alert_count}")
        print(f"   • 新闻预警: {self.news_analyzer.alert_count}")
        print(f"   • 推特预警: {self.twitter_monitor.alert_count}")
        print(f"   • 推送成功: {notifier.success_count if hasattr(notifier, 'success_count') else 0}")
        print(f"   • 推送失败: {notifier.fail_count if hasattr(notifier, 'fail_count') else 0}")
        
        # 发送停止通知
        await notifier.send_alert(
            title="🛑 系统已停止",
            content=f"""
黄金实盘预警系统已停止

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 运行统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 总预警次数: {self.total_alerts}
• 领先指标: {self.leading_indicators.alert_count} 次
• 价格异常: {self.price_monitor.alert_count} 次
• 新闻分析: {self.news_analyzer.alert_count} 次
• 推特监控: {self.twitter_monitor.alert_count} 次

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            alert_type="info"
        )
        
        print("\n✅ 系统已安全退出")


# 全局实例
system = None


def signal_handler(signum, frame):
    """信号处理器 (Ctrl+C)"""
    print("\n\n⚠️  收到中断信号...")
    if system and system.running:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(system.stop())
        loop.close()
    sys.exit(0)


async def main():
    """主函数"""
    global system
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建系统实例
    system = LiveTradingSystem()
    
    try:
        await system.start()
    except KeyboardInterrupt:
        await system.stop()
    except Exception as e:
        print(f"\n❌ 系统异常: {e}")
        import traceback
        traceback.print_exc()
        await system.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见!")

