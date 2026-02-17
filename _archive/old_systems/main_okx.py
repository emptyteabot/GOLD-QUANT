"""
完整版 - OKX价格 + AI新闻分析 + 飞书推送
适配国内网络环境
"""
import asyncio
import signal
import sys
from datetime import datetime
from config_ultimate import config
from notifier import notifier
from okx_monitor import OKXPriceMonitor


class OptimizedTradingSystem:
    """优化版交易系统 - OKX + AI"""
    
    def __init__(self):
        self.price_monitor = OKXPriceMonitor()
        self.running = False
        self.tasks = []
    
    def print_banner(self):
        """打印启动横幅"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆 黄金实盘预警系统 v6.0 - OKX优化版                 ║
║     Gold Trading System - OKX Optimized                  ║
║                                                           ║
║     📊 OKX实时价格 | 🧠 AI分析 | 📱 飞书推送            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
        print(banner)
        print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 交易所: OKX (免费API)")
        print(f"🧠 AI 引擎: {config.AI_PROVIDER.upper()}")
        print(f"📱 推送方式: {config.PUSH_METHOD.upper()}")
        print("=" * 63)
    
    async def news_monitor(self):
        """新闻监控"""
        print("\n📰 新闻监控器启动")
        print(f"⏱️  检查间隔: {config.NEWS_CHECK_INTERVAL}秒")
        print(f"🔗 新闻源: {len(config.NEWS_FEEDS)}个")
        print("-" * 60)
        
        import feedparser
        from openai import AsyncOpenAI
        import json
        
        # 初始化 AI 客户端
        if config.AI_PROVIDER == "deepseek":
            client = AsyncOpenAI(
                api_key=config.DEEPSEEK_API_KEY,
                base_url=config.DEEPSEEK_BASE_URL
            )
            model = "deepseek-chat"
        else:
            # 使用你的 Grok 中转 API
            client = AsyncOpenAI(
                api_key=config.GROK_API_KEY,
                base_url=config.GROK_BASE_URL
            )
            model = "grok-beta"  # 或者你的中转API支持的模型名
        
        seen_links = set()
        
        while self.running:
            try:
                for feed_url in config.NEWS_FEEDS:
                    try:
                        feed = feedparser.parse(feed_url)
                        
                        for entry in feed.entries[:3]:
                            title = entry.get('title', '')
                            link = entry.get('link', '')
                            
                            if link in seen_links:
                                continue
                            
                            # 过滤黄金相关
                            keywords = ['gold', 'xau', 'bullion', '黄金', 'precious', 'metal', 'fed', 'dollar']
                            if not any(kw in title.lower() for kw in keywords):
                                continue
                            
                            seen_links.add(link)
                            print(f"\n📰 {title[:60]}...")
                            
                            # AI 分析
                            try:
                                response = await client.chat.completions.create(
                                    model=model,
                                    messages=[
                                        {
                                            "role": "system",
                                            "content": "你是黄金交易分析师。分析新闻对黄金价格的影响，返回JSON格式: {\"score\": -10到10的整数, \"summary\": \"20字以内的简短分析\"}"
                                        },
                                        {
                                            "role": "user",
                                            "content": f"分析这条新闻对黄金的影响: {title}"
                                        }
                                    ],
                                    temperature=0.3,
                                    max_tokens=150,
                                    timeout=15.0
                                )
                                
                                result_text = response.choices[0].message.content.strip()
                                
                                # 解析JSON
                                if "```" in result_text:
                                    result_text = result_text.split("```")[1]
                                    if result_text.startswith("json"):
                                        result_text = result_text[4:]
                                
                                result = json.loads(result_text)
                                score = result.get('score', 0)
                                summary = result.get('summary', '')
                                
                                emoji = "🔴" if score < -5 else "🟡" if score < 0 else "🟢"
                                print(f"   {emoji} AI评分: {score:+d}/10 | {summary}")
                                
                                # 重大事件预警
                                if abs(score) >= 7:
                                    alert_type = "danger" if score < 0 else "info"
                                    alert_title = "🚨 黄金重大利空" if score < 0 else "📈 黄金重大利好"
                                    
                                    await notifier.send_alert(
                                        title=alert_title,
                                        content=f"""
📰 {title}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI 分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 影响评分: {score}/10
• 分析: {summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 {link}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                        """,
                                        alert_type=alert_type
                                    )
                                
                            except Exception as e:
                                print(f"   ❌ AI分析失败: {str(e)[:50]}")
                            
                            await asyncio.sleep(2)
                    
                    except Exception as e:
                        print(f"❌ RSS抓取失败: {str(e)[:50]}")
                
                await asyncio.sleep(config.NEWS_CHECK_INTERVAL)
                
            except Exception as e:
                print(f"❌ 新闻监控异常: {e}")
                await asyncio.sleep(30)
    
    async def start(self):
        """启动系统"""
        self.print_banner()
        
        # 发送启动通知
        print("\n📤 发送启动通知...")
        await notifier.send_alert(
            title="🚀 系统启动",
            content=f"""
✅ 黄金预警系统已启动

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 系统配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 交易所: OKX (免费API)
• AI 引擎: {config.AI_PROVIDER.upper()}
• 推送方式: {config.PUSH_METHOD.upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 监控内容
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• BTC/ETH 实时价格
• 黄金相关新闻
• AI 情感分析

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            alert_type="info"
        )
        
        print("\n🚀 启动监控任务...\n")
        self.running = True
        
        # 创建任务
        self.tasks = [
            asyncio.create_task(self.price_monitor.run(), name="PriceMonitor"),
            asyncio.create_task(self.news_monitor(), name="NewsMonitor"),
        ]
        
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            print("\n⏹️  任务已取消")
    
    async def stop(self):
        """停止系统"""
        print("\n\n🛑 正在停止系统...")
        self.running = False
        
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        await self.price_monitor.close()
        
        print(f"\n📊 运行统计:")
        print(f"   • 价格检查: {self.price_monitor.check_count} 次")
        print(f"   • 价格预警: {self.price_monitor.alert_count} 次")
        
        await notifier.send_alert(
            title="🛑 系统已停止",
            content=f"""
系统已停止运行

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 运行统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 价格检查: {self.price_monitor.check_count} 次
• 价格预警: {self.price_monitor.alert_count} 次

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            alert_type="info"
        )
        
        print("\n✅ 系统已安全退出")


system = None

def signal_handler(signum, frame):
    """信号处理器"""
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
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    system = OptimizedTradingSystem()
    
    try:
        await system.start()
    except KeyboardInterrupt:
        await system.stop()
    except Exception as e:
        print(f"\n❌ 系统异常: {e}")
        import traceback
        traceback.print_exc()
        if system:
            await system.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见!")




