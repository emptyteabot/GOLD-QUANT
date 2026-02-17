"""
Dual Thrust 2.0 策略 - 改进版
基于往期策略优化，适配黄金交易
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class DualThrustStrategy:
    """
    Dual Thrust 2.0 策略
    
    核心思想：
    1. 计算前N日的最高价、最低价、收盘价
    2. 计算上轨和下轨
    3. 突破上轨做多，跌破下轨做空
    4. 加入波动率过滤和趋势确认
    
    改进点：
    - 动态调整K值（根据波动率）
    - 加入趋势过滤（避免震荡市）
    - 加入时间过滤（避开重要数据发布）
    - 加入止损止盈
    """
    
    def __init__(
        self,
        k1: float = 0.5,  # 上轨系数
        k2: float = 0.5,  # 下轨系数
        n_days: int = 4,  # 回看天数
        atr_period: int = 14,  # ATR周期
        trend_period: int = 20,  # 趋势周期
        volatility_adjust: bool = True,  # 是否动态调整K值
        trend_filter: bool = True,  # 是否使用趋势过滤
        stop_loss_atr: float = 2.0,  # 止损ATR倍数
        take_profit_atr: float = 3.0  # 止盈ATR倍数
    ):
        self.k1 = k1
        self.k2 = k2
        self.n_days = n_days
        self.atr_period = atr_period
        self.trend_period = trend_period
        self.volatility_adjust = volatility_adjust
        self.trend_filter = trend_filter
        self.stop_loss_atr = stop_loss_atr
        self.take_profit_atr = take_profit_atr
        
        # 状态
        self.position = 0  # 1: 多头, -1: 空头, 0: 空仓
        self.entry_price = 0
        self.stop_loss_price = 0
        self.take_profit_price = 0
        
        # 统计
        self.signals = []
        self.trades = []
    
    def calculate_range(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        计算上下轨
        
        Args:
            df: DataFrame with columns [high, low, close]
        
        Returns:
            (upper_rail, lower_rail)
        """
        # 前N日数据
        recent = df.tail(self.n_days)
        
        # HH: 最高价的最高值
        # HC: 收盘价的最高值
        # LC: 收盘价的最低值
        # LL: 最低价的最低值
        HH = recent['high'].max()
        HC = recent['close'].max()
        LC = recent['close'].min()
        LL = recent['low'].min()
        
        # Range
        range_value = max(HH - LC, HC - LL)
        
        # 动态调整K值
        if self.volatility_adjust:
            # 计算波动率
            atr = df['atr'].iloc[-1] if 'atr' in df.columns else range_value * 0.5
            volatility = atr / df['close'].iloc[-1]
            
            # 波动率高 → K值小（收紧通道）
            # 波动率低 → K值大（放宽通道）
            k1_adjusted = self.k1 * (1 - volatility * 10)
            k2_adjusted = self.k2 * (1 - volatility * 10)
            
            k1_adjusted = max(0.2, min(0.8, k1_adjusted))
            k2_adjusted = max(0.2, min(0.8, k2_adjusted))
        else:
            k1_adjusted = self.k1
            k2_adjusted = self.k2
        
        # 计算上下轨
        open_price = df['open'].iloc[-1]
        upper_rail = open_price + k1_adjusted * range_value
        lower_rail = open_price - k2_adjusted * range_value
        
        return upper_rail, lower_rail
    
    def check_trend(self, df: pd.DataFrame) -> int:
        """
        检查趋势
        
        Returns:
            1: 上升趋势, -1: 下降趋势, 0: 震荡
        """
        if not self.trend_filter:
            return 0
        
        # 使用均线判断趋势
        if 'sma_20' not in df.columns:
            return 0
        
        close = df['close'].iloc[-1]
        sma_20 = df['sma_20'].iloc[-1]
        sma_60 = df['sma_60'].iloc[-1] if 'sma_60' in df.columns else sma_20
        
        # 价格在均线上方 → 上升趋势
        if close > sma_20 > sma_60:
            return 1
        # 价格在均线下方 → 下降趋势
        elif close < sma_20 < sma_60:
            return -1
        else:
            return 0
    
    def check_time_filter(self, timestamp: datetime) -> bool:
        """
        时间过滤
        
        避开重要数据发布时间
        
        Returns:
            True: 可以交易, False: 不可交易
        """
        # 非农数据: 每月第一个周五 20:30
        if timestamp.weekday() == 4 and timestamp.day <= 7:
            if 20 <= timestamp.hour <= 21:
                return False
        
        # 美联储会议: 通常周三 02:00
        if timestamp.weekday() == 2:
            if 1 <= timestamp.hour <= 3:
                return False
        
        return True
    
    def generate_signal(
        self,
        df: pd.DataFrame,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        生成交易信号
        
        Args:
            df: DataFrame with OHLC data
            timestamp: 当前时间
        
        Returns:
            {
                'signal': int,  # 1: 做多, -1: 做空, 0: 平仓/观望
                'upper_rail': float,
                'lower_rail': float,
                'trend': int,
                'reason': str
            }
        """
        # 计算上下轨
        upper_rail, lower_rail = self.calculate_range(df)
        
        # 当前价格
        current_price = df['close'].iloc[-1]
        
        # 检查趋势
        trend = self.check_trend(df)
        
        # 时间过滤
        if timestamp and not self.check_time_filter(timestamp):
            return {
                'signal': 0,
                'upper_rail': upper_rail,
                'lower_rail': lower_rail,
                'trend': trend,
                'reason': '时间过滤：避开重要数据发布'
            }
        
        # 生成信号
        signal = 0
        reason = ''
        
        # 突破上轨 → 做多
        if current_price > upper_rail:
            if trend >= 0:  # 上升趋势或震荡
                signal = 1
                reason = f'突破上轨 {upper_rail:.2f}，做多'
            else:
                reason = f'突破上轨但趋势向下，观望'
        
        # 跌破下轨 → 做空
        elif current_price < lower_rail:
            if trend <= 0:  # 下降趋势或震荡
                signal = -1
                reason = f'跌破下轨 {lower_rail:.2f}，做空'
            else:
                reason = f'跌破下轨但趋势向上，观望'
        
        # 在通道内 → 观望或平仓
        else:
            if self.position != 0:
                # 如果有持仓，检查是否需要平仓
                if self.position == 1 and current_price < lower_rail:
                    signal = 0
                    reason = '多头止损'
                elif self.position == -1 and current_price > upper_rail:
                    signal = 0
                    reason = '空头止损'
            else:
                reason = '价格在通道内，观望'
        
        return {
            'signal': signal,
            'upper_rail': upper_rail,
            'lower_rail': lower_rail,
            'trend': trend,
            'reason': reason,
            'current_price': current_price
        }
    
    def update_position(
        self,
        signal: int,
        price: float,
        atr: float
    ) -> Optional[Dict]:
        """
        更新持仓
        
        Args:
            signal: 交易信号
            price: 当前价格
            atr: ATR值
        
        Returns:
            交易记录 or None
        """
        trade = None
        
        # 开仓
        if signal != 0 and self.position == 0:
            self.position = signal
            self.entry_price = price
            
            # 设置止损止盈
            if signal == 1:  # 多头
                self.stop_loss_price = price - self.stop_loss_atr * atr
                self.take_profit_price = price + self.take_profit_atr * atr
            else:  # 空头
                self.stop_loss_price = price + self.stop_loss_atr * atr
                self.take_profit_price = price - self.take_profit_atr * atr
            
            trade = {
                'action': 'open',
                'direction': 'long' if signal == 1 else 'short',
                'price': price,
                'stop_loss': self.stop_loss_price,
                'take_profit': self.take_profit_price,
                'timestamp': datetime.now()
            }
        
        # 平仓
        elif signal == 0 and self.position != 0:
            pnl = (price - self.entry_price) * self.position
            pnl_pct = pnl / self.entry_price
            
            trade = {
                'action': 'close',
                'direction': 'long' if self.position == 1 else 'short',
                'entry_price': self.entry_price,
                'exit_price': price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'timestamp': datetime.now()
            }
            
            self.position = 0
            self.entry_price = 0
            self.stop_loss_price = 0
            self.take_profit_price = 0
        
        # 反向开仓（先平后开）
        elif signal != 0 and self.position != 0 and signal != self.position:
            # 先平仓
            pnl = (price - self.entry_price) * self.position
            pnl_pct = pnl / self.entry_price
            
            trade = {
                'action': 'reverse',
                'old_direction': 'long' if self.position == 1 else 'short',
                'new_direction': 'long' if signal == 1 else 'short',
                'entry_price': self.entry_price,
                'exit_price': price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'timestamp': datetime.now()
            }
            
            # 再开仓
            self.position = signal
            self.entry_price = price
            
            if signal == 1:
                self.stop_loss_price = price - self.stop_loss_atr * atr
                self.take_profit_price = price + self.take_profit_atr * atr
            else:
                self.stop_loss_price = price + self.stop_loss_atr * atr
                self.take_profit_price = price - self.take_profit_atr * atr
        
        if trade:
            self.trades.append(trade)
        
        return trade
    
    def check_stop_loss_take_profit(self, current_price: float) -> Optional[str]:
        """
        检查止损止盈
        
        Returns:
            'stop_loss' or 'take_profit' or None
        """
        if self.position == 0:
            return None
        
        if self.position == 1:  # 多头
            if current_price <= self.stop_loss_price:
                return 'stop_loss'
            elif current_price >= self.take_profit_price:
                return 'take_profit'
        else:  # 空头
            if current_price >= self.stop_loss_price:
                return 'stop_loss'
            elif current_price <= self.take_profit_price:
                return 'take_profit'
        
        return None
    
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
        
        for i in range(self.n_days, len(df)):
            # 当前数据
            current_df = df.iloc[:i+1]
            current_price = current_df['close'].iloc[-1]
            atr = current_df['atr'].iloc[-1] if 'atr' in current_df.columns else 10
            
            # 检查止损止盈
            sl_tp = self.check_stop_loss_take_profit(current_price)
            if sl_tp:
                self.update_position(0, current_price, atr)
                continue
            
            # 生成信号
            signal_data = self.generate_signal(current_df)
            signal = signal_data['signal']
            
            # 更新持仓
            self.update_position(signal, current_price, atr)
        
        # 计算统计
        if not self.trades:
            return {'total_trades': 0}
        
        trades_df = pd.DataFrame(self.trades)
        closed_trades = trades_df[trades_df['action'].isin(['close', 'reverse'])]
        
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
            'max_win': win_trades['pnl'].max() if len(win_trades) > 0 else 0,
            'max_loss': lose_trades['pnl'].min() if len(lose_trades) > 0 else 0
        }
        
        return stats


# ==================== 测试 ====================

def test_dual_thrust():
    """测试Dual Thrust策略"""
    print("\n" + "=" * 70)
    print("🧪 测试 Dual Thrust 2.0 策略")
    print("=" * 70)
    
    # 创建模拟数据
    np.random.seed(42)
    n = 1000
    
    # 生成趋势+噪音
    trend = np.linspace(2600, 2700, n)
    noise = np.random.randn(n) * 20
    close = trend + noise
    
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n, freq='1h'),
        'open': close + np.random.randn(n) * 5,
        'high': close + abs(np.random.randn(n) * 10),
        'low': close - abs(np.random.randn(n) * 10),
        'close': close,
        'volume': 1000 + np.random.randn(n) * 100
    })
    
    # 计算ATR和均线
    df['atr'] = df['high'] - df['low']
    df['sma_20'] = df['close'].rolling(20).mean()
    df['sma_60'] = df['close'].rolling(60).mean()
    
    # 创建策略
    strategy = DualThrustStrategy(
        k1=0.5,
        k2=0.5,
        n_days=4,
        volatility_adjust=True,
        trend_filter=True
    )
    
    print("\n1️⃣ 测试信号生成...")
    signal_data = strategy.generate_signal(df.tail(100))
    print(f"   信号: {signal_data['signal']}")
    print(f"   上轨: {signal_data['upper_rail']:.2f}")
    print(f"   下轨: {signal_data['lower_rail']:.2f}")
    print(f"   趋势: {signal_data['trend']}")
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
    else:
        print("   ⚠️ 没有完成的交易")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_dual_thrust()



