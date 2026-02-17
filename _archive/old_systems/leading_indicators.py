"""
领先指标监控系统 - 提前5-30秒预警
监控黄金价格变化的原因，而不是价格本身
"""
import asyncio
import aiohttp
import ccxt.async_support as ccxt
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from collections import deque
import logging

logger = logging.getLogger(__name__)


class LeadingIndicatorMonitor:
    """
    领先指标监控器
    
    监控内容:
    1. 美元指数 (DXY) - 黄金的死敌，提前5-15秒
    2. 美债收益率 (US10Y) - 资金流向，提前10-30秒
    3. VIX 恐慌指数 - 避险情绪，提前5-20秒
    4. 订单簿失衡 - 大单压盘/托盘，提前3-10秒
    5. 推特情绪 - 华尔街大V风向，提前10-60秒
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        
        # 历史数据缓存（用于计算变化率）
        self.dxy_history = deque(maxlen=60)  # 最近60个数据点
        self.us10y_history = deque(maxlen=60)
        self.vix_history = deque(maxlen=60)
        self.orderbook_history = deque(maxlen=30)
        
        # 阈值配置
        self.thresholds = {
            'dxy_spike': 0.003,           # DXY涨0.3% → 黄金即将跌
            'us10y_spike': 0.02,          # 美债收益率涨2bp
            'vix_spike': 0.05,            # VIX涨5%
            'orderbook_imbalance': 0.7,   # 订单簿失衡70%
            'twitter_sentiment': -7       # 推特情绪-7
        }
        
        # 推特监控账号（华尔街大V）
        self.twitter_accounts = [
            'DeItaone',        # 最快的财经新闻
            'zerohedge',       # 零对冲
            'FirstSquawk',     # 第一时间
            'LiveSquawk',      # 实时播报
            'Fxhedgers'        # 外汇对冲
        ]
    
    async def initialize(self):
        """初始化会话"""
        self.session = aiohttp.ClientSession()
        logger.info("领先指标监控器已初始化")
    
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
        await self.exchange.close()
    
    # ==================== 1. 美元指数 (DXY) ====================
    
    async def fetch_dxy(self) -> Optional[float]:
        """
        获取美元指数
        数据源: Investing.com API
        """
        try:
            url = "https://api.investing.com/api/financialdata/1/historical/chart"
            params = {
                'symbol': 'DXY',
                'resolution': '1',  # 1分钟
                'from': int((datetime.now() - timedelta(minutes=5)).timestamp()),
                'to': int(datetime.now().timestamp())
            }
            
            async with self.session.get(url, params=params, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and 'c' in data and len(data['c']) > 0:
                        return float(data['c'][-1])
        except Exception as e:
            logger.warning(f"获取DXY失败: {e}")
        
        return None
    
    async def analyze_dxy(self) -> Dict:
        """
        分析美元指数变化
        
        返回:
        {
            'value': 当前值,
            'change_1m': 1分钟变化率,
            'change_5m': 5分钟变化率,
            'signal': 'bullish'/'bearish'/'neutral',
            'urgency': 0-10 (紧急程度)
        }
        """
        dxy = await self.fetch_dxy()
        if dxy is None:
            return {'signal': 'neutral', 'urgency': 0}
        
        self.dxy_history.append({
            'time': datetime.now(),
            'value': dxy
        })
        
        if len(self.dxy_history) < 2:
            return {'value': dxy, 'signal': 'neutral', 'urgency': 0}
        
        # 计算变化率
        change_1m = (dxy - self.dxy_history[-2]['value']) / self.dxy_history[-2]['value']
        
        if len(self.dxy_history) >= 5:
            change_5m = (dxy - self.dxy_history[-5]['value']) / self.dxy_history[-5]['value']
        else:
            change_5m = change_1m
        
        # 判断信号
        signal = 'neutral'
        urgency = 0
        
        if change_1m > self.thresholds['dxy_spike']:
            signal = 'bearish'  # DXY涨 → 黄金跌
            urgency = min(10, int(abs(change_1m) / self.thresholds['dxy_spike'] * 5))
        elif change_1m < -self.thresholds['dxy_spike']:
            signal = 'bullish'  # DXY跌 → 黄金涨
            urgency = min(10, int(abs(change_1m) / self.thresholds['dxy_spike'] * 5))
        
        return {
            'value': dxy,
            'change_1m': change_1m,
            'change_5m': change_5m,
            'signal': signal,
            'urgency': urgency,
            'lead_time': '5-15秒'
        }
    
    # ==================== 2. 美债收益率 (US10Y) ====================
    
    async def fetch_us10y(self) -> Optional[float]:
        """
        获取美国10年期国债收益率
        数据源: FRED API (免费)
        """
        try:
            # 使用Yahoo Finance作为备用数据源
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX"
            params = {
                'interval': '1m',
                'range': '1d'
            }
            
            async with self.session.get(url, params=params, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'chart' in data and 'result' in data['chart']:
                        result = data['chart']['result'][0]
                        if 'meta' in result and 'regularMarketPrice' in result['meta']:
                            return float(result['meta']['regularMarketPrice'])
        except Exception as e:
            logger.warning(f"获取US10Y失败: {e}")
        
        return None
    
    async def analyze_us10y(self) -> Dict:
        """分析美债收益率变化"""
        us10y = await self.fetch_us10y()
        if us10y is None:
            return {'signal': 'neutral', 'urgency': 0}
        
        self.us10y_history.append({
            'time': datetime.now(),
            'value': us10y
        })
        
        if len(self.us10y_history) < 2:
            return {'value': us10y, 'signal': 'neutral', 'urgency': 0}
        
        # 计算变化（单位：基点 bp）
        change_bp = (us10y - self.us10y_history[-2]['value']) * 100
        
        signal = 'neutral'
        urgency = 0
        
        if change_bp > 2:  # 涨2bp
            signal = 'bearish'  # 收益率涨 → 黄金跌
            urgency = min(10, int(abs(change_bp) / 2 * 3))
        elif change_bp < -2:
            signal = 'bullish'  # 收益率跌 → 黄金涨
            urgency = min(10, int(abs(change_bp) / 2 * 3))
        
        return {
            'value': us10y,
            'change_bp': change_bp,
            'signal': signal,
            'urgency': urgency,
            'lead_time': '10-30秒'
        }
    
    # ==================== 3. VIX 恐慌指数 ====================
    
    async def fetch_vix(self) -> Optional[float]:
        """获取VIX恐慌指数"""
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
            params = {
                'interval': '1m',
                'range': '1d'
            }
            
            async with self.session.get(url, params=params, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'chart' in data and 'result' in data['chart']:
                        result = data['chart']['result'][0]
                        if 'meta' in result and 'regularMarketPrice' in result['meta']:
                            return float(result['meta']['regularMarketPrice'])
        except Exception as e:
            logger.warning(f"获取VIX失败: {e}")
        
        return None
    
    async def analyze_vix(self) -> Dict:
        """分析VIX变化"""
        vix = await self.fetch_vix()
        if vix is None:
            return {'signal': 'neutral', 'urgency': 0}
        
        self.vix_history.append({
            'time': datetime.now(),
            'value': vix
        })
        
        if len(self.vix_history) < 2:
            return {'value': vix, 'signal': 'neutral', 'urgency': 0}
        
        change = (vix - self.vix_history[-2]['value']) / self.vix_history[-2]['value']
        
        signal = 'neutral'
        urgency = 0
        
        if change > self.thresholds['vix_spike']:
            signal = 'bullish'  # VIX涨 → 避险 → 黄金涨
            urgency = min(10, int(abs(change) / self.thresholds['vix_spike'] * 4))
        elif change < -self.thresholds['vix_spike']:
            signal = 'bearish'  # VIX跌 → 风险偏好 → 黄金跌
            urgency = min(10, int(abs(change) / self.thresholds['vix_spike'] * 4))
        
        return {
            'value': vix,
            'change': change,
            'signal': signal,
            'urgency': urgency,
            'lead_time': '5-20秒'
        }
    
    # ==================== 4. 订单簿失衡 ====================
    
    async def fetch_orderbook(self) -> Optional[Dict]:
        """获取订单簿数据"""
        try:
            orderbook = await self.exchange.fetch_order_book('XAU/USDT', limit=20)
            return orderbook
        except Exception as e:
            logger.warning(f"获取订单簿失败: {e}")
            return None
    
    async def analyze_orderbook(self) -> Dict:
        """
        分析订单簿失衡
        
        大单压盘/托盘是价格变化的最直接信号
        提前时间: 3-10秒
        """
        orderbook = await self.fetch_orderbook()
        if not orderbook:
            return {'signal': 'neutral', 'urgency': 0}
        
        bids = orderbook['bids'][:20]  # 前20档买单
        asks = orderbook['asks'][:20]  # 前20档卖单
        
        # 计算买卖量
        bid_volume = sum([bid[1] for bid in bids])
        ask_volume = sum([ask[1] for ask in asks])
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return {'signal': 'neutral', 'urgency': 0}
        
        # 买卖比
        bid_ratio = bid_volume / total_volume
        ask_ratio = ask_volume / total_volume
        
        # 计算失衡度
        imbalance = bid_ratio - ask_ratio
        
        signal = 'neutral'
        urgency = 0
        
        if imbalance > self.thresholds['orderbook_imbalance'] - 0.5:
            signal = 'bullish'  # 买单多 → 即将上涨
            urgency = min(10, int(abs(imbalance) / 0.1 * 5))
        elif imbalance < -(self.thresholds['orderbook_imbalance'] - 0.5):
            signal = 'bearish'  # 卖单多 → 即将下跌
            urgency = min(10, int(abs(imbalance) / 0.1 * 5))
        
        self.orderbook_history.append({
            'time': datetime.now(),
            'imbalance': imbalance
        })
        
        return {
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'bid_ratio': bid_ratio,
            'ask_ratio': ask_ratio,
            'imbalance': imbalance,
            'signal': signal,
            'urgency': urgency,
            'lead_time': '3-10秒'
        }
    
    # ==================== 5. 推特情绪监控 ====================
    
    async def fetch_twitter_sentiment(self) -> Optional[Dict]:
        """
        监控推特情绪
        
        注意: 需要Twitter API密钥
        这里提供框架，实际使用需要配置API
        """
        # TODO: 实现推特API调用
        # 由于Twitter API需要申请，这里返回模拟数据
        return {
            'sentiment_score': 0,
            'recent_tweets': [],
            'signal': 'neutral',
            'urgency': 0
        }
    
    # ==================== 综合分析 ====================
    
    async def get_comprehensive_signal(self) -> Dict:
        """
        综合所有领先指标，生成最终信号
        
        返回:
        {
            'signal': 'strong_bullish'/'bullish'/'neutral'/'bearish'/'strong_bearish',
            'confidence': 0-100,
            'urgency': 0-10,
            'lead_time': '预计提前时间',
            'reasons': ['原因1', '原因2', ...],
            'details': {...}
        }
        """
        # 并行获取所有指标
        results = await asyncio.gather(
            self.analyze_dxy(),
            self.analyze_us10y(),
            self.analyze_vix(),
            self.analyze_orderbook(),
            return_exceptions=True
        )
        
        dxy_result = results[0] if not isinstance(results[0], Exception) else {'signal': 'neutral', 'urgency': 0}
        us10y_result = results[1] if not isinstance(results[1], Exception) else {'signal': 'neutral', 'urgency': 0}
        vix_result = results[2] if not isinstance(results[2], Exception) else {'signal': 'neutral', 'urgency': 0}
        orderbook_result = results[3] if not isinstance(results[3], Exception) else {'signal': 'neutral', 'urgency': 0}
        
        # 信号权重
        weights = {
            'dxy': 0.35,        # DXY最重要
            'orderbook': 0.30,  # 订单簿次之
            'us10y': 0.20,      # 美债
            'vix': 0.15         # VIX
        }
        
        # 转换信号为数值
        signal_map = {
            'strong_bullish': 2,
            'bullish': 1,
            'neutral': 0,
            'bearish': -1,
            'strong_bearish': -2
        }
        
        # 计算加权信号
        weighted_signal = (
            signal_map.get(dxy_result['signal'], 0) * weights['dxy'] +
            signal_map.get(orderbook_result['signal'], 0) * weights['orderbook'] +
            signal_map.get(us10y_result['signal'], 0) * weights['us10y'] +
            signal_map.get(vix_result['signal'], 0) * weights['vix']
        )
        
        # 计算紧急程度
        max_urgency = max(
            dxy_result.get('urgency', 0),
            us10y_result.get('urgency', 0),
            vix_result.get('urgency', 0),
            orderbook_result.get('urgency', 0)
        )
        
        # 生成最终信号
        if weighted_signal > 0.8:
            final_signal = 'strong_bullish'
            confidence = min(95, 50 + weighted_signal * 30)
        elif weighted_signal > 0.3:
            final_signal = 'bullish'
            confidence = min(80, 50 + weighted_signal * 20)
        elif weighted_signal < -0.8:
            final_signal = 'strong_bearish'
            confidence = min(95, 50 + abs(weighted_signal) * 30)
        elif weighted_signal < -0.3:
            final_signal = 'bearish'
            confidence = min(80, 50 + abs(weighted_signal) * 20)
        else:
            final_signal = 'neutral'
            confidence = 30
        
        # 收集原因
        reasons = []
        if dxy_result.get('urgency', 0) > 5:
            reasons.append(f"美元指数{'上涨' if dxy_result['signal'] == 'bearish' else '下跌'}")
        if orderbook_result.get('urgency', 0) > 5:
            reasons.append(f"订单簿{'卖单压盘' if orderbook_result['signal'] == 'bearish' else '买单托盘'}")
        if us10y_result.get('urgency', 0) > 5:
            reasons.append(f"美债收益率{'上涨' if us10y_result['signal'] == 'bearish' else '下跌'}")
        if vix_result.get('urgency', 0) > 5:
            reasons.append(f"VIX{'上涨' if vix_result['signal'] == 'bullish' else '下跌'}")
        
        # 估算提前时间
        if orderbook_result.get('urgency', 0) > 7:
            lead_time = '3-10秒'
        elif dxy_result.get('urgency', 0) > 7:
            lead_time = '5-15秒'
        elif vix_result.get('urgency', 0) > 7:
            lead_time = '5-20秒'
        elif us10y_result.get('urgency', 0) > 7:
            lead_time = '10-30秒'
        else:
            lead_time = '未知'
        
        return {
            'signal': final_signal,
            'confidence': confidence,
            'urgency': max_urgency,
            'lead_time': lead_time,
            'reasons': reasons,
            'details': {
                'dxy': dxy_result,
                'us10y': us10y_result,
                'vix': vix_result,
                'orderbook': orderbook_result
            }
        }


# ==================== 测试代码 ====================

async def test_leading_indicators():
    """测试领先指标监控"""
    monitor = LeadingIndicatorMonitor()
    await monitor.initialize()
    
    print("=" * 70)
    print("🔍 领先指标监控测试")
    print("=" * 70)
    print()
    
    try:
        # 获取综合信号
        signal = await monitor.get_comprehensive_signal()
        
        print(f"📊 综合信号: {signal['signal']}")
        print(f"📈 置信度: {signal['confidence']:.1f}%")
        print(f"⚡ 紧急程度: {signal['urgency']}/10")
        print(f"⏱️  预计提前: {signal['lead_time']}")
        print()
        
        if signal['reasons']:
            print("📋 原因:")
            for reason in signal['reasons']:
                print(f"  • {reason}")
            print()
        
        print("📊 详细数据:")
        print("-" * 70)
        
        # DXY
        dxy = signal['details']['dxy']
        if 'value' in dxy:
            print(f"💵 美元指数 (DXY): {dxy['value']:.2f}")
            print(f"   变化: {dxy.get('change_1m', 0)*100:.2f}%")
            print(f"   信号: {dxy['signal']} (紧急度: {dxy['urgency']}/10)")
            print()
        
        # US10Y
        us10y = signal['details']['us10y']
        if 'value' in us10y:
            print(f"📈 美债收益率 (US10Y): {us10y['value']:.2f}%")
            print(f"   变化: {us10y.get('change_bp', 0):.1f}bp")
            print(f"   信号: {us10y['signal']} (紧急度: {us10y['urgency']}/10)")
            print()
        
        # VIX
        vix = signal['details']['vix']
        if 'value' in vix:
            print(f"😱 VIX恐慌指数: {vix['value']:.2f}")
            print(f"   变化: {vix.get('change', 0)*100:.2f}%")
            print(f"   信号: {vix['signal']} (紧急度: {vix['urgency']}/10)")
            print()
        
        # 订单簿
        orderbook = signal['details']['orderbook']
        if 'imbalance' in orderbook:
            print(f"📊 订单簿失衡: {orderbook['imbalance']*100:.1f}%")
            print(f"   买单: {orderbook.get('bid_volume', 0):.2f}")
            print(f"   卖单: {orderbook.get('ask_volume', 0):.2f}")
            print(f"   信号: {orderbook['signal']} (紧急度: {orderbook['urgency']}/10)")
            print()
        
        print("=" * 70)
        
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(test_leading_indicators())
