"""
飞书交互版 - 黄金监控系统
支持命令交互、实时查询、智能预警
"""
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime
from typing import Optional, Dict
import os
from dotenv import load_dotenv

from feishu_bot import FeishuBot
from command_handler import CommandHandler

load_dotenv()


class OKXMonitorInteractive:
    """OKX 交互式监控器"""
    
    def __init__(self, bot: FeishuBot):
        # 飞书机器人
        self.bot = bot
        
        # 初始化 OKX 交易所
        self.exchange = ccxt.okx({
            'enableRateLimit': True,
            'timeout': 10000,
        })
        
        # 监控的交易对
        self.symbols = {
            'btc': 'BTC/USDT',  # 用 BTC 作为黄金代理
            'eth': 'ETH/USDT',
        }
        
        # 价格历史
        self.price_history = {symbol: [] for symbol in self.symbols.values()}
        
        # 配置
        self.check_interval = int(os.getenv("PRICE_CHECK_INTERVAL", "2"))
        self.threshold_drop = float(os.getenv("THRESHOLD_PRICE_DROP_1M", "-0.002"))
        self.threshold_spike = float(os.getenv("THRESHOLD_PRICE_SPIKE_1M", "0.003"))
        self.alert_cooldown = int(os.getenv("ALERT_COOLDOWN", "300"))
        
        # 统计
        self.check_count = 0
        self.alert_count = 0
        self.start_time = datetime.now().timestamp()
        
        # 上次预警时间
        self.last_alert_time = 0
        
        # 运行状态
        self.running = False
    
    async def fetch_price(self, symbol: str) -> Optional[float]:
        """获取实时价格"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"❌ 获取 {symbol} 价格失败: {str(e)[:50]}")
            return None
    
    async def calculate_change(self, symbol: str, minutes: int = 1) -> Optional[float]:
        """计算涨跌幅"""
        history = self.price_history[symbol]
        
        # 每秒一个数据点，所以 minutes * 60
        required_points = minutes * 60 // self.check_interval
        
        if len(history) < required_points:
            return None
        
        current_price = history[-1]
        old_price = history[-required_points]
        
        if old_price == 0:
            return None
        
        change = (current_price - old_price) / old_price
        return change
    
    async def check_alert_conditions(self, symbol: str, price: float, change_1m: float):
        """检查预警条件"""
        current_time = datetime.now().timestamp()
        
        # 检查冷却时间
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        
        # 急跌预警
        if change_1m <= self.threshold_drop:
            print(f"🚨 触发急跌预警: {symbol} {change_1m:.2%}")
            
            content = f"""⚠️ **价格急速下跌！**

**交易对**: {symbol}
**当前价格**: ${price:,.2f}
**1分钟跌幅**: {change_1m:.2%}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 **建议**
• 检查持仓风险
• 关注市场动态
• 考虑止损策略
"""
            
            await self.bot.send_alert(
                alert_type="price",
                title=f"{symbol} 急跌预警",
                content=content,
                severity="danger"
            )
            
            self.last_alert_time = current_time
            self.alert_count += 1
        
        # 急涨预警
        elif change_1m >= self.threshold_spike:
            print(f"📈 触发急涨预警: {symbol} {change_1m:.2%}")
            
            content = f"""🚀 **价格快速上涨！**

**交易对**: {symbol}
**当前价格**: ${price:,.2f}
**1分钟涨幅**: {change_1m:.2%}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 **建议**
• 关注突破确认
• 警惕假突破回落
• 考虑止盈策略
"""
            
            await self.bot.send_alert(
                alert_type="price",
                title=f"{symbol} 急涨预警",
                content=content,
                severity="warning"
            )
            
            self.last_alert_time = current_time
            self.alert_count += 1
    
    async def monitor_loop(self):
        """主监控循环"""
        print(f"\n📊 OKX 交互式监控器启动")
        print(f"⏱️  检查间隔: {self.check_interval}秒")
        print(f"📈 监控品种: {', '.join(self.symbols.keys())}")
        print(f"📉 跌幅阈值: {self.threshold_drop:.2%}")
        print(f"📈 涨幅阈值: {self.threshold_spike:.2%}")
        print("-" * 60)
        
        self.running = True
        
        while self.running:
            try:
                self.check_count += 1
                
                for name, symbol in self.symbols.items():
                    price = await self.fetch_price(symbol)
                    
                    if price is None:
                        continue
                    
                    # 记录价格
                    self.price_history[symbol].append(price)
                    
                    # 只保留最近 300 个数据点（5分钟）
                    max_points = 300 // self.check_interval
                    if len(self.price_history[symbol]) > max_points:
                        self.price_history[symbol].pop(0)
                    
                    # 计算涨跌幅
                    change_1m = await self.calculate_change(symbol, minutes=1)
                    
                    # 显示信息（每 30 次显示一次）
                    if self.check_count % 30 == 0:
                        change_str = f"{change_1m:+.2%}" if change_1m else "N/A"
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {name.upper()}: ${price:,.2f} | 1m: {change_str}")
                    
                    # 检查预警
                    if change_1m is not None:
                        await self.check_alert_conditions(symbol, price, change_1m)
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                await asyncio.sleep(10)
    
    async def close(self):
        """关闭连接"""
        self.running = False
        await self.exchange.close()


async def main():
    """主函数"""
    # 加载配置
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "")
    
    if not webhook_url:
        print("❌ 未配置 FEISHU_WEBHOOK_URL")
        print("请在 .env 文件中设置 FEISHU_WEBHOOK_URL")
        return
    
    # 初始化飞书机器人
    bot = FeishuBot(webhook_url)
    
    # 初始化监控器
    monitor = OKXMonitorInteractive(bot)
    
    # 初始化命令处理器
    handler = CommandHandler(bot, monitor)
    
    # 发送启动消息
    await bot.send_welcome()
    
    print("\n" + "=" * 70)
    print("🚀 飞书交互版黄金监控系统")
    print("=" * 70)
    print(f"📱 飞书 Webhook: {webhook_url[:50]}...")
    print(f"📊 监控交易对: {', '.join(monitor.symbols.values())}")
    print(f"⏱️  检查间隔: {monitor.check_interval}秒")
    print(f"🔔 预警阈值: {monitor.threshold_drop:.2%} / {monitor.threshold_spike:.2%}")
    print("=" * 70)
    print("\n💡 提示：在飞书群中输入 /help 查看所有命令\n")
    
    try:
        # 启动监控循环
        await monitor.monitor_loop()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ 收到停止信号，正在关闭...")
    
    finally:
        await monitor.close()
        
        # 发送停止消息
        await bot.send_card(
            title="⚠️ 系统已停止",
            content=f"""系统已停止运行

**运行统计**
• 检查次数: {monitor.check_count}
• 预警次数: {monitor.alert_count}
• 运行时长: {datetime.now().timestamp() - monitor.start_time:.0f} 秒
""",
            color="orange"
        )
        
        print("✅ 系统已安全关闭")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见！")



