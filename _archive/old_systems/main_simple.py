"""
国内网络优化版 - 主程序
使用 DeepSeek API + 模拟数据（用于测试）
"""
import asyncio
import signal
import sys
from datetime import datetime
from config_ultimate import config
from notifier import notifier


class SimplifiedTradingSystem:
    """简化版交易系统 - 适配国内网络"""
    
    def __init__(self):
        self.running = False
        self.alert_count = 0
    
    def print_banner(self):
        """打印启动横幅"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆 黄金实盘预警系统 v5.0 - 国内优化版                ║
║     Gold Trading System - China Optimized                ║
║                                                           ║
║     📊 新闻监控 | 🧠 AI分析 | 📱 飞书推送               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
        print(banner)
        print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 运行模式: 新闻监控模式")
        print(f"🧠 AI 引擎: {config.AI_PROVIDER.upper()}")
        print(f"📱 推送方式: {config.PUSH_METHOD.upper()}")
        print("=" * 63)
    
    async def test_feishu(self):
        """测试飞书推送"""
        print("\n📤 测试飞书推送...")
        success = await notifier.send_alert(
            title="🚀 系统启动测试",
            content=f"""
✅ 黄金预警系统已启动

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 系统配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• AI 引擎: {config.AI_PROVIDER.upper()}
• 推送方式: {config.PUSH_METHOD.upper()}
• 监控模式: 新闻分析

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 提示
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
由于网络限制，当前版本专注于:
• 新闻情感分析
• 重大事件预警
• AI 智能推送

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            alert_type="info"
        )
        
        if success:
            print("✅ 飞书推送成功！")
        else:
            print("❌ 飞书推送失败，请检查配置")
        
        return success
    
    async def news_monitor(self):
        """新闻监控循环"""
        print("\n📰 新闻监控器启动")
        print(f"⏱️  检查间隔: {config.NEWS_CHECK_INTERVAL}秒")
        print(f"🔗 新闻源: {len(config.NEWS_FEEDS)}个")
        print("-" * 60)
        
        import feedparser
        from openai import AsyncOpenAI
        
        # 初始化 AI 客户端
        if config.AI_PROVIDER == "deepseek":
            client = AsyncOpenAI(
                api_key=config.DEEPSEEK_API_KEY,
                base_url=config.DEEPSEEK_BASE_URL
            )
            model = "deepseek-chat"
        else:
            client = AsyncOpenAI(
                api_key=config.GROK_API_KEY,
                base_url=config.GROK_BASE_URL
            )
            model = config.GROK_MODEL
        
        seen_links = set()
        
        while self.running:
            try:
                for feed_url in config.NEWS_FEEDS:
                    try:
                        print(f"\n🔍 检查新闻源: {feed_url.split('/')[2]}...")
                        feed = feedparser.parse(feed_url)
                        
                        for entry in feed.entries[:3]:
                            title = entry.get('title', '')
                            link = entry.get('link', '')
                            
                            if link in seen_links:
                                continue
                            
                            # 过滤黄金相关新闻
                            keywords = ['gold', 'xau', 'bullion', '黄金', 'precious', 'metal']
                            if not any(kw in title.lower() for kw in keywords):
                                continue
                            
                            seen_links.add(link)
                            print(f"\n📰 新闻: {title[:60]}...")
                            
                            # AI 分析
                            try:
                                response = await client.chat.completions.create(
                                    model=model,
                                    messages=[
                                        {
                                            "role": "system",
                                            "content": "你是黄金交易分析师。分析新闻对黄金价格的影响，返回JSON: {\"score\": -10到10的整数, \"summary\": \"简短分析\"}"
                                        },
                                        {
                                            "role": "user",
                                            "content": f"分析: {title}"
                                        }
                                    ],
                                    temperature=0.3,
                                    max_tokens=150,
                                    timeout=10.0
                                )
                                
                                result_text = response.choices[0].message.content.strip()
                                
                                # 解析结果
                                import json
                                if "```" in result_text:
                                    result_text = result_text.split("```")[1]
                                    if result_text.startswith("json"):
                                        result_text = result_text[4:]
                                
                                result = json.loads(result_text)
                                score = result.get('score', 0)
                                summary = result.get('summary', '')
                                
                                emoji = "🔴" if score < -5 else "🟡" if score < 0 else "🟢"
                                print(f"   {emoji} AI评分: {score:+d}/10")
                                print(f"   💬 分析: {summary}")
                                
                                # 重大利空预警
                                if score <= -7:
                                    print(f"   🚨 触发预警！")
                                    await notifier.send_alert(
                                        title="🚨 黄金重大利空",
                                        content=f"""
📰 新闻标题:
{title}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI 分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 影响评分: {score}/10 (重大利空)
• 分析: {summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 新闻链接
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{link}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                        """,
                                        alert_type="danger"
                                    )
                                    self.alert_count += 1
                                
                                # 重大利多预警
                                elif score >= 7:
                                    print(f"   📈 触发预警！")
                                    await notifier.send_alert(
                                        title="📈 黄金重大利好",
                                        content=f"""
📰 新闻标题:
{title}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI 分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 影响评分: {score}/10 (重大利好)
• 分析: {summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 新闻链接
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{link}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                        """,
                                        alert_type="info"
                                    )
                                    self.alert_count += 1
                                
                            except Exception as e:
                                print(f"   ❌ AI分析失败: {str(e)[:50]}")
                            
                            await asyncio.sleep(2)
                    
                    except Exception as e:
                        print(f"❌ RSS抓取失败: {str(e)[:50]}")
                
                print(f"\n💤 等待 {config.NEWS_CHECK_INTERVAL} 秒...")
                await asyncio.sleep(config.NEWS_CHECK_INTERVAL)
                
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                await asyncio.sleep(30)
    
    async def start(self):
        """启动系统"""
        self.print_banner()
        
        # 测试飞书
        feishu_ok = await self.test_feishu()
        if not feishu_ok:
            print("\n⚠️ 飞书推送测试失败，但系统会继续运行")
            print("💡 请检查 .env 中的 FEISHU_WEBHOOK_URL 配置")
        
        print("\n" + "=" * 63)
        print("🚀 开始监控...")
        print("=" * 63)
        
        self.running = True
        
        try:
            await self.news_monitor()
        except KeyboardInterrupt:
            await self.stop()
    
    async def stop(self):
        """停止系统"""
        print("\n\n🛑 正在停止系统...")
        self.running = False
        
        print(f"\n📊 运行统计:")
        print(f"   • 预警次数: {self.alert_count}")
        
        await notifier.send_alert(
            title="🛑 系统已停止",
            content=f"""
黄金预警系统已停止运行

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 运行统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 预警次数: {self.alert_count}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            alert_type="info"
        )
        
        print("\n✅ 系统已安全退出")


# 全局实例
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
    
    system = SimplifiedTradingSystem()
    
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




