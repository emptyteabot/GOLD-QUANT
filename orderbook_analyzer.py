"""
订单簿深度分析
"""
import logging
import numpy as np
from typing import Dict

logger = logging.getLogger(__name__)


class OrderbookAnalyzer:
    """订单簿分析器"""
    
    def __init__(self):
        logger.info("✅ 订单簿分析器初始化")
    
    async def analyze(self, okx_client) -> Dict:
        """分析订单簿"""
        try:
            # 获取订单簿
            orderbook = await okx_client.get_orderbook(depth=100)
            
            if not orderbook:
                return {'signal': 0, 'imbalance': 0}
            
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            # 计算买卖量
            bid_volume = sum(float(b[1]) for b in bids[:20])
            ask_volume = sum(float(a[1]) for a in asks[:20])
            
            # 订单流失衡
            total_volume = bid_volume + ask_volume
            if total_volume > 0:
                imbalance = (bid_volume - ask_volume) / total_volume
            else:
                imbalance = 0
            
            # 大单墙检测
            avg_bid = bid_volume / 20 if len(bids) >= 20 else 0
            avg_ask = ask_volume / 20 if len(asks) >= 20 else 0
            
            big_bid_wall = any(float(b[1]) > avg_bid * 10 for b in bids[:5])
            big_ask_wall = any(float(a[1]) > avg_ask * 10 for a in asks[:5])
            
            # 信号
            signal = imbalance
            
            if big_bid_wall:
                signal += 0.3
                logger.info("🛡️ 检测到大买单墙")
            
            if big_ask_wall:
                signal -= 0.3
                logger.info("🧱 检测到大卖单墙")
            
            signal = np.clip(signal, -1, 1)
            
            logger.info(f"📊 订单簿: 失衡={imbalance:+.2f} 信号={signal:+.2f}")
            
            return {
                'signal': signal,
                'imbalance': imbalance,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'big_bid_wall': big_bid_wall,
                'big_ask_wall': big_ask_wall
            }
            
        except Exception as e:
            logger.error(f"❌ 订单簿分析失败: {e}")
            return {'signal': 0, 'imbalance': 0}
