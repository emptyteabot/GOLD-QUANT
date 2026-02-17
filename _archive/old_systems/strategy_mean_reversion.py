"""
统计套利策略 - 均值回归
基于协整和统计套利原理
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
from statsmodels.tsa.stattools import coint, adfuller


class MeanReversionStrategy:
    """
    均值回归策略
    
    核心思想：
    1. 价格偏离均值时会回归
    2. 使用布林带识别超买超卖
    3. 使用Z-Score量化偏离程度
    4. 加入协整检验确保均值回归性质
    
    适用场景：
    - 震荡市
    - 高频交易
    - 配对交易
    """
    
    def __init__(
        self,
        lookback_period: int = 20,  # 回看周期
        entry_z_score: float = 2.0,  # 入场Z-Score
        exit_z_score: float = 0.5,   # 出场Z-Score
        stop_loss_z_score: float = 3.0,  # 止损Z-Score
        use_bollinger: bool = True,  # 使用布林带
        bb_std: float = 2.0,  # 布林带标准差倍数
        min_half_life: int = 5,  # 最小半衰期
        max_half_life: int = 50  # 最大半衰期
    ):
        self.lookback_period = lookback_period
        self.entry_z_score = entry_z_score
        self.exit_z_score = exit_z_score
        self.stop_loss_z_score = stop_loss_z_score
        self.use_bollinger = use_bollinger
        self.bb_std = bb_std
        self.min_half_life = min_half_life
        self.max_half_life = max_half_life
        
        # 状态
        self.position = 0  # 1: 多头, -1: 空头, 0: 空仓
        self.entry_price = 0
        self.entry_z_score_value = 0
        
        # 统计
        self.trades = []
    
    def calculate_z_score(self, prices: pd.Series) -> float:
        """
        计算Z-Score
        
        Z-Score = (当前价格 - 均值) / 标准差
        
        Args:
            prices: 价格序列
        
        Returns:
            Z-Score值
        """
        mean = prices.mean()
        std = prices.std()
        
        if std == 0:
            return 0
        
        current_price = prices.iloc[-1]
        z_score = (current_price - mean) / std
        
        return z_score
    
    def calculate_half_life(self, prices: pd.Series) -> float:
        """
        计算半衰期
        
        半衰期：价格回归到均值所需时间的一半
        
        Args:
            prices: 价格序列
        
        Returns:
            半衰期（周期数）
        """
        # 计算价格变化
        price_diff = prices.diff().dropna()
        price_lag = prices.shift(1).dropna()
        
        # 对齐数据
        price_diff = price_diff[price_lag.index]
        
        # 线性回归: Δp(t) = λ * p(t-1) + ε
        # 半衰期 = -ln(2) / λ
        try:
            from sklearn.linear_model import LinearRegression
            
            X = price_lag.values.reshape(-1, 1)
            y = price_diff.values
            
            model = LinearRegression()
            model.fit(X, y)
            
            lambda_coef = model.coef_[0]
            
            if lambda_coef >= 0:
                return float('inf')
            
            half_life = -np.log(2) / lambda_coef
            
            return half_life
            
        except:
            return self.lookback_period
    
    def check_stationarity(self, prices: pd.Series) -> bool:
        """
        检查平稳性（ADF检验）
        
        Args:
            prices: 价格序列
        
        Returns:
            True: 平稳, False: 非平稳
        """
        try:
            result = adfuller(prices.dropna())
            p_value = result[1]
            
            # p-value < 0.05 → 拒绝原假设 → 平稳
            return p_value < 0.05
            
        except:
            return False
    
    def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_mult: float = 2.0
    ) -> Tuple[float, float, float]:
        """
        计算布林带
        
        Args:
            prices: 价格序列
            period: 周期
            std_mult: 标准差倍数
        
        Returns:
            (upper_band, middle_band, lower_band)
        """
        middle = prices.rolling(period).mean().iloc[-1]
        std = prices.rolling(period).std().iloc[-1]
        
        upper = middle + std_mult * std
        lower = middle - std_mult * std
        
        return upper, middle, lower
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """
        生成交易信号
        
        Args:
            df: DataFrame with close prices
        
        Returns:
            {
                'signal': int,  # 1: 做多, -1: 做空, 0: 平仓/观望
                'z_score': float,
                'half_life': float,
                'is_stationary': bool,
                'bb_upper': float,
                'bb_lower': float,
                'reason': str
            }
        """
        prices = df['close'].tail(self.lookback_period)
        
        if len(prices) < self.lookback_period:
            return {
                'signal': 0,
                'reason': '数据不足'
            }
        
        # 计算Z-Score
        z_score = self.calculate_z_score(prices)
        
        # 计算半衰期
        half_life = self.calculate_half_life(prices)
        
        # 检查平稳性
        is_stationary = self.check_stationarity(prices)
        
        # 计算布林带
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(
            prices, self.lookback_period, self.bb_std
        )
        
        current_price = prices.iloc[-1]
        
        # 信号逻辑
        signal = 0
        reason = ''
        
        # 检查半衰期是否合理
        if half_life < self.min_half_life or half_life > self.max_half_life:
            reason = f'半衰期不合理: {half_life:.1f}'
            return {
                'signal': 0,
                'z_score': z_score,
                'half_life': half_life,
                'is_stationary': is_stationary,
                'bb_upper': bb_upper,
                'bb_lower': bb_lower,
                'reason': reason
            }
        
        # 检查平稳性
        if not is_stationary:
            reason = '价格非平稳，不适合均值回归'
            return {
                'signal': 0,
                'z_score': z_score,
                'half_life': half_life,
                'is_stationary': is_stationary,
                'bb_upper': bb_upper,
                'bb_lower': bb_lower,
                'reason': reason
            }
        
        # 开仓信号
        if self.position == 0:
            # Z-Score < -entry_z_score → 超卖 → 做多
            if z_score < -self.entry_z_score:
                if not self.use_bollinger or current_price < bb_lower:
                    signal = 1
                    reason = f'超卖信号: Z-Score={z_score:.2f}'
            
            # Z-Score > entry_z_score → 超买 → 做空
            elif z_score > self.entry_z_score:
                if not self.use_bollinger or current_price > bb_upper:
                    signal = -1
                    reason = f'超买信号: Z-Score={z_score:.2f}'
            
            else:
                reason = f'Z-Score在正常范围: {z_score:.2f}'
        
        # 平仓信号
        else:
            # 多头平仓
            if self.position == 1:
                # 回归到均值附近 → 平仓
                if abs(z_score) < self.exit_z_score:
                    signal = 0
                    reason = f'多头止盈: Z-Score回归到{z_score:.2f}'
                # 继续下跌 → 止损
                elif z_score < -self.stop_loss_z_score:
                    signal = 0
                    reason = f'多头止损: Z-Score={z_score:.2f}'
            
            # 空头平仓
            elif self.position == -1:
                # 回归到均值附近 → 平仓
                if abs(z_score) < self.exit_z_score:
                    signal = 0
                    reason = f'空头止盈: Z-Score回归到{z_score:.2f}'
                # 继续上涨 → 止损
                elif z_score > self.stop_loss_z_score:
                    signal = 0
                    reason = f'空头止损: Z-Score={z_score:.2f}'
        
        return {
            'signal': signal,
            'z_score': z_score,
            'half_life': half_life,
            'is_stationary': is_stationary,
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'current_price': current_price,
            'reason': reason
        }
    
    def update_position(self, signal: int, price: float, z_score: float) -> Optional[Dict]:
        """
        更新持仓
        
        Args:
            signal: 交易信号
            price: 当前价格
            z_score: 当前Z-Score
        
        Returns:
            交易记录 or None
        """
        trade = None
        
        # 开仓
        if signal != 0 and self.position == 0:
            self.position = signal
            self.entry_price = price
            self.entry_z_score_value = z_score
            
            trade = {
                'action': 'open',
                'direction': 'long' if signal == 1 else 'short',
                'price': price,
                'z_score': z_score,
                'timestamp': pd.Timestamp.now()
            }
        
        # 平仓
        elif signal == 0 and self.position != 0:
            pnl = (price - self.entry_price) * self.position
            pnl_pct = pnl / self.entry_price
            
            trade = {
                'action': 'close',
                'direction': 'long' if self.position == 1 else 'short',
                'entry_price': self.entry_price,
                'entry_z_score': self.entry_z_score_value,
                'exit_price': price,
                'exit_z_score': z_score,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'timestamp': pd.Timestamp.now()
            }
            
            self.position = 0
            self.entry_price = 0
            self.entry_z_score_value = 0
        
        if trade:
            self.trades.append(trade)
        
        return trade
    
    def backtest(self, df: pd.DataFrame) -> Dict:
        """
        回测策略
        
        Args:
            df: 历史数据
        
        Returns:
            回测结果统计
        """
        self.trades = []
        self.position = 0
        
        for i in range(self.lookback_period, len(df)):
            # 当前数据
            current_df = df.iloc[:i+1]
            current_price = current_df['close'].iloc[-1]
            
            # 生成信号
            signal_data = self.generate_signal(current_df)
            signal = signal_data['signal']
            z_score = signal_data.get('z_score', 0)
            
            # 更新持仓
            self.update_position(signal, current_price, z_score)
        
        # 计算统计
        if not self.trades:
            return {'total_trades': 0}
        
        trades_df = pd.DataFrame(self.trades)
        closed_trades = trades_df[trades_df['action'] == 'close']
        
        if len(closed_trades) == 0:
            return {'total_trades': 0}
        
        total_pnl = closed_trades['pnl'].sum()
        win_trades = closed_trades[closed_trades['pnl'] > 0]
        lose_trades = closed_trades[closed_trades['pnl'] < 0]
        
        stats = {
            'total_trades': len(closed_trades),
            'win_trades': len(win_trades),
            'lose_trades': len(lose_trades),
            'win_rate': len(win_trades) / len(closed_trades) if len(closed_trades) > 0 else 0,
            'total_pnl': total_pnl,
            'avg_pnl': closed_trades['pnl'].mean(),
            'avg_win': win_trades['pnl'].mean() if len(win_trades) > 0 else 0,
            'avg_loss': lose_trades['pnl'].mean() if len(lose_trades) > 0 else 0,
            'profit_factor': abs(win_trades['pnl'].sum() / lose_trades['pnl'].sum()) if len(lose_trades) > 0 and lose_trades['pnl'].sum() != 0 else 0,
            'sharpe_ratio': closed_trades['pnl'].mean() / closed_trades['pnl'].std() if closed_trades['pnl'].std() > 0 else 0
        }
        
        return stats


# ==================== 测试 ====================

def test_mean_reversion():
    """测试均值回归策略"""
    print("\n" + "=" * 70)
    print("🧪 测试均值回归策略")
    print("=" * 70)
    
    # 创建模拟数据（均值回归特性）
    np.random.seed(42)
    n = 1000
    
    # 生成均值回归序列
    mean = 2650
    prices = [mean]
    
    for i in range(n-1):
        # 均值回归: 价格向均值靠拢
        reversion_force = (mean - prices[-1]) * 0.1
        noise = np.random.randn() * 10
        new_price = prices[-1] + reversion_force + noise
        prices.append(new_price)
    
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n, freq='1h'),
        'close': prices
    })
    
    # 创建策略
    strategy = MeanReversionStrategy(
        lookback_period=20,
        entry_z_score=2.0,
        exit_z_score=0.5,
        use_bollinger=True
    )
    
    print("\n1️⃣ 测试信号生成...")
    signal_data = strategy.generate_signal(df.tail(100))
    print(f"   信号: {signal_data['signal']}")
    print(f"   Z-Score: {signal_data.get('z_score', 0):.2f}")
    print(f"   半衰期: {signal_data.get('half_life', 0):.1f}")
    print(f"   平稳性: {signal_data.get('is_stationary', False)}")
    print(f"   原因: {signal_data['reason']}")
    
    print("\n2️⃣ 测试回测...")
    stats = strategy.backtest(df)
    
    if stats['total_trades'] > 0:
        print(f"   ✅ 总交易次数: {stats['total_trades']}")
        print(f"   📊 胜率: {stats['win_rate']:.2%}")
        print(f"   💰 总盈亏: ${stats['total_pnl']:.2f}")
        print(f"   📈 平均盈利: ${stats['avg_win']:.2f}")
        print(f"   📉 平均亏损: ${stats['avg_loss']:.2f}")
        print(f"   🎯 盈亏比: {stats['profit_factor']:.2f}")
        print(f"   📊 夏普比率: {stats['sharpe_ratio']:.2f}")
    else:
        print("   ⚠️ 没有完成的交易")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_mean_reversion()



