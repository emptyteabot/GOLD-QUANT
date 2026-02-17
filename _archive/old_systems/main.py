"""
黄金崩盘预警系统 - 主程序
Gold Crash Early Warning System

整合价格监控和舆情分析,实现分钟级预警
"""
import asyncio
import signal
import sys
from datetime import datetime
from config import config
from notifier import notifier
from price_monitor import PriceMonitor
from news_analyzer import NewsAnalyzer


class GoldSentinel:
    """黄金哨兵主控制器"""
    
    def __init__(self):
        self.price_monitor = PriceMonitor(config.GOLD_SYMBOL)
        self.news_analyzer = NewsAnalyzer()
        self.running = False
        self.tasks = []
    
    def print_banner(self):
        """打印启动横幅"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆 黄金崩盘预警系统 v3.0                              ║
║     Gold Crash Early Warning System                       ║
║                                                           ║
║     ⚡ 分钟级趋势预警 | 🧠 DeepSeek AI驱动                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
        print(banner)
        print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 监控标的: {config.GOLD_SYMBOL}")
        print(f"🔔 通知渠道: 飞书 Webhook")
        print("=" * 63)
    
    def print_config(self):
        """打印配置信息"""
        print("\n⚙️  系统配置:")
        print(f"   • 价格检查间隔: {config.PRICE_CHECK_INTERVAL}秒")
        print(f"   • 新闻检查间隔: {config.NEWS_CHECK_INTERVAL}秒")
        print(f"   • 1分钟跌幅阈值: {config.THRESHOLD_PRICE_DROP_1M:.2%}")
        print(f"   • 5分钟跌幅阈值: {config.THRESHOLD_PRICE_DROP_5M:.2%}")
        print(f"   • 情感分数阈值: {config.THRESHOLD_SENTIMENT}/10")
        print(f"   • 高频监控时段: {config.HIGH_FREQUENCY_PERIODS}")
        print(f"   • 新闻源数量: {len(config.NEWS_FEEDS)}")
        print("=" * 63)
    
    async def start(self):
        """启动系统"""
        # 打印横幅
        self.print_banner()
        
        # 验证配置
        if not config.validate():
            print("\n❌ 配置验证失败,请检查 .env 文件")
            print("💡 提示: 复制 env.example 为 .env 并填入你的配置")
            return
        
        # 打印配置
        self.print_config()
        
        # 发送启动通知
        print("\n📤 发送启动通知到飞书...")
        await notifier.send_system_start()
        
        # 启动监控任务
        print("\n🚀 启动监控任务...\n")
        self.running = True
        
        # 创建并发任务
        self.tasks = [
            asyncio.create_task(self.price_monitor.run(), name="PriceMonitor"),
            asyncio.create_task(self.news_analyzer.run(), name="NewsAnalyzer")
        ]
        
        # 等待所有任务
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            print("\n⏹️  任务已取消")
    
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
        
        # 关闭交易所连接
        await self.price_monitor.close()
        
        # 打印统计信息
        print("\n📊 运行统计:")
        print(f"   • 价格检查次数: {self.price_monitor.check_count}")
        print(f"   • 价格警报次数: {self.price_monitor.alert_count}")
        print(f"   • 新闻检查次数: {self.news_analyzer.news_checked}")
        print(f"   • 新闻分析次数: {self.news_analyzer.news_analyzed}")
        print(f"   • 舆情警报次数: {self.news_analyzer.alert_count}")
        
        print("\n✅ 系统已安全退出")


# 全局实例
sentinel = None


def signal_handler(signum, frame):
    """信号处理器 (Ctrl+C)"""
    print("\n\n⚠️  收到中断信号...")
    if sentinel and sentinel.running:
        # 创建新的事件循环来运行停止协程
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(sentinel.stop())
        loop.close()
    sys.exit(0)


async def main():
    """主函数"""
    global sentinel
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建哨兵实例
    sentinel = GoldSentinel()
    
    try:
        await sentinel.start()
    except KeyboardInterrupt:
        await sentinel.stop()
    except Exception as e:
        print(f"\n❌ 系统异常: {e}")
        import traceback
        traceback.print_exc()
        await sentinel.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见!")




