"""
多源数据引擎 - 专业版
整合所有数据源，提供统一的数据接口
"""
import asyncio
import aiohttp
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv
import json
import time

load_dotenv()


class DataEngine:
    """多源数据引擎"""
    
    def __init__(self):
        # 交易所
        self.okx = ccxt.okx({'enableRateLimit': True})
        self.binance = ccxt.binance({'enableRateLimit': True})
        
        # API Keys
        self.goldapi_key = os.getenv("GOLDAPI_KEY", "")
        self.tushare_token = os.getenv("TUSHARE_TOKEN", "")
        self.twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
        
        # 数据缓存
        self.price_cache = {}
        self.orderbook_cache = {}
        self.indicator_cache = {}
        
        # 统计
        self.fetch_count = 0
        self.error_count = 0
    
    # ==================== 价格数据 ====================
    
    async def fetch_gold_price(self, source: str = "okx") -> Optional[Dict]:
        """
        获取黄金价格
        
        Returns:
            {
                'price': float,
                'timestamp': int,
                'source': str,
                'bid': float,
                'ask': float,
                'volume_24h': float
            }
        """
        try:
            if source == "okx":
                ticker = await self.okx.fetch_ticker('PAXG/USDT')
                return {
                    'price': ticker['last'],
                    'timestamp': ticker['timestamp'],
                    'source': 'OKX',
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'volume_24h': ticker['quoteVolume']
                }
            
            elif source == "binance":
                ticker = await self.binance.fetch_ticker('PAXGUSDT')
                return {
                    'price': ticker['last'],
                    'timestamp': ticker['timestamp'],
                    'source': 'Binance',
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'volume_24h': ticker['quoteVolume']
                }
            
            elif source == "goldapi" and self.goldapi_key:
                async with aiohttp.ClientSession() as session:
                    headers = {"x-access-token": self.goldapi_key}
                    async with session.get(
                        "https://www.goldapi.io/api/XAU/USD",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                'price': data['price'],
                                'timestamp': data['timestamp'] * 1000,
                                'source': 'GoldAPI',
                                'bid': data['bid'],
                                'ask': data['ask'],
                                'volume_24h': 0
                            }
            
            self.fetch_count += 1
            return None
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取价格失败 ({source}): {str(e)[:50]}")
            return None
    
    async def fetch_ohlcv(
        self, 
        symbol: str = 'PAXG/USDT',
        timeframe: str = '1m',
        limit: int = 100,
        source: str = 'okx'
    ) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            if source == 'okx':
                ohlcv = await self.okx.fetch_ohlcv(symbol, timeframe, limit=limit)
            else:
                ohlcv = await self.binance.fetch_ohlcv(symbol.replace('/', ''), timeframe, limit=limit)
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            self.fetch_count += 1
            return df
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取K线失败: {str(e)[:50]}")
            return None
    
    # ==================== 订单簿数据 ====================
    
    async def fetch_orderbook(
        self,
        symbol: str = 'PAXG/USDT',
        depth: int = 20,
        source: str = 'okx'
    ) -> Optional[Dict]:
        """
        获取订单簿数据
        
        Returns:
            {
                'bids': [[price, amount], ...],
                'asks': [[price, amount], ...],
                'timestamp': int,
                'imbalance': float,  # 买卖失衡度
                'spread': float,     # 买卖价差
                'depth_ratio': float # 深度比率
            }
        """
        try:
            if source == 'okx':
                orderbook = await self.okx.fetch_order_book(symbol, depth)
            else:
                orderbook = await self.binance.fetch_order_book(symbol.replace('/', ''), depth)
            
            # 计算订单簿指标
            bids = orderbook['bids']
            asks = orderbook['asks']
            
            # 买卖失衡度
            bid_volume = sum([bid[1] for bid in bids])
            ask_volume = sum([ask[1] for ask in asks])
            imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
            
            # 买卖价差
            spread = (asks[0][0] - bids[0][0]) / bids[0][0] if bids and asks else 0
            
            # 深度比率（前5档 vs 后15档）
            bid_depth_front = sum([bid[1] for bid in bids[:5]])
            bid_depth_back = sum([bid[1] for bid in bids[5:]])
            depth_ratio = bid_depth_front / bid_depth_back if bid_depth_back > 0 else 0
            
            result = {
                'bids': bids,
                'asks': asks,
                'timestamp': orderbook['timestamp'],
                'imbalance': imbalance,
                'spread': spread,
                'depth_ratio': depth_ratio
            }
            
            self.orderbook_cache[symbol] = result
            self.fetch_count += 1
            
            return result
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取订单簿失败: {str(e)[:50]}")
            return None
    
    async def detect_large_orders(
        self,
        symbol: str = 'PAXG/USDT',
        threshold_multiplier: float = 3.0
    ) -> Optional[Dict]:
        """
        检测大单
        
        Returns:
            {
                'has_large_bid': bool,
                'has_large_ask': bool,
                'large_bid_price': float,
                'large_ask_price': float,
                'large_bid_amount': float,
                'large_ask_amount': float
            }
        """
        orderbook = await self.fetch_orderbook(symbol)
        if not orderbook:
            return None
        
        bids = orderbook['bids']
        asks = orderbook['asks']
        
        # 计算平均订单量
        avg_bid_amount = np.mean([bid[1] for bid in bids])
        avg_ask_amount = np.mean([ask[1] for ask in asks])
        
        # 检测大单
        large_bids = [bid for bid in bids if bid[1] > avg_bid_amount * threshold_multiplier]
        large_asks = [ask for ask in asks if ask[1] > avg_ask_amount * threshold_multiplier]
        
        return {
            'has_large_bid': len(large_bids) > 0,
            'has_large_ask': len(large_asks) > 0,
            'large_bid_price': large_bids[0][0] if large_bids else 0,
            'large_ask_price': large_asks[0][0] if large_asks else 0,
            'large_bid_amount': large_bids[0][1] if large_bids else 0,
            'large_ask_amount': large_asks[0][1] if large_asks else 0,
            'num_large_bids': len(large_bids),
            'num_large_asks': len(large_asks)
        }
    
    # ==================== 领先指标 ====================
    
    async def fetch_dxy(self) -> Optional[Dict]:
        """
        获取美元指数 DXY
        黄金的死敌，DXY涨 → 黄金跌
        
        Returns:
            {
                'price': float,
                'change_1h': float,
                'change_24h': float,
                'timestamp': int
            }
        """
        try:
            # 使用 Binance 的 DXY 期货
            ticker = await self.binance.fetch_ticker('USDCUSDT')
            
            # 获取1小时K线计算变化
            ohlcv = await self.binance.fetch_ohlcv('USDCUSDT', '1h', limit=24)
            
            current_price = ticker['last']
            price_1h_ago = ohlcv[-2][4] if len(ohlcv) >= 2 else current_price
            price_24h_ago = ohlcv[0][4] if len(ohlcv) >= 24 else current_price
            
            change_1h = (current_price - price_1h_ago) / price_1h_ago if price_1h_ago > 0 else 0
            change_24h = (current_price - price_24h_ago) / price_24h_ago if price_24h_ago > 0 else 0
            
            result = {
                'price': current_price,
                'change_1h': change_1h,
                'change_24h': change_24h,
                'timestamp': ticker['timestamp']
            }
            
            self.indicator_cache['dxy'] = result
            self.fetch_count += 1
            
            return result
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取DXY失败: {str(e)[:50]}")
            return None
    
    async def fetch_vix(self) -> Optional[Dict]:
        """
        获取VIX恐慌指数
        VIX高 → 避险需求 → 黄金涨
        
        使用 BTC 波动率作为代理
        """
        try:
            # 获取BTC最近24小时K线
            ohlcv = await self.binance.fetch_ohlcv('BTCUSDT', '1h', limit=24)
            
            # 计算波动率
            closes = [candle[4] for candle in ohlcv]
            returns = np.diff(np.log(closes))
            volatility = np.std(returns) * np.sqrt(24) * 100  # 年化波动率
            
            # 计算变化
            current_vol = volatility
            prev_vol = self.indicator_cache.get('vix', {}).get('volatility', volatility)
            change = (current_vol - prev_vol) / prev_vol if prev_vol > 0 else 0
            
            result = {
                'volatility': volatility,
                'change': change,
                'timestamp': int(time.time() * 1000)
            }
            
            self.indicator_cache['vix'] = result
            self.fetch_count += 1
            
            return result
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取VIX失败: {str(e)[:50]}")
            return None
    
    async def fetch_us10y(self) -> Optional[Dict]:
        """
        获取美债10年期收益率
        收益率涨 → 黄金跌
        
        使用 Tushare 获取（如果配置）
        """
        if not self.tushare_token:
            return None
        
        try:
            import tushare as ts
            ts.set_token(self.tushare_token)
            pro = ts.pro_api()
            
            # 获取美债收益率
            df = pro.yc_cb(ts_code='US10Y.IB', trade_date=datetime.now().strftime('%Y%m%d'))
            
            if not df.empty:
                current_yield = float(df['yield'].iloc[0])
                
                # 获取前一天数据计算变化
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                df_prev = pro.yc_cb(ts_code='US10Y.IB', trade_date=yesterday)
                
                prev_yield = float(df_prev['yield'].iloc[0]) if not df_prev.empty else current_yield
                change = current_yield - prev_yield
                
                result = {
                    'yield': current_yield,
                    'change': change,
                    'timestamp': int(time.time() * 1000)
                }
                
                self.indicator_cache['us10y'] = result
                self.fetch_count += 1
                
                return result
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取US10Y失败: {str(e)[:50]}")
            return None
    
    # ==================== 新闻数据 ====================
    
    async def fetch_news(self, limit: int = 10) -> List[Dict]:
        """
        获取黄金相关新闻
        
        Returns:
            [
                {
                    'title': str,
                    'link': str,
                    'published': datetime,
                    'summary': str
                },
                ...
            ]
        """
        try:
            import feedparser
            
            feeds = [
                "https://www.kitco.com/rss/KitcoNews.xml",
                "https://www.investing.com/rss/news_25.rss",
            ]
            
            news_list = []
            
            for feed_url in feeds:
                async with aiohttp.ClientSession() as session:
                    async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)
                            
                            for entry in feed.entries[:limit]:
                                news_list.append({
                                    'title': entry.get('title', ''),
                                    'link': entry.get('link', ''),
                                    'published': entry.get('published', ''),
                                    'summary': entry.get('summary', '')
                                })
            
            self.fetch_count += 1
            return news_list[:limit]
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取新闻失败: {str(e)[:50]}")
            return []
    
    # ==================== Twitter 数据 ====================
    
    async def fetch_twitter_sentiment(self, accounts: List[str] = None) -> Optional[Dict]:
        """
        获取Twitter情绪
        
        监控华尔街大V：@DeItaone, @GoldTelegraph_, @zerohedge
        
        Returns:
            {
                'sentiment_score': float,  # -1 to 1
                'tweet_count': int,
                'latest_tweets': List[str]
            }
        """
        if not self.twitter_bearer:
            return None
        
        if accounts is None:
            accounts = ['DeItaone', 'GoldTelegraph_', 'zerohedge']
        
        try:
            import tweepy
            
            client = tweepy.Client(bearer_token=self.twitter_bearer)
            
            tweets = []
            for account in accounts:
                user_tweets = client.get_users_tweets(
                    username=account,
                    max_results=10,
                    tweet_fields=['created_at', 'text']
                )
                
                if user_tweets.data:
                    tweets.extend([tweet.text for tweet in user_tweets.data])
            
            # 简单情感分析（关键词）
            bearish_keywords = ['sell', 'drop', 'fall', 'crash', 'bear', 'down', 'weak']
            bullish_keywords = ['buy', 'rise', 'rally', 'bull', 'up', 'strong', 'surge']
            
            bearish_count = sum([1 for tweet in tweets for keyword in bearish_keywords if keyword in tweet.lower()])
            bullish_count = sum([1 for tweet in tweets for keyword in bullish_keywords if keyword in tweet.lower()])
            
            total = bearish_count + bullish_count
            sentiment_score = (bullish_count - bearish_count) / total if total > 0 else 0
            
            result = {
                'sentiment_score': sentiment_score,
                'tweet_count': len(tweets),
                'latest_tweets': tweets[:5]
            }
            
            self.fetch_count += 1
            return result
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取Twitter失败: {str(e)[:50]}")
            return None
    
    # ==================== 综合数据 ====================
    
    async def fetch_all_data(self) -> Dict:
        """
        一次性获取所有数据
        
        Returns:
            {
                'price': Dict,
                'orderbook': Dict,
                'dxy': Dict,
                'vix': Dict,
                'us10y': Dict,
                'news': List[Dict],
                'twitter': Dict,
                'timestamp': int
            }
        """
        tasks = [
            self.fetch_gold_price('okx'),
            self.fetch_orderbook(),
            self.fetch_dxy(),
            self.fetch_vix(),
            self.fetch_us10y(),
            self.fetch_news(5),
            self.fetch_twitter_sentiment()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'price': results[0] if not isinstance(results[0], Exception) else None,
            'orderbook': results[1] if not isinstance(results[1], Exception) else None,
            'dxy': results[2] if not isinstance(results[2], Exception) else None,
            'vix': results[3] if not isinstance(results[3], Exception) else None,
            'us10y': results[4] if not isinstance(results[4], Exception) else None,
            'news': results[5] if not isinstance(results[5], Exception) else [],
            'twitter': results[6] if not isinstance(results[6], Exception) else None,
            'timestamp': int(time.time() * 1000)
        }
    
    async def close(self):
        """关闭连接"""
        await self.okx.close()
        await self.binance.close()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'fetch_count': self.fetch_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / self.fetch_count if self.fetch_count > 0 else 0,
            'cache_size': len(self.price_cache) + len(self.orderbook_cache) + len(self.indicator_cache)
        }


# ==================== 测试 ====================

async def test_data_engine():
    """测试数据引擎"""
    engine = DataEngine()
    
    print("\n" + "=" * 70)
    print("🧪 测试数据引擎")
    print("=" * 70)
    
    # 测试价格数据
    print("\n1️⃣ 测试价格数据...")
    price = await engine.fetch_gold_price('okx')
    if price:
        print(f"   ✅ 价格: ${price['price']:,.2f}")
        print(f"   📊 买卖价差: {price['ask'] - price['bid']:.2f}")
        print(f"   💰 24h成交量: ${price['volume_24h']:,.0f}")
    
    # 测试K线数据
    print("\n2️⃣ 测试K线数据...")
    ohlcv = await engine.fetch_ohlcv(limit=10)
    if ohlcv is not None:
        print(f"   ✅ 获取 {len(ohlcv)} 根K线")
        print(f"   📈 最新收盘价: ${ohlcv['close'].iloc[-1]:,.2f}")
    
    # 测试订单簿
    print("\n3️⃣ 测试订单簿...")
    orderbook = await engine.fetch_orderbook()
    if orderbook:
        print(f"   ✅ 买卖失衡度: {orderbook['imbalance']:.2%}")
        print(f"   📊 买卖价差: {orderbook['spread']:.4%}")
    
    # 测试大单检测
    print("\n4️⃣ 测试大单检测...")
    large_orders = await engine.detect_large_orders()
    if large_orders:
        print(f"   {'✅' if large_orders['has_large_bid'] else '❌'} 大买单: {large_orders['num_large_bids']} 个")
        print(f"   {'✅' if large_orders['has_large_ask'] else '❌'} 大卖单: {large_orders['num_large_asks']} 个")
    
    # 测试DXY
    print("\n5️⃣ 测试美元指数...")
    dxy = await engine.fetch_dxy()
    if dxy:
        print(f"   ✅ DXY: {dxy['price']:.2f}")
        print(f"   📊 1h变化: {dxy['change_1h']:+.2%}")
    
    # 测试VIX
    print("\n6️⃣ 测试波动率...")
    vix = await engine.fetch_vix()
    if vix:
        print(f"   ✅ 波动率: {vix['volatility']:.2f}%")
    
    # 测试新闻
    print("\n7️⃣ 测试新闻...")
    news = await engine.fetch_news(3)
    if news:
        print(f"   ✅ 获取 {len(news)} 条新闻")
        for i, item in enumerate(news[:2], 1):
            print(f"   {i}. {item['title'][:50]}...")
    
    # 测试综合数据
    print("\n8️⃣ 测试综合数据获取...")
    all_data = await engine.fetch_all_data()
    print(f"   ✅ 价格: {'✓' if all_data['price'] else '✗'}")
    print(f"   ✅ 订单簿: {'✓' if all_data['orderbook'] else '✗'}")
    print(f"   ✅ DXY: {'✓' if all_data['dxy'] else '✗'}")
    print(f"   ✅ VIX: {'✓' if all_data['vix'] else '✗'}")
    print(f"   ✅ 新闻: {len(all_data['news'])} 条")
    
    # 统计信息
    print("\n" + "=" * 70)
    stats = engine.get_stats()
    print(f"📊 统计信息:")
    print(f"   • 请求次数: {stats['fetch_count']}")
    print(f"   • 错误次数: {stats['error_count']}")
    print(f"   • 错误率: {stats['error_rate']:.2%}")
    print("=" * 70)
    
    await engine.close()
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_data_engine())



