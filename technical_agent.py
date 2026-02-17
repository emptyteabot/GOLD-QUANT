"""
技术分析师 - Agent 2
基于15分钟K线进行特征工程 + SMC + 机器学习
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional
from scipy.stats import linregress, entropy
import config

logger = logging.getLogger(__name__)

# 导入技术分析库
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logger.warning("pandas_ta未安装，将使用简化指标")

try:
    from smartmoneyconcepts import smc
    SMC_AVAILABLE = True
except ImportError:
    SMC_AVAILABLE = False
    logger.warning("smartmoneyconcepts未安装，将跳过SMC分析")

try:
    from hurst import compute_Hc
    HURST_AVAILABLE = True
except ImportError:
    HURST_AVAILABLE = False
    logger.warning("hurst未安装，将跳过赫斯特指数")


class TechnicalAnalyst:
    """技术分析师 - 特征工程 + 机器学习"""
    
    def __init__(self):
        self.ml_model = None  # 后续可以加载训练好的模型
    
    def analyze(self, df: pd.DataFrame, price: float) -> Dict:
        """
        完整技术分析
        
        Args:
            df: K线数据 (columns: timestamp, open, high, low, close, volume)
            price: 当前价格
        
        Returns:
            dict: 分析结果
        """
        logger.info("\n" + "="*80)
        logger.info("📊 技术分析（15分钟K线）")
        logger.info("="*80)
        
        # 1. 特征工程
        df = self._add_features(df)
        
        # 2. 获取最新指标
        latest = df.iloc[-1]
        
        # 3. 状态感知（赫斯特指数）
        hurst = latest.get('hurst_48', 0.5)
        if hurst < config.HURST_RANGE_THRESHOLD:
            logger.warning(f"⚠️ 赫斯特指数 {hurst:.2f} < {config.HURST_RANGE_THRESHOLD}，震荡市！")
            return {
                'signal': 0,
                'signal_strength': 0,
                'reason': '震荡市，禁止交易',
                'hurst': hurst,
                'regime': 'RANGE'
            }
        
        # 4. 趋势确认（ADX）
        adx = latest.get('ADX_14', 0)
        if adx < config.ADX_RANGE_THRESHOLD:
            logger.warning(f"⚠️ ADX {adx:.1f} < {config.ADX_RANGE_THRESHOLD}，无明确趋势！")
            return {
                'signal': 0,
                'signal_strength': 0,
                'reason': '无明确趋势',
                'adx': adx,
                'regime': 'RANGE'
            }
        
        # 5. 计算信号
        signal_score = 0
        reasons = []
        
        # RSI
        rsi = latest.get('RSI_14', 50)
        if rsi < config.RSI_OVERSOLD:
            signal_score += 0.3
            reasons.append(f"RSI超卖({rsi:.1f})")
        elif rsi > config.RSI_OVERBOUGHT:
            signal_score -= 0.3
            reasons.append(f"RSI超买({rsi:.1f})")
        
        # 趋势斜率
        slope_16 = latest.get('slope_16', 0)
        if slope_16 > 0:
            signal_score += 0.2
            reasons.append(f"上升趋势(斜率{slope_16:.2f})")
        elif slope_16 < 0:
            signal_score -= 0.2
            reasons.append(f"下降趋势(斜率{slope_16:.2f})")
        
        # MACD
        macd = latest.get('MACD_12_26_9', 0)
        macd_signal = latest.get('MACDs_12_26_9', 0)
        if macd > macd_signal:
            signal_score += 0.2
            reasons.append("MACD金叉")
        elif macd < macd_signal:
            signal_score -= 0.2
            reasons.append("MACD死叉")
        
        # 布林带位置
        bb_position = self._calculate_bb_position(df)
        if bb_position < 0.2:
            signal_score += 0.2
            reasons.append(f"布林带下轨({bb_position:.2f})")
        elif bb_position > 0.8:
            signal_score -= 0.2
            reasons.append(f"布林带上轨({bb_position:.2f})")
        
        # 6. SMC分析（如果可用）
        smc_signals = self._analyze_smc(df) if SMC_AVAILABLE else {}
        
        # 7. 机器学习预测（如果模型可用）
        ml_prob = self._ml_predict(df) if self.ml_model else 0.5
        
        # 8. 综合评分
        signal_strength = abs(signal_score)
        if hurst > config.HURST_TREND_THRESHOLD:
            signal_strength *= 1.2  # 强趋势加成
            reasons.append(f"强趋势加成(Hurst={hurst:.2f})")
        
        signal_direction = 1 if signal_score > 0 else -1 if signal_score < 0 else 0
        
        logger.info(f"\n📊 技术分析结果:")
        logger.info(f"   信号方向: {'🟢 做多' if signal_direction > 0 else '🔴 做空' if signal_direction < 0 else '⚪ 观望'}")
        logger.info(f"   信号强度: {signal_strength:.0%}")
        logger.info(f"   赫斯特指数: {hurst:.2f} {'(强趋势)' if hurst > 0.55 else '(震荡)' if hurst < 0.45 else '(中性)'}")
        logger.info(f"   ADX: {adx:.1f}")
        logger.info(f"   RSI: {rsi:.1f}")
        logger.info(f"   原因: {', '.join(reasons)}")
        
        return {
            'signal': signal_direction,
            'signal_strength': signal_strength,
            'reasons': reasons,
            'hurst': hurst,
            'adx': adx,
            'rsi': rsi,
            'macd': macd,
            'slope_16': slope_16,
            'bb_position': bb_position,
            'ml_prob': ml_prob,
            'smc_signals': smc_signals,
            'regime': 'TREND' if adx > config.ADX_TREND_THRESHOLD else 'RANGE'
        }
    
    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加所有特征"""
        df = df.copy()
        
        # 计算收益率
        df['returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # 1. 滞后收益（15分钟K线调整）
        for lag in [1, 4, 8, 16, 32]:  # 15分钟、1小时、2小时、4小时、8小时
            df[f'lag_{lag}'] = df['returns'].shift(lag)
        
        # 2. 滚动均值与波动（15分钟K线调整）
        for w in [4, 16, 48]:  # 1小时、4小时、12小时
            df[f'ma_{w}'] = df['close'].rolling(w).mean()
            df[f'vol_{w}'] = df['returns'].rolling(w).std()
        
        # 3. 趋势斜率
        df['slope_16'] = df['close'].rolling(16).apply(self._calculate_slope, raw=False)  # 4小时趋势
        
        # 4. 日内极值区间
        df['hl_range'] = np.log(df['high'] / df['low'])
        df['hl_range_ma16'] = df['hl_range'].rolling(16).mean()
        
        # 5. 赫斯特指数（核心！）- 使用更长窗口保持稳定性
        if HURST_AVAILABLE:
            df['hurst_48'] = df['close'].rolling(48).apply(self._calculate_hurst, raw=False)  # 12小时窗口
        else:
            df['hurst_48'] = 0.5  # 默认值
        
        # 6. 帕金森波动率
        df['parkinson_vol'] = np.sqrt(
            (1/(4*np.log(2))) * (np.log(df['high']/df['low']))**2
        )
        
        # 7. 经典技术指标（pandas_ta）
        if PANDAS_TA_AVAILABLE:
            df.ta.adx(length=14, append=True)
            df.ta.rsi(length=14, append=True)
            df.ta.atr(length=14, append=True)
            df.ta.macd(append=True)
            df.ta.bbands(length=20, append=True)
        else:
            # 简化版RSI
            df['RSI_14'] = self._calculate_rsi(df['close'], 14)
            df['ADX_14'] = 25  # 默认值
        
        return df
    
    @staticmethod
    def _calculate_slope(series):
        """计算趋势斜率"""
        if len(series) < 2:
            return 0
        x = np.arange(len(series))
        try:
            slope, _, _, _, _ = linregress(x, series)
            return slope
        except:
            return 0
    
    @staticmethod
    def _calculate_hurst(series):
        """计算赫斯特指数"""
        if len(series) < 20:
            return 0.5
        try:
            H, _, _ = compute_Hc(series.values, kind='price', simplified=True)
            return H
        except:
            return 0.5
    
    @staticmethod
    def _calculate_rsi(series, period=14):
        """简化版RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_bb_position(df):
        """计算布林带位置"""
        if 'BBU_20_2.0' in df.columns:
            upper = df['BBU_20_2.0'].iloc[-1]
            lower = df['BBL_20_2.0'].iloc[-1]
            close = df['close'].iloc[-1]
            if upper > lower:
                return (close - lower) / (upper - lower)
        return 0.5
    
    def _analyze_smc(self, df: pd.DataFrame) -> Dict:
        """Smart Money Concepts分析"""
        try:
            # Order Blocks
            ob = smc.ob(df)
            # Fair Value Gaps
            fvg = smc.fvg(df)
            
            return {
                'order_blocks': ob,
                'fvg': fvg
            }
        except Exception as e:
            logger.warning(f"SMC分析失败: {e}")
            return {}
    
    def _ml_predict(self, df: pd.DataFrame) -> float:
        """机器学习预测（占位符）"""
        # TODO: 实现XGBoost模型
        return 0.5


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 生成模拟数据
    dates = pd.date_range('2024-01-01', periods=200, freq='1H')
    df = pd.DataFrame({
        'timestamp': dates,
        'open': 4500 + np.random.randn(200).cumsum() * 10,
        'high': 4510 + np.random.randn(200).cumsum() * 10,
        'low': 4490 + np.random.randn(200).cumsum() * 10,
        'close': 4500 + np.random.randn(200).cumsum() * 10,
        'volume': np.random.randint(1000, 10000, 200)
    })
    
    analyst = TechnicalAnalyst()
    result = analyst.analyze(df, 4500)
    
    print(f"\n信号: {result['signal']}")
    print(f"强度: {result['signal_strength']:.0%}")
    print(f"赫斯特: {result['hurst']:.2f}")

