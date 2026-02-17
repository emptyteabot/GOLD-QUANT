"""
简化版价格监控 - 使用Yahoo Finance作为主要数据源
避免网络连接问题
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SimplePriceMonitor:
    """简化版价格监控器 - 只关注核心功能"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_price = None
    
    async def initialize(self):
        """初始化"""
        self.session = aiohttp.ClientSession()
        logger.info("价格监控器已初始化")
    
    async def close(self):
        """关闭"""
        if self.session:
            await self.session.close()
    
    async def fetch_gold_price_yahoo(self) -> Optional[float]:
        """
        从Yahoo Finance获取黄金价格
        交易品种: GC=F (黄金期货)
        """
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
            params = {
                'interval': '1m',
                'range': '1d'
            }
            
            async with self.session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'chart' in data and 'result' in data['chart']:
                        result = data['chart']['result'][0]
                        if 'meta' in result and 'regularMarketPrice' in result['meta']:
                            price = float(result['meta']['regularMarketPrice'])
                            self.last_price = price
                            return price
        except Exception as e:
            logger.warning(f"Yahoo Finance获取失败: {e}")
        
        return None
    
    async def fetch_gold_price_binance(self) -> Optional[float]:
        """
        从Binance获取黄金价格
        交易对: PAXGUSDT (黄金代币)
        """
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {'symbol': 'PAXGUSDT'}
            
            async with self.session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'price' in data:
                        # PAXG价格约等于1盎司黄金价格
                        price = float(data['price'])
                        self.last_price = price
                        return price
        except Exception as e:
            logger.warning(f"Binance获取失败: {e}")
        
        return None
    
    async def fetch_current_price(self) -> Optional[float]:
        """
        获取当前黄金价格（多源容错）
        
        优先级:
        1. Yahoo Finance (最准确)
        2. Binance PAXG (备用)
        3. 上次缓存价格
        """
        # 尝试Yahoo Finance
        price = await self.fetch_gold_price_yahoo()
        if price:
            return price
        
        # 尝试Binance
        price = await self.fetch_gold_price_binance()
        if price:
            return price
        
        # 返回缓存价格
        if self.last_price:
            logger.warning("使用缓存价格")
            return self.last_price
        
        logger.error("所有数据源均失败")
        return None
    
    async def fetch_price_history(self, hours: int = 24) -> Optional[list]:
        """
        获取历史价格数据
        
        Args:
            hours: 获取最近N小时的数据
        
        Returns:
            列表: [{'time': timestamp, 'price': float}, ...]
        """
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
            params = {
                'interval': '1h',
                'range': f'{hours}h'
            }
            
            async with self.session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'chart' in data and 'result' in data['chart']:
                        result = data['chart']['result'][0]
                        
                        timestamps = result.get('timestamp', [])
                        indicators = result.get('indicators', {})
                        quote = indicators.get('quote', [{}])[0]
                        closes = quote.get('close', [])
                        
                        history = []
                        for i, (ts, price) in enumerate(zip(timestamps, closes)):
                            if price is not None:
                                history.append({
                                    'time': datetime.fromtimestamp(ts),
                                    'price': float(price)
                                })
                        
                        return history
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
        
        return None


# ==================== 测试代码 ====================

async def test_price_monitor():
    """测试价格监控"""
    monitor = SimplePriceMonitor()
    await monitor.initialize()
    
    print("=" * 70)
    print("💰 黄金价格监控测试")
    print("=" * 70)
    print()
    
    try:
        # 测试当前价格
        print("正在获取当前价格...")
        price = await monitor.fetch_current_price()
        
        if price:
            print(f"✅ 当前黄金价格: ${price:,.2f}")
        else:
            print("❌ 获取价格失败")
        
        print()
        
        # 测试历史数据
        print("正在获取24小时历史数据...")
        history = await monitor.fetch_price_history(hours=24)
        
        if history:
            print(f"✅ 获取到 {len(history)} 个数据点")
            print(f"   最早: {history[0]['time']} - ${history[0]['price']:,.2f}")
            print(f"   最新: {history[-1]['time']} - ${history[-1]['price']:,.2f}")
            
            # 计算24小时涨跌
            if len(history) >= 2:
                change = history[-1]['price'] - history[0]['price']
                change_pct = (change / history[0]['price']) * 100
                print(f"   24h变化: ${change:+.2f} ({change_pct:+.2f}%)")
        else:
            print("❌ 获取历史数据失败")
        
        print()
        print("=" * 70)
        
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(test_price_monitor())


