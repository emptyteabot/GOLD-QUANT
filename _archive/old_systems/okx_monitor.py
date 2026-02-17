"""
OKX 版本 - 使用 OKX 交易所获取价格数据
免费、稳定、国内可访问
"""
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime
from typing import Optional, Dict
from notifier import notifier
from config_ultimate import config


class OKXPriceMonitor:
    """OKX 价格监控器"""
    
    def __init__(self):
        # 初始化 OKX 交易所（不需要 API Key）
        self.exchange = ccxt.okx({
            'enableRateLimit': True,
            'timeout': 10000,
        })
        
        # 监控的交易对
        self.symbols = {
            'gold': 'BTC/USDT',  # 用 BTC 作为黄金代理（相关性高）
            'eth': 'ETH/USDT',
        }
        
        # 价格历史
        self.price_history = {symbol: [] for symbol in self.symbols.values()}
        
        # 统计
        self.check_count = 0
        self.alert_count = 0
        
        # 上次预警时间
        self.last_alert_time = 0
        self.alert_cooldown = 300  # 5分钟冷却
    
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
        
        if len(history) < minutes:
            return None
        
        current_price = history[-1]
        old_price = history[-minutes]
        
        if old_price == 0:
            return None
        
        change = (current_price - old_price) / old_price
        return change
    
    async def check_alert_conditions(self, symbol: str, price: float, change_1m: float):
        """检查预警条件"""
        current_time = datetime.now().timestamp()
        
        # 急跌预警
        if change_1m <= config.THRESHOLD_PRICE_DROP_1M:
            if current_time - self.last_alert_time < self.alert_cooldown:
                print(f"⏳ 预警冷却中...")
                return
            
            print(f"🚨 触发急跌预警: {symbol} {change_1m:.2%}")
            
            await notifier.send_alert(
                title=f"🚨 {symbol} 急跌预警",
                content=f"""
⚠️ 价格急速下跌！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 价格信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 交易对: {symbol}
• 当前价格: ${price:,.2f}
• 1分钟跌幅: {change_1m:.2%}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 检查持仓风险
• 关注市场动态
• 考虑止损策略

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """,
                alert_type="danger"
            )
            
            self.last_alert_time = current_time
            self.alert_count += 1
        
        # 急涨预警
        elif change_1m >= config.THRESHOLD_PRICE_SPIKE_1M:
            if current_time - self.last_alert_time < self.alert_cooldown:
                return
            
            print(f"📈 触发急涨预警: {symbol} {change_1m:.2%}")
            
            await notifier.send_alert(
                title=f"📈 {symbol} 急涨预警",
                content=f"""
🚀 价格快速上涨！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 价格信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 交易对: {symbol}
• 当前价格: ${price:,.2f}
• 1分钟涨幅: {change_1m:.2%}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 关注突破确认
• 警惕假突破回落
• 考虑止盈策略

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """,
                alert_type="info"
            )
            
            self.last_alert_time = current_time
            self.alert_count += 1
    
    async def run(self):
        """主监控循环"""
        print(f"\n📊 OKX 价格监控器启动")
        print(f"⏱️  检查间隔: {config.PRICE_CHECK_INTERVAL}秒")
        print(f"📈 监控品种: {', '.join(self.symbols.keys())}")
        print(f"📉 跌幅阈值: {config.THRESHOLD_PRICE_DROP_1M:.2%}")
        print("-" * 60)
        
        while True:
            try:
                self.check_count += 1
                
                for name, symbol in self.symbols.items():
                    price = await self.fetch_price(symbol)
                    
                    if price is None:
                        continue
                    
                    # 记录价格
                    self.price_history[symbol].append(price)
                    
                    # 只保留最近60个数据点（1分钟）
                    if len(self.price_history[symbol]) > 60:
                        self.price_history[symbol].pop(0)
                    
                    # 计算涨跌幅
                    change_1m = await self.calculate_change(symbol, minutes=1)
                    
                    # 显示信息
                    if self.check_count % 10 == 0:  # 每10次显示一次
                        change_str = f"{change_1m:+.2%}" if change_1m else "N/A"
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {name.upper()}: ${price:,.2f} | 1m: {change_str}")
                    
                    # 检查预警
                    if change_1m is not None:
                        await self.check_alert_conditions(symbol, price, change_1m)
                
                await asyncio.sleep(config.PRICE_CHECK_INTERVAL)
                
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                await asyncio.sleep(10)
    
    async def close(self):
        """关闭连接"""
        await self.exchange.close()


# 测试函数
async def test_okx():
    """测试 OKX 连接"""
    monitor = OKXPriceMonitor()
    
    print("🧪 测试 OKX 交易所连接\n")
    
    for name, symbol in monitor.symbols.items():
        price = await monitor.fetch_price(symbol)
        if price:
            print(f"✅ {name.upper()} ({symbol}): ${price:,.2f}")
        else:
            print(f"❌ {name.upper()} ({symbol}): 获取失败")
    
    await monitor.close()
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_okx())




