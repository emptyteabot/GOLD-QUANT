"""
多周期监控模块
同时监控15分钟、5分钟、1分钟K线
敏锐捕捉暴跌和反转信号
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MultiTimeframeMonitor:
    """多周期监控器"""
    
    def __init__(self):
        self.last_alert_time = {}
        
    def analyze_all_timeframes(
        self, 
        klines_15m: pd.DataFrame,
        klines_5m: pd.DataFrame, 
        klines_1m: pd.DataFrame,
        current_price: float
    ) -> Dict:
        """
        分析所有周期
        
        返回：
        {
            'crash_detected': bool,      # 是否检测到暴跌
            'reversal_detected': bool,   # 是否检测到反转
            'signal': str,               # 'LONG', 'SHORT', 'HOLD'
            'urgency': str,              # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
            'reason': str,               # 原因说明
            'details': dict              # 详细数据
        }
        """
        result = {
            'crash_detected': False,
            'reversal_detected': False,
            'signal': 'HOLD',
            'urgency': 'LOW',
            'reason': '',
            'details': {}
        }
        
        # 1. 检测暴跌（优先级最高）
        crash_result = self._detect_crash(klines_15m, klines_5m, klines_1m, current_price)
        if crash_result['detected']:
            result['crash_detected'] = True
            result['signal'] = 'SHORT'
            result['urgency'] = 'CRITICAL'
            result['reason'] = crash_result['reason']
            result['details']['crash'] = crash_result
            
            logger.warning(f"🔴🔴🔴 暴跌检测！{crash_result['reason']}")
            return result
        
        # 2. 检测反转（次优先级）
        reversal_result = self._detect_reversal(klines_15m, klines_5m, klines_1m, current_price)
        if reversal_result['detected']:
            result['reversal_detected'] = True
            result['signal'] = 'LONG'
            result['urgency'] = 'HIGH'
            result['reason'] = reversal_result['reason']
            result['details']['reversal'] = reversal_result
            
            logger.info(f"🟢🟢🟢 反转检测！{reversal_result['reason']}")
            return result
        
        # 3. 常规分析
        result['details']['15m'] = self._analyze_timeframe(klines_15m, '15m')
        result['details']['5m'] = self._analyze_timeframe(klines_5m, '5m')
        result['details']['1m'] = self._analyze_timeframe(klines_1m, '1m')
        
        return result
    
    def _detect_crash(
        self, 
        klines_15m: pd.DataFrame,
        klines_5m: pd.DataFrame,
        klines_1m: pd.DataFrame,
        current_price: float
    ) -> Dict:
        """
        检测暴跌
        
        条件：
        1. 1分钟跌幅 > 0.5%
        2. 5分钟跌幅 > 1.0%
        3. 15分钟跌幅 > 2.0%
        4. ADX > 20（强趋势）
        5. RSI < 40（偏弱）
        """
        result = {
            'detected': False,
            'reason': '',
            'severity': 0,  # 0-100
            'timeframes': {}
        }
        
        # 计算各周期跌幅
        drop_1m = self._calculate_drop(klines_1m, periods=1)
        drop_5m = self._calculate_drop(klines_5m, periods=5)
        drop_15m = self._calculate_drop(klines_15m, periods=15)
        
        result['timeframes'] = {
            '1m': drop_1m,
            '5m': drop_5m,
            '15m': drop_15m
        }
        
        # 计算技术指标
        rsi_15m = self._calculate_rsi(klines_15m)
        adx_15m = self._calculate_adx(klines_15m)
        
        # 判断暴跌级别
        severity = 0
        reasons = []
        
        # 1分钟暴跌
        if drop_1m < -0.5:
            severity += 20
            reasons.append(f"1分钟跌{abs(drop_1m):.2f}%")
        
        # 5分钟暴跌
        if drop_5m < -1.0:
            severity += 30
            reasons.append(f"5分钟跌{abs(drop_5m):.2f}%")
        
        # 15分钟暴跌
        if drop_15m < -2.0:
            severity += 40
            reasons.append(f"15分钟跌{abs(drop_15m):.2f}%")
        
        # 强趋势确认
        if adx_15m > 20:
            severity += 10
            reasons.append(f"ADX={adx_15m:.1f}")
        
        # 超卖确认
        if rsi_15m < 40:
            severity += 10
            reasons.append(f"RSI={rsi_15m:.1f}")
        
        result['severity'] = severity
        
        # 判断是否触发
        if severity >= 50:  # 至少50分才触发
            result['detected'] = True
            result['reason'] = "暴跌：" + "，".join(reasons)
        
        return result
    
    def _detect_reversal(
        self,
        klines_15m: pd.DataFrame,
        klines_5m: pd.DataFrame,
        klines_1m: pd.DataFrame,
        current_price: float
    ) -> Dict:
        """
        检测反转
        
        条件：
        1. RSI < 30（超卖）
        2. MACD金叉
        3. 成交量放大（> 1.5倍均值）
        4. K线形态（锤子线/启明星）
        5. 价格止跌企稳
        """
        result = {
            'detected': False,
            'reason': '',
            'confidence': 0,  # 0-100
            'signals': []
        }
        
        # 计算技术指标
        rsi_15m = self._calculate_rsi(klines_15m)
        rsi_5m = self._calculate_rsi(klines_5m)
        
        macd_15m = self._calculate_macd(klines_15m)
        macd_5m = self._calculate_macd(klines_5m)
        
        volume_ratio_15m = self._calculate_volume_ratio(klines_15m)
        volume_ratio_5m = self._calculate_volume_ratio(klines_5m)
        
        # 判断反转信号
        confidence = 0
        signals = []
        
        # 1. 超卖
        if rsi_15m < 30:
            confidence += 30
            signals.append(f"15m RSI={rsi_15m:.1f}超卖")
        elif rsi_5m < 30:
            confidence += 20
            signals.append(f"5m RSI={rsi_5m:.1f}超卖")
        
        # 2. MACD金叉
        if macd_15m['golden_cross']:
            confidence += 25
            signals.append("15m MACD金叉")
        elif macd_5m['golden_cross']:
            confidence += 15
            signals.append("5m MACD金叉")
        
        # 3. 成交量放大
        if volume_ratio_15m > 1.5:
            confidence += 20
            signals.append(f"15m成交量{volume_ratio_15m:.1f}x")
        elif volume_ratio_5m > 1.5:
            confidence += 10
            signals.append(f"5m成交量{volume_ratio_5m:.1f}x")
        
        # 4. K线形态
        pattern_15m = self._detect_reversal_pattern(klines_15m)
        pattern_5m = self._detect_reversal_pattern(klines_5m)
        
        if pattern_15m:
            confidence += 15
            signals.append(f"15m {pattern_15m}")
        elif pattern_5m:
            confidence += 10
            signals.append(f"5m {pattern_5m}")
        
        # 5. 价格止跌
        if self._is_price_stabilizing(klines_1m):
            confidence += 10
            signals.append("价格止跌")
        
        result['confidence'] = confidence
        result['signals'] = signals
        
        # 判断是否触发（至少60分）
        if confidence >= 60:
            result['detected'] = True
            result['reason'] = "反转：" + "，".join(signals)
        
        return result
    
    def _analyze_timeframe(self, klines: pd.DataFrame, timeframe: str) -> Dict:
        """分析单个周期"""
        if len(klines) < 20:
            return {'error': '数据不足'}
        
        # 计算技术指标
        rsi = self._calculate_rsi(klines)
        macd = self._calculate_macd(klines)
        adx = self._calculate_adx(klines)
        volume_ratio = self._calculate_volume_ratio(klines)
        
        # 计算涨跌幅
        latest_close = klines['close'].iloc[-1]
        prev_close = klines['close'].iloc[-2]
        change_pct = (latest_close - prev_close) / prev_close * 100
        
        return {
            'rsi': rsi,
            'macd': macd,
            'adx': adx,
            'volume_ratio': volume_ratio,
            'change_pct': change_pct,
            'close': latest_close
        }
    
    def _calculate_drop(self, klines: pd.DataFrame, periods: int) -> float:
        """计算跌幅"""
        if len(klines) < periods + 1:
            return 0.0
        
        current = klines['close'].iloc[-1]
        previous = klines['close'].iloc[-(periods+1)]
        
        return (current - previous) / previous * 100
    
    def _calculate_rsi(self, klines: pd.DataFrame, period: int = 14) -> float:
        """计算RSI"""
        if len(klines) < period + 1:
            return 50.0
        
        delta = klines['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1])
    
    def _calculate_macd(self, klines: pd.DataFrame) -> Dict:
        """计算MACD"""
        if len(klines) < 26:
            return {'value': 0, 'signal': 0, 'golden_cross': False}
        
        ema12 = klines['close'].ewm(span=12).mean()
        ema26 = klines['close'].ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        
        # 检测金叉
        golden_cross = False
        if len(macd) >= 2:
            if macd.iloc[-2] < signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1]:
                golden_cross = True
        
        return {
            'value': float(macd.iloc[-1]),
            'signal': float(signal.iloc[-1]),
            'golden_cross': golden_cross
        }
    
    def _calculate_adx(self, klines: pd.DataFrame, period: int = 14) -> float:
        """计算ADX（简化版）"""
        if len(klines) < period:
            return 0.0
        
        # 简化计算：使用标准差/均值
        std = klines['close'].rolling(period).std()
        mean = klines['close'].rolling(period).mean()
        adx = (std / mean * 100).iloc[-1]
        
        return float(adx)
    
    def _calculate_volume_ratio(self, klines: pd.DataFrame, period: int = 20) -> float:
        """计算成交量比率"""
        if len(klines) < period:
            return 1.0
        
        current_volume = klines['volume'].iloc[-1]
        avg_volume = klines['volume'].rolling(period).mean().iloc[-1]
        
        if avg_volume == 0:
            return 1.0
        
        return float(current_volume / avg_volume)
    
    def _detect_reversal_pattern(self, klines: pd.DataFrame) -> Optional[str]:
        """检测反转K线形态"""
        if len(klines) < 3:
            return None
        
        # 获取最近3根K线
        k1 = klines.iloc[-3]
        k2 = klines.iloc[-2]
        k3 = klines.iloc[-1]
        
        # 锤子线（Hammer）
        if self._is_hammer(k3):
            return "锤子线"
        
        # 启明星（Morning Star）
        if self._is_morning_star(k1, k2, k3):
            return "启明星"
        
        # 看涨吞没（Bullish Engulfing）
        if self._is_bullish_engulfing(k2, k3):
            return "看涨吞没"
        
        return None
    
    def _is_hammer(self, k: pd.Series) -> bool:
        """判断是否为锤子线"""
        body = abs(k['close'] - k['open'])
        lower_shadow = min(k['open'], k['close']) - k['low']
        upper_shadow = k['high'] - max(k['open'], k['close'])
        
        # 下影线至少是实体的2倍，上影线很短
        return (lower_shadow >= body * 2 and 
                upper_shadow <= body * 0.3 and
                k['close'] > k['open'])
    
    def _is_morning_star(self, k1: pd.Series, k2: pd.Series, k3: pd.Series) -> bool:
        """判断是否为启明星"""
        # 第一根：大阴线
        body1 = k1['open'] - k1['close']
        if body1 <= 0:
            return False
        
        # 第二根：小实体
        body2 = abs(k2['close'] - k2['open'])
        if body2 > body1 * 0.3:
            return False
        
        # 第三根：大阳线
        body3 = k3['close'] - k3['open']
        if body3 <= 0:
            return False
        
        return True
    
    def _is_bullish_engulfing(self, k1: pd.Series, k2: pd.Series) -> bool:
        """判断是否为看涨吞没"""
        # 第一根：阴线
        if k1['close'] >= k1['open']:
            return False
        
        # 第二根：阳线
        if k2['close'] <= k2['open']:
            return False
        
        # 第二根完全吞没第一根
        return (k2['open'] < k1['close'] and 
                k2['close'] > k1['open'])
    
    def _is_price_stabilizing(self, klines_1m: pd.DataFrame) -> bool:
        """判断价格是否止跌企稳"""
        if len(klines_1m) < 5:
            return False
        
        # 最近5根K线的收盘价
        recent_closes = klines_1m['close'].iloc[-5:].values
        
        # 计算波动率
        volatility = np.std(recent_closes) / np.mean(recent_closes)
        
        # 波动率小于0.001（0.1%）认为企稳
        return volatility < 0.001


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    print("="*80)
    print("🔍 多周期监控模块测试")
    print("="*80)
    
    monitor = MultiTimeframeMonitor()
    
    # 创建测试数据
    dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
    
    # 模拟暴跌数据
    prices = np.linspace(4800, 4700, 100)  # 下跌100美元
    prices[-10:] = np.linspace(4700, 4650, 10)  # 最后加速下跌
    
    klines_15m = pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.randn(100) * 2,
        'high': prices + np.random.randn(100) * 2 + 5,
        'low': prices + np.random.randn(100) * 2 - 5,
        'close': prices,
        'volume': np.random.randn(100) * 1000 + 5000
    })
    
    klines_5m = klines_15m.copy()
    klines_1m = klines_15m.copy()
    
    result = monitor.analyze_all_timeframes(
        klines_15m, klines_5m, klines_1m, 4650
    )
    
    print(f"\n检测结果：")
    print(f"  暴跌检测: {result['crash_detected']}")
    print(f"  反转检测: {result['reversal_detected']}")
    print(f"  信号: {result['signal']}")
    print(f"  紧急程度: {result['urgency']}")
    print(f"  原因: {result['reason']}")
