"""
量化增强模块 - 整合机器学习和量化策略
基于上传的量化资料构建
"""
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from collections import deque
from datetime import datetime


class DualThrustStrategy:
    """
    Dual Thrust 策略
    参考: 衍生品小组第二次分享
    
    适用于黄金日内突破交易
    """
    
    def __init__(self, k1: float = 0.5, k2: float = 0.5, lookback: int = 4):
        """
        Args:
            k1: 上轨系数 (0.4-0.7)
            k2: 下轨系数 (0.4-0.7)
            lookback: 回看周期 (天)
        """
        self.k1 = k1
        self.k2 = k2
        self.lookback = lookback
        
        # 历史数据
        self.daily_high = deque(maxlen=lookback)
        self.daily_low = deque(maxlen=lookback)
        self.daily_close = deque(maxlen=lookback)
        
        self.current_day_open = None
        self.upper_band = None
        self.lower_band = None
    
    def update_daily_data(self, high: float, low: float, close: float):
        """更新日线数据"""
        self.daily_high.append(high)
        self.daily_low.append(low)
        self.daily_close.append(close)
    
    def calculate_bands(self, open_price: float) -> Tuple[float, float]:
        """
        计算 Dual Thrust 上下轨
        
        Returns:
            (upper_band, lower_band)
        """
        if len(self.daily_high) < self.lookback:
            return None, None
        
        # 计算 Range
        HH = max(self.daily_high)  # N日最高价
        LL = min(self.daily_low)   # N日最低价
        HC = max(self.daily_close) # N日最高收盘价
        LC = min(self.daily_close) # N日最低收盘价
        
        Range = max(HH - LC, HC - LL)
        
        # 计算上下轨
        upper = open_price + self.k1 * Range
        lower = open_price - self.k2 * Range
        
        self.current_day_open = open_price
        self.upper_band = upper
        self.lower_band = lower
        
        return upper, lower
    
    def check_signal(self, current_price: float) -> str:
        """
        检查交易信号
        
        Returns:
            'LONG': 突破上轨，做多信号
            'SHORT': 突破下轨，做空信号
            'NEUTRAL': 无信号
        """
        if self.upper_band is None or self.lower_band is None:
            return 'NEUTRAL'
        
        if current_price > self.upper_band:
            return 'LONG'
        elif current_price < self.lower_band:
            return 'SHORT'
        else:
            return 'NEUTRAL'


class GoldFeatureEngine:
    """
    黄金特征工程
    参考: 祖传代码 - 特征工程系列
    
    为机器学习模型构建特征
    """
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """计算 RSI 指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, 
                       fast: int = 12, 
                       slow: int = 26, 
                       signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算 MACD 指标"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, 
                                   period: int = 20, 
                                   std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    @staticmethod
    def create_time_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        创建时间特征
        
        黄金市场特点:
        - 亚洲时段 (北京 8:00-16:00): 相对平静
        - 欧洲时段 (北京 16:00-24:00): 开始活跃
        - 美国时段 (北京 20:30-次日4:00): 最活跃
        """
        df = df.copy()
        
        # 基础时间特征
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        # 交易时段特征
        df['is_us_session'] = ((df['hour'] >= 20) | (df['hour'] <= 4)).astype(int)
        df['is_europe_session'] = ((df['hour'] >= 16) & (df['hour'] < 24)).astype(int)
        df['is_asia_session'] = ((df['hour'] >= 8) & (df['hour'] < 16)).astype(int)
        
        # 重要时间点 (美国数据发布)
        df['is_data_release_time'] = (df['hour'] == 20).astype(int)  # 20:30 非农/CPI
        
        # 季节性特征 (黄金有季节性)
        df['is_q4'] = (df['quarter'] == 4).astype(int)  # Q4 通常黄金需求旺盛
        
        return df
    
    @staticmethod
    def create_volatility_features(df: pd.DataFrame, 
                                    price_col: str = 'close') -> pd.DataFrame:
        """创建波动率特征"""
        df = df.copy()
        
        # 历史波动率
        df['volatility_5'] = df[price_col].pct_change().rolling(5).std()
        df['volatility_20'] = df[price_col].pct_change().rolling(20).std()
        df['volatility_60'] = df[price_col].pct_change().rolling(60).std()
        
        # 波动率比率 (当前波动率 / 历史平均)
        df['vol_ratio'] = df['volatility_5'] / df['volatility_20']
        
        # ATR (Average True Range)
        if 'high' in df.columns and 'low' in df.columns:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df[price_col].shift())
            low_close = np.abs(df['low'] - df[price_col].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['atr'] = true_range.rolling(14).mean()
        
        return df
    
    @staticmethod
    def create_momentum_features(df: pd.DataFrame, 
                                  price_col: str = 'close') -> pd.DataFrame:
        """创建动量特征"""
        df = df.copy()
        
        # 收益率
        df['return_1h'] = df[price_col].pct_change(1)
        df['return_4h'] = df[price_col].pct_change(4)
        df['return_24h'] = df[price_col].pct_change(24)
        
        # 累计收益
        df['cum_return_24h'] = (1 + df['return_1h']).rolling(24).apply(np.prod) - 1
        
        # 动量指标
        df['momentum_5'] = df[price_col] / df[price_col].shift(5) - 1
        df['momentum_20'] = df[price_col] / df[price_col].shift(20) - 1
        
        return df


class TripleBarrierLabeling:
    """
    三重屏障标注法
    参考: Advances in Financial Machine Learning (Marcos López de Prado)
    
    用于机器学习的标签生成
    """
    
    @staticmethod
    def apply_triple_barrier(prices: pd.Series,
                             profit_target: float = 0.01,
                             stop_loss: float = 0.005,
                             max_hold_hours: int = 24) -> pd.DataFrame:
        """
        应用三重屏障方法
        
        Args:
            prices: 价格序列
            profit_target: 止盈阈值 (1% = 0.01)
            stop_loss: 止损阈值 (0.5% = 0.005)
            max_hold_hours: 最大持有时间 (小时)
        
        Returns:
            DataFrame with columns: ['label', 'return', 'hold_time']
            label: 1 (盈利), -1 (止损), 0 (超时)
        """
        results = []
        
        for i in range(len(prices) - max_hold_hours):
            entry_price = prices.iloc[i]
            
            # 检查未来 max_hold_hours 内的价格
            future_prices = prices.iloc[i+1:i+max_hold_hours+1]
            future_returns = (future_prices / entry_price) - 1
            
            # 检查三重屏障
            profit_hit = future_returns >= profit_target
            loss_hit = future_returns <= -stop_loss
            
            if profit_hit.any():
                # 触及止盈
                hit_idx = profit_hit.idxmax()
                hold_time = future_returns.index.get_loc(hit_idx) + 1
                final_return = future_returns.loc[hit_idx]
                label = 1
            elif loss_hit.any():
                # 触及止损
                hit_idx = loss_hit.idxmax()
                hold_time = future_returns.index.get_loc(hit_idx) + 1
                final_return = future_returns.loc[hit_idx]
                label = -1
            else:
                # 超时退出
                hold_time = max_hold_hours
                final_return = future_returns.iloc[-1]
                label = 0
            
            results.append({
                'timestamp': prices.index[i],
                'label': label,
                'return': final_return,
                'hold_time': hold_time
            })
        
        return pd.DataFrame(results).set_index('timestamp')


class RiskManager:
    """
    风险管理模块
    参考: Advances in Financial Machine Learning
    
    动态仓位管理和风险控制
    """
    
    def __init__(self, max_position: float = 1.0, max_drawdown: float = 0.1):
        """
        Args:
            max_position: 最大仓位 (1.0 = 100%)
            max_drawdown: 最大回撤阈值 (0.1 = 10%)
        """
        self.max_position = max_position
        self.max_drawdown = max_drawdown
        
        self.peak_value = 0
        self.current_drawdown = 0
    
    def calculate_position_size(self, 
                                signal_strength: float,
                                volatility: float,
                                account_value: float) -> float:
        """
        计算仓位大小
        
        Args:
            signal_strength: 信号强度 (0-1)
            volatility: 当前波动率
            account_value: 账户价值
        
        Returns:
            建议仓位 (0-1)
        """
        # Kelly Criterion 的简化版本
        # position = signal_strength / volatility
        
        base_position = signal_strength * self.max_position
        
        # 根据波动率调整
        vol_adjusted_position = base_position * (0.01 / volatility)  # 假设目标波动率 1%
        
        # 限制最大仓位
        final_position = min(vol_adjusted_position, self.max_position)
        
        return final_position
    
    def check_drawdown(self, current_value: float) -> bool:
        """
        检查回撤是否超过阈值
        
        Returns:
            True: 回撤超标，需要减仓
            False: 回撤正常
        """
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        self.current_drawdown = (self.peak_value - current_value) / self.peak_value
        
        return self.current_drawdown > self.max_drawdown


# 使用示例
if __name__ == "__main__":
    print("🧪 量化增强模块测试\n")
    
    # 测试 Dual Thrust
    print("=" * 60)
    print("1. Dual Thrust 策略测试")
    print("=" * 60)
    
    strategy = DualThrustStrategy(k1=0.5, k2=0.5, lookback=4)
    
    # 模拟数据
    strategy.update_daily_data(2650, 2620, 2640)
    strategy.update_daily_data(2660, 2630, 2655)
    strategy.update_daily_data(2670, 2640, 2665)
    strategy.update_daily_data(2680, 2650, 2675)
    
    upper, lower = strategy.calculate_bands(open_price=2670)
    print(f"开盘价: $2670")
    print(f"上轨: ${upper:.2f}")
    print(f"下轨: ${lower:.2f}")
    
    signal = strategy.check_signal(2685)
    print(f"当前价格 $2685 信号: {signal}")
    
    print("\n" + "=" * 60)
    print("2. 特征工程测试")
    print("=" * 60)
    
    # 创建模拟数据
    dates = pd.date_range('2024-01-01', periods=100, freq='H')
    prices = pd.Series(2650 + np.random.randn(100).cumsum(), index=dates)
    
    # 计算 RSI
    rsi = GoldFeatureEngine.calculate_rsi(prices)
    print(f"最新 RSI: {rsi.iloc[-1]:.2f}")
    
    # 计算 MACD
    macd, signal, hist = GoldFeatureEngine.calculate_macd(prices)
    print(f"最新 MACD: {macd.iloc[-1]:.2f}")
    
    print("\n✅ 量化增强模块测试完成！")




