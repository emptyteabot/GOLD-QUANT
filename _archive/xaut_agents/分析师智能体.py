"""
分析师智能体 (The Analyst)
职能：认知层 - 计算公允价值、价差Z-Score、订单簿失衡率
运行频率：100ms - 500ms
"""

import asyncio
import numpy as np
from collections import deque
from typing import Dict, Optional, Tuple
import redis
import json
import time
import logging
from dataclasses import dataclass
import ccxt.async_support as ccxt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("分析师")


@dataclass
class AnalysisSignal:
    """分析信号"""
    action: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    confidence: float  # 0-1
    target_price: float
    reasoning: Dict
    timestamp: float


class 公允价值计算器:
    """技能4: 公允价值与价差计算 (Fair Value & Z-Score)"""
    
    def __init__(self, window_size: int = 3600):
        self.window_size = window_size  # 1小时滚动窗口
        self.spread_history = deque(maxlen=window_size)
        
    def calculate_fair_value(self, xau_usd: float, usdt_usd: float) -> float:
        """
        计算XAUT公允价值
        
        公式: Fair Value = XAU/USD × USDT/USD
        
        参数:
            xau_usd: 现货黄金价格 (来自OANDA)
            usdt_usd: USDT汇率 (来自Kraken)
        """
        fair_value = xau_usd * usdt_usd
        return fair_value
    
    def calculate_spread(self, xaut_price: float, fair_value: float) -> float:
        """
        计算价差百分比
        
        Spread% = (XAUT_CEX - Fair_Value) / Fair_Value
        
        负值 = XAUT被低估 = 买入机会
        """
        spread_pct = (xaut_price - fair_value) / fair_value
        return spread_pct
    
    def calculate_z_score(self, current_spread: float) -> float:
        """
        计算价差的Z-Score
        
        Z = (Spread_t - μ_spread) / σ_spread
        
        Z < -3: 极度低估，统计学异常值
        Z > +3: 极度高估
        """
        self.spread_history.append(current_spread)
        
        if len(self.spread_history) < 100:
            return 0.0  # 数据不足
        
        spreads = np.array(self.spread_history)
        mean = np.mean(spreads)
        std = np.std(spreads)
        
        if std == 0:
            return 0.0
        
        z_score = (current_spread - mean) / std
        return z_score
    
    def generate_signal(self, z_score: float, spread_pct: float) -> Optional[AnalysisSignal]:
        """
        基于Z-Score生成交易信号
        
        策略：
        - Z < -3: STRONG_BUY (极度低估)
        - Z < -2: BUY
        - -2 < Z < 2: HOLD
        - Z > 2: SELL
        - Z > 3: STRONG_SELL
        """
        if z_score < -3:
            return AnalysisSignal(
                action="STRONG_BUY",
                confidence=min(abs(z_score) / 5, 1.0),
                target_price=0,  # 由狙击手计算
                reasoning={
                    "z_score": z_score,
                    "spread_pct": spread_pct,
                    "interpretation": "统计学异常低估，暴跌反弹机会"
                },
                timestamp=time.time()
            )
        elif z_score < -2:
            return AnalysisSignal(
                action="BUY",
                confidence=abs(z_score) / 3,
                target_price=0,
                reasoning={
                    "z_score": z_score,
                    "spread_pct": spread_pct,
                    "interpretation": "显著低估"
                },
                timestamp=time.time()
            )
        elif z_score > 3:
            return AnalysisSignal(
                action="STRONG_SELL",
                confidence=min(z_score / 5, 1.0),
                target_price=0,
                reasoning={
                    "z_score": z_score,
                    "spread_pct": spread_pct,
                    "interpretation": "极度高估，泡沫风险"
                },
                timestamp=time.time()
            )
        
        return None


class 订单簿分析器:
    """技能5: 订单簿失衡率 (Order Book Imbalance, OBI)"""
    
    def __init__(self, depth: int = 10):
        self.depth = depth  # 分析前N档深度
        
    def calculate_obi(self, order_book: Dict) -> float:
        """
        计算订单簿失衡率
        
        OBI = (∑V_bids - ∑V_asks) / (∑V_bids + ∑V_asks)
        
        OBI → +1: 买盘占优
        OBI → -1: 卖盘占优
        OBI → 0: 平衡
        """
        bids = order_book.get('bids', [])[:self.depth]
        asks = order_book.get('asks', [])[:self.depth]
        
        total_bid_volume = sum(price * volume for price, volume in bids)
        total_ask_volume = sum(price * volume for price, volume in asks)
        
        if total_bid_volume + total_ask_volume == 0:
            return 0.0
        
        obi = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume)
        return obi
    
    def detect_absorption(self, obi_history: deque) -> bool:
        """
        检测大资金吸筹（Absorption）
        
        信号：价格创新低，但OBI从-0.9回升至-0.6
        这意味着卖方力量枯竭，巨鲸开始挂单吸筹
        """
        if len(obi_history) < 10:
            return False
        
        recent_obi = list(obi_history)[-10:]
        
        # 检测OBI底背离
        if recent_obi[0] < -0.8 and recent_obi[-1] > -0.6:
            logger.info(f"🎯 检测到吸筹信号: OBI从{recent_obi[0]:.2f}回升至{recent_obi[-1]:.2f}")
            return True
        
        return False


class 成交量分析器:
    """技能6: 成交量高潮识别 (Volume Climax Identification)"""
    
    def __init__(self, lookback: int = 50):
        self.lookback = lookback
        self.volume_history = deque(maxlen=lookback)
        
    def detect_climax(self, current_volume: float, price_change: float) -> bool:
        """
        识别恐慌抛售高潮
        
        条件：
        1. 成交量 > 5× 平均成交量
        2. K线为大阴线（跌幅>2%）
        
        策略：不在Climax Candle立即买入，等待下一根K线确认不再创新低
        """
        self.volume_history.append(current_volume)
        
        if len(self.volume_history) < self.lookback:
            return False
        
        avg_volume = np.mean(self.volume_history)
        
        is_climax = (
            current_volume > 5 * avg_volume and
            price_change < -0.02  # 跌幅超过2%
        )
        
        if is_climax:
            logger.warning(f"📊 成交量高潮: 当前{current_volume:.0f} vs 平均{avg_volume:.0f}")
        
        return is_climax


class 分析师智能体:
    """
    分析师智能体主控制器
    
    职责：
    1. 实时计算XAUT公允价值
    2. 监控订单簿失衡
    3. 识别成交量异常
    4. 生成量化交易信号
    """
    
    def __init__(self, redis_host: str = 'localhost'):
        self.redis_client = redis.Redis(host=redis_host, decode_responses=True)
        
        self.公允价值 = 公允价值计算器(window_size=3600)
        self.订单簿 = 订单簿分析器(depth=10)
        self.成交量 = 成交量分析器(lookback=50)
        
        self.obi_history = deque(maxlen=100)
        
        # 交易所连接
        self.exchanges = {
            'okx': ccxt.okx({'enableRateLimit': True}),
            'bybit': ccxt.bybit({'enableRateLimit': True})
        }
        
    async def fetch_xau_spot_price(self) -> float:
        """获取现货黄金价格（OANDA或其他数据源）"""
        # 实际需要OANDA API
        # 这里使用模拟数据
        return 2650.0  # $2650/盎司
    
    async def fetch_usdt_rate(self) -> float:
        """获取USDT汇率（Kraken USDT/USD）"""
        try:
            ticker = await self.exchanges['okx'].fetch_ticker('USDT/USD')
            return ticker['last']
        except:
            return 1.0  # 默认1:1
    
    async def fetch_xaut_price(self, exchange: str = 'okx') -> float:
        """获取XAUT/USDT价格"""
        try:
            ticker = await self.exchanges[exchange].fetch_ticker('XAUT/USDT')
            return ticker['last']
        except Exception as e:
            logger.error(f"获取XAUT价格失败: {e}")
            return 0.0
    
    async def fetch_order_book(self, exchange: str = 'okx') -> Dict:
        """获取订单簿"""
        try:
            order_book = await self.exchanges[exchange].fetch_order_book('XAUT/USDT')
            return order_book
        except Exception as e:
            logger.error(f"获取订单簿失败: {e}")
            return {'bids': [], 'asks': []}
    
    async def analyze_market(self):
        """主分析循环"""
        logger.info("🧠 分析师智能体启动")
        
        while True:
            try:
                # 1. 获取所有必要数据
                xau_spot = await self.fetch_xau_spot_price()
                usdt_rate = await self.fetch_usdt_rate()
                xaut_price = await self.fetch_xaut_price('okx')
                order_book = await self.fetch_order_book('okx')
                
                # 2. 计算公允价值与价差
                fair_value = self.公允价值.calculate_fair_value(xau_spot, usdt_rate)
                spread_pct = self.公允价值.calculate_spread(xaut_price, fair_value)
                z_score = self.公允价值.calculate_z_score(spread_pct)
                
                # 3. 计算订单簿失衡
                obi = self.订单簿.calculate_obi(order_book)
                self.obi_history.append(obi)
                absorption_detected = self.订单簿.detect_absorption(self.obi_history)
                
                # 4. 生成信号
                signal = self.公允价值.generate_signal(z_score, spread_pct)
                
                # 5. 增强信号（结合OBI）
                if signal and signal.action in ["STRONG_BUY", "BUY"]:
                    if absorption_detected:
                        signal.confidence = min(signal.confidence * 1.5, 1.0)
                        signal.reasoning['obi_absorption'] = True
                        logger.info(f"💎 信号增强: 检测到吸筹行为")
                
                # 6. 发布信号
                if signal:
                    self.publish_analysis(signal, {
                        'fair_value': fair_value,
                        'xaut_price': xaut_price,
                        'spread_pct': spread_pct,
                        'z_score': z_score,
                        'obi': obi
                    })
                
                # 7. 更新Redis状态
                self.redis_client.hset('market_state', mapping={
                    'xaut_price': xaut_price,
                    'fair_value': fair_value,
                    'spread_pct': spread_pct,
                    'z_score': z_score,
                    'obi': obi,
                    'timestamp': time.time()
                })
                
                await asyncio.sleep(0.5)  # 500ms更新频率
                
            except Exception as e:
                logger.error(f"分析循环错误: {e}")
                await asyncio.sleep(1)
    
    def publish_analysis(self, signal: AnalysisSignal, market_data: Dict):
        """发布分析信号到Redis"""
        message = {
            'signal': signal.__dict__,
            'market_data': market_data
        }
        self.redis_client.publish('signal:ANALYSIS', json.dumps(message))
        logger.info(f"📊 发布分析: {signal.action} (置信度: {signal.confidence:.2%})")
    
    async def close(self):
        """关闭交易所连接"""
        for exchange in self.exchanges.values():
            await exchange.close()


if __name__ == "__main__":
    analyst = 分析师智能体()
    try:
        asyncio.run(analyst.analyze_market())
    finally:
        asyncio.run(analyst.close())

