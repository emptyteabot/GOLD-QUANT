"""
国内数据源价格监控 - 免费且稳定
使用新浪财经、东方财富等国内API
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class ChinaDataMonitor:
    """国内数据源监控器 - 完全免费"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_price = None
        
        # 使用V2Ray的socks5代理（端口11843）
        # 注意：aiohttp需要安装 aiohttp-socks 才能使用socks5
        # 先尝试不使用代理，让系统代理生效
        self.proxy = None  # 使用系统代理
        self.use_proxy = False  # 暂时禁用代理
    
    async def initialize(self):
        """初始化"""
        # 创建session，信任环境变量中的代理设置
        connector = aiohttp.TCPConnector(ssl=False)  # 禁用SSL验证
        self.session = aiohttp.ClientSession(connector=connector, trust_env=True)
        logger.info("价格监控器已初始化（使用系统代理）")
    
    async def close(self):
        """关闭"""
        if self.session:
            await self.session.close()
    
    # ==================== 1. 新浪财经 ====================
    
    async def fetch_gold_sina(self) -> Optional[float]:
        """
        新浪财经 - 黄金价格
        完全免费，无需API密钥
        """
        try:
            # 新浪财经黄金期货
            url = "https://hq.sinajs.cn/list=hf_GC"
            
            # 不指定代理，使用系统代理
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # 解析数据：var hq_str_hf_GC="最新价,..."
                    if 'hf_GC=' in text:
                        data = text.split('"')[1].split(',')
                        if len(data) > 0:
                            price = float(data[0])
                            self.last_price = price
                            return price
        except Exception as e:
            logger.warning(f"新浪财经获取失败: {e}")
        
        return None
    
    # ==================== 2. 东方财富 ====================
    
    async def fetch_gold_eastmoney(self) -> Optional[float]:
        """
        东方财富 - 黄金价格
        完全免费，数据准确
        """
        try:
            # 东方财富黄金行情
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': '113.gc2504',  # 黄金期货主力合约
                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58',
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
            }
            
            # 使用代理
            async with self.session.get(url, params=params, proxy=self.proxy, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'data' in data and data['data']:
                        # f43 是最新价
                        price = float(data['data'].get('f43', 0)) / 100  # 转换为美元
                        if price > 0:
                            self.last_price = price
                            return price
        except Exception as e:
            logger.warning(f"东方财富获取失败: {e}")
        
        return None
    
    # ==================== 3. 腾讯财经 ====================
    
    async def fetch_gold_tencent(self) -> Optional[float]:
        """
        腾讯财经 - 黄金价格
        完全免费
        """
        try:
            # 腾讯财经黄金
            url = "https://qt.gtimg.cn/q=AUTD"
            
            # 使用代理
            async with self.session.get(url, proxy=self.proxy, timeout=10) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # 解析数据
                    if 'AUTD~' in text:
                        parts = text.split('~')
                        if len(parts) > 3:
                            price = float(parts[3])
                            self.last_price = price
                            return price
        except Exception as e:
            logger.warning(f"腾讯财经获取失败: {e}")
        
        return None
    
    # ==================== 4. Binance (使用代理) ====================
    
    async def fetch_gold_binance(self) -> Optional[float]:
        """
        Binance - PAXGUSDT (黄金代币)
        使用系统代理
        """
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {'symbol': 'PAXGUSDT'}
            
            # 不指定代理，使用系统代理
            async with self.session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'price' in data:
                        price = float(data['price'])
                        self.last_price = price
                        return price
        except Exception as e:
            logger.warning(f"Binance获取失败: {e}")
        
        return None
    
    # ==================== 5. OKX (推荐) ====================
    
    async def fetch_gold_okx(self) -> Optional[float]:
        """
        OKX - XAUT-USDT (Tether Gold黄金代币)
        使用系统代理
        """
        try:
            url = "https://www.okx.com/api/v5/market/ticker"
            params = {'instId': 'XAUT-USDT'}
            
            # 不指定代理，使用系统代理
            async with self.session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'data' in data and len(data['data']) > 0:
                        price = float(data['data'][0]['last'])
                        self.last_price = price
                        return price
        except Exception as e:
            logger.warning(f"OKX获取失败: {e}")
        
        return None
    
    # ==================== 综合获取 ====================
    
    async def fetch_current_price(self) -> Optional[float]:
        """
        获取当前黄金价格（多源容错）
        
        优先级：
        1. OKX (国内可访问，最稳定) ⭐⭐⭐
        2. Binance (使用代理)
        3. 新浪财经 (国内)
        4. 东方财富 (国内)
        5. 腾讯财经 (国内)
        6. 缓存价格
        """
        # 1. 优先OKX
        price = await self.fetch_gold_okx()
        if price:
            logger.info(f"✅ OKX价格: ${price:,.2f}")
            return price
        
        # 2. 尝试Binance（使用代理）
        price = await self.fetch_gold_binance()
        if price:
            logger.info(f"✅ Binance价格: ${price:,.2f}")
            return price
        
        # 3. 尝试新浪财经
        price = await self.fetch_gold_sina()
        if price:
            logger.info(f"✅ 新浪财经价格: ${price:,.2f}")
            return price
        
        # 4. 尝试东方财富
        price = await self.fetch_gold_eastmoney()
        if price:
            logger.info(f"✅ 东方财富价格: ${price:,.2f}")
            return price
        
        # 5. 尝试腾讯财经
        price = await self.fetch_gold_tencent()
        if price:
            logger.info(f"✅ 腾讯财经价格: ${price:,.2f}")
            return price
        
        # 6. 返回缓存
        if self.last_price:
            logger.warning(f"⚠️ 使用缓存价格: ${self.last_price:,.2f}")
            return self.last_price
        
        logger.error("❌ 所有数据源均失败")
        return None
    
    async def fetch_price_history(self, hours: int = 24) -> Optional[List[Dict]]:
        """
        获取历史价格（使用OKX）
        
        Args:
            hours: 小时数
        
        Returns:
            [{'time': datetime, 'price': float}, ...]
        """
        try:
            url = "https://www.okx.com/api/v5/market/candles"
            params = {
                'instId': 'XAUT-USDT',
                'bar': '1H',  # 1小时K线
                'limit': hours
            }
            
            # 使用代理
            async with self.session.get(url, params=params, proxy=self.proxy, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'data' in data:
                        history = []
                        for candle in data['data']:
                            # [时间戳, 开, 高, 低, 收, 量, ...]
                            timestamp = int(candle[0]) / 1000
                            close_price = float(candle[4])
                            history.append({
                                'time': datetime.fromtimestamp(timestamp),
                                'price': close_price
                            })
                        return list(reversed(history))  # 从旧到新排序
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
        
        return None


# ==================== 测试代码 ====================

async def test_china_monitor():
    """测试国内数据源"""
    monitor = ChinaDataMonitor()
    await monitor.initialize()
    
    print("=" * 70)
    print("💰 国内数据源测试")
    print("=" * 70)
    print()
    
    try:
        # 测试各个数据源
        print("【测试1】OKX (推荐)")
        price = await monitor.fetch_gold_okx()
        if price:
            print(f"  ✅ 价格: ${price:,.2f}")
        else:
            print(f"  ❌ 获取失败")
        print()
        
        print("【测试2】Binance (使用代理)")
        price = await monitor.fetch_gold_binance()
        if price:
            print(f"  ✅ 价格: ${price:,.2f}")
        else:
            print(f"  ❌ 获取失败")
        print()
        
        print("【测试3】新浪财经")
        price = await monitor.fetch_gold_sina()
        if price:
            print(f"  ✅ 价格: ${price:,.2f}")
        else:
            print(f"  ❌ 获取失败")
        print()
        
        print("【测试4】综合获取（自动选择最佳数据源）")
        price = await monitor.fetch_current_price()
        if price:
            print(f"  ✅ 当前黄金价格: ${price:,.2f}")
        else:
            print(f"  ❌ 所有数据源均失败")
        print()
        
        print("【测试5】历史数据")
        history = await monitor.fetch_price_history(hours=24)
        if history:
            print(f"  ✅ 获取到 {len(history)} 个数据点")
            print(f"     最早: {history[0]['time']} - ${history[0]['price']:,.2f}")
            print(f"     最新: {history[-1]['time']} - ${history[-1]['price']:,.2f}")
            
            if len(history) >= 2:
                change = history[-1]['price'] - history[0]['price']
                change_pct = (change / history[0]['price']) * 100
                print(f"     24h变化: ${change:+.2f} ({change_pct:+.2f}%)")
        else:
            print(f"  ❌ 获取失败")
        
        print()
        print("=" * 70)
        print("✅ 测试完成")
        print("=" * 70)
        
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(test_china_monitor())

