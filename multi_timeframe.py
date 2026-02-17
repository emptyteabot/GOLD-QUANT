"""
多时间框架分析 - MTF (Multi-Timeframe)
综合5分钟、15分钟、1小时、4小时多个周期信号
"""
import logging
import pandas as pd
from typing import Dict, List
import numpy as np

logger = logging.getLogger(__name__)


class MultiTimeframeAnalyzer:
    """多时间框架分析器"""
    
    def __init__(self):
        self.timeframes = {
            '5m': {'weight': 0.15, 'period': 5},
            '15m': {'weight': 0.25, 'period': 15},
            '1h': {'weight': 0.30, 'period': 60},
            '4h': {'weight': 0.30, 'period': 240}
        }
        logger.info(f"✅ 多时间框架分析器初始化 ({len(self.timeframes)}个周期)")
    
    def calculate_trend(self, klines_df: pd.DataFrame) -> Dict:
        """计算单个时间框架的趋势"""
        try:
            df = klines_df.copy()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # MACD
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal_line = macd.ewm(span=9).mean()
            macd_hist = macd - signal_line
            
            # 趋势判断
            trend_signal = 0
            
            # RSI趋势
            if current_rsi > 60:
                trend_signal += 0.3
            elif current_rsi < 40:
                trend_signal -= 0.3
            
            # MACD趋势
            if macd_hist.iloc[-1] > 0:
                trend_signal += 0.4
            else:
                trend_signal -= 0.4
            
            # 均线趋势
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            sma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else sma_20
            
            if df['close'].iloc[-1] > sma_20 > sma_50:
                trend_signal += 0.3
            elif df['close'].iloc[-1] < sma_20 < sma_50:
                trend_signal -= 0.3
            
            # 归一化到-1到1
            trend_signal = np.clip(trend_signal, -1, 1)
            
            return {
                'signal': trend_signal,
                'rsi': current_rsi,
                'macd': macd.iloc[-1],
                'trend': '上涨' if trend_signal > 0.2 else ('下跌' if trend_signal < -0.2 else '震荡')
            }
            
        except Exception as e:
            logger.error(f"❌ 趋势计算失败: {e}")
            return {'signal': 0, 'rsi': 50, 'macd': 0, 'trend': '震荡'}
    
    def resample_klines(self, klines_df: pd.DataFrame, target_period: int) -> pd.DataFrame:
        """重采样K线到目标周期"""
        try:
            df = klines_df.copy()
            
            # 假设输入是15分钟K线
            source_period = 15
            
            if target_period == source_period:
                return df
            
            if target_period < source_period:
                # 无法从大周期生成小周期
                logger.warning(f"⚠️ 无法从{source_period}分钟生成{target_period}分钟K线")
                return df
            
            # 计算聚合比例
            ratio = target_period // source_period
            
            # 重采样
            resampled = pd.DataFrame()
            resampled['open'] = df['open'].iloc[::ratio].values
            resampled['high'] = df['high'].rolling(ratio).max().iloc[::ratio].values
            resampled['low'] = df['low'].rolling(ratio).min().iloc[::ratio].values
            resampled['close'] = df['close'].iloc[::ratio].values
            resampled['volume'] = df['volume'].rolling(ratio).sum().iloc[::ratio].values
            
            return resampled.dropna()
            
        except Exception as e:
            logger.error(f"❌ K线重采样失败: {e}")
            return klines_df
    
    def analyze(self, klines_15m: pd.DataFrame) -> Dict:
        """
        多时间框架综合分析
        
        Args:
            klines_15m: 15分钟K线数据
        
        Returns:
            dict: 综合分析结果
        """
        logger.info("
" + "="*60)
        logger.info("📊 多时间框架分析")
        logger.info("="*60)
        
        signals = {}
        weighted_signal = 0
        
        for tf_name, tf_config in self.timeframes.items():
            period = tf_config['period']
            weight = tf_config['weight']
            
            # 重采样到目标周期
            klines_tf = self.resample_klines(klines_15m, period)
            
            # 计算趋势
            result = self.calculate_trend(klines_tf)
            signals[tf_name] = result
            
            # 加权
            weighted_signal += result['signal'] * weight
            
            logger.info(f"{tf_name:>4}: {result['signal']:+.2f} ({result['trend']}) RSI={result['rsi']:.1f}")
        
        # 计算一致性
        signal_values = [s['signal'] for s in signals.values()]
        consistency = 1 - (np.std(signal_values) / 2)
        
        logger.info(f"
🎯 综合信号: {weighted_signal:+.2f}")
        logger.info(f"   一致性: {consistency:.1%}")
        
        return {
            'signal': weighted_signal,
            'consistency': consistency,
            'timeframe_signals': signals,
            'recommendation': '做多' if weighted_signal > 0.3 else ('做空' if weighted_signal < -0.3 else '观望')
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 测试
    mtf = MultiTimeframeAnalyzer()
    
    # 模拟15分钟K线
    klines = pd.DataFrame({
        'open': np.random.randn(200).cumsum() + 4800,
        'high': np.random.randn(200).cumsum() + 4810,
        'low': np.random.randn(200).cumsum() + 4790,
        'close': np.random.randn(200).cumsum() + 4800,
        'volume': np.random.rand(200) * 1000
    })
    
    result = mtf.analyze(klines)
    print(f"
综合信号: {result['signal']:.2f}")
    print(f"建议: {result['recommendation']}")
