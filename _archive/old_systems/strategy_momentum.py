"""
动量策略 (Momentum Strategy)
基于价格动量和趋势强度的交易策略

核心思想:
- 强者恒强，弱者恒弱
- 追涨杀跌，顺势而为
- 结合多个时间周期确认趋势

参考资料:
- 量化资料/趋势追踪类策略
- Advances in Financial Machine Learning
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False
    print("⚠️ TA-Lib未安装，将使用pandas实现")


class MomentumStrategy:
    """
    动量策略
    
    信号生成逻辑:
    1. 计算多周期动量指标 (ROC, MOM)
    2. 计算趋势强度 (ADX)
    3. 确认成交量配合
    4. 多周期共振确认
    """
    
    def __init__(self,
                 short_period: int = 10,
                 medium_period: int = 20,
                 long_period: int = 50,
                 adx_period: int = 14,
                 adx_threshold: float = 25.0,
                 volume_ma_period: int = 20,
                 entry_threshold: float = 0.6,
                 exit_threshold: float = 0.3):
        """
        Args:
            short_period: 短期动量周期
            medium_period: 中期动量周期
            long_period: 长期动量周期
            adx_period: ADX周期
            adx_threshold: ADX阈值 (趋势强度)
            volume_ma_period: 成交量均线周期
            entry_threshold: 入场阈值
            exit_threshold: 出场阈值
        """
        self.short_period = short_period
        self.medium_period = medium_period
        self.long_period = long_period
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.volume_ma_period = volume_ma_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        
        self.position = 0  # 0=空仓, 1=多头, -1=空头
        self.entry_price = 0
        self.trades = []
    
    def calculate_roc(self, prices: np.ndarray, period: int) -> np.ndarray:
        """
        计算变动率 (Rate of Change)
        
        ROC = (Price - Price[n]) / Price[n] * 100
        """
        if HAS_TALIB:
            return talib.ROC(prices, timeperiod=period)
        else:
            roc = np.zeros_like(prices)
            for i in range(period, len(prices)):
                roc[i] = (prices[i] - prices[i-period]) / prices[i-period] * 100
            return roc
    
    def calculate_momentum(self, prices: np.ndarray, period: int) -> np.ndarray:
        """
        计算动量 (Momentum)
        
        MOM = Price - Price[n]
        """
        if HAS_TALIB:
            return talib.MOM(prices, timeperiod=period)
        else:
            mom = np.zeros_like(prices)
            for i in range(period, len(prices)):
                mom[i] = prices[i] - prices[i-period]
            return mom
    
    def calculate_adx(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """
        计算平均趋向指数 (ADX)
        
        ADX衡量趋势强度，不区分方向
        ADX > 25: 强趋势
        ADX < 20: 弱趋势/震荡
        """
        if HAS_TALIB:
            return talib.ADX(high, low, close, timeperiod=self.adx_period)
        else:
            # 简化实现
            tr = np.maximum(high - low, 
                           np.maximum(abs(high - np.roll(close, 1)),
                                     abs(low - np.roll(close, 1))))
            atr = pd.Series(tr).rolling(self.adx_period).mean().values
            return atr / close * 100
    
    def calculate_volume_ratio(self, volume: np.ndarray) -> np.ndarray:
        """
        计算成交量比率
        
        Volume Ratio = Volume / MA(Volume)
        """
        volume_ma = pd.Series(volume).rolling(self.volume_ma_period).mean().values
        volume_ratio = np.divide(volume, volume_ma, 
                                out=np.ones_like(volume), 
                                where=volume_ma!=0)
        return volume_ratio
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
        
        Returns:
            df: 添加了信号列的 DataFrame
        """
        # 提取数据
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        # 1. 计算多周期ROC
        roc_short = self.calculate_roc(close, self.short_period)
        roc_medium = self.calculate_roc(close, self.medium_period)
        roc_long = self.calculate_roc(close, self.long_period)
        
        # 2. 计算动量
        mom_short = self.calculate_momentum(close, self.short_period)
        mom_medium = self.calculate_momentum(close, self.medium_period)
        
        # 3. 计算ADX (趋势强度)
        adx = self.calculate_adx(high, low, close)
        
        # 4. 计算成交量比率
        volume_ratio = self.calculate_volume_ratio(volume)
        
        # 5. 标准化信号 (0-1)
        def normalize_signal(values: np.ndarray) -> np.ndarray:
            """将信号标准化到0-1范围"""
            values = np.nan_to_num(values, 0)
            abs_max = np.max(np.abs(values))
            if abs_max > 0:
                return values / abs_max
            return values
        
        roc_short_norm = normalize_signal(roc_short)
        roc_medium_norm = normalize_signal(roc_medium)
        roc_long_norm = normalize_signal(roc_long)
        
        # 6. 综合信号
        # 短期权重40%，中期30%，长期30%
        momentum_signal = (roc_short_norm * 0.4 + 
                          roc_medium_norm * 0.3 + 
                          roc_long_norm * 0.3)
        
        # 7. 趋势强度过滤
        # ADX < 阈值时，降低信号强度
        trend_filter = np.where(adx > self.adx_threshold, 1.0, 0.5)
        momentum_signal *= trend_filter
        
        # 8. 成交量确认
        # 成交量放大时，增强信号
        volume_filter = np.clip(volume_ratio, 0.5, 1.5)
        momentum_signal *= volume_filter
        
        # 9. 生成交易信号
        signals = np.zeros(len(df))
        signals[momentum_signal > self.entry_threshold] = 1  # 多头
        signals[momentum_signal < -self.entry_threshold] = -1  # 空头
        
        # 添加到DataFrame
        df['roc_short'] = roc_short
        df['roc_medium'] = roc_medium
        df['roc_long'] = roc_long
        df['adx'] = adx
        df['volume_ratio'] = volume_ratio
        df['momentum_signal'] = momentum_signal
        df['signal'] = signals
        
        return df
    
    def backtest(self, df: pd.DataFrame, initial_capital: float = 100000) -> Dict:
        """
        回测策略
        
        Returns:
            stats: 回测统计数据
        """
        # 生成信号
        df = self.generate_signals(df)
        
        # 初始化
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = [initial_capital]
        
        # 遍历数据
        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            signal = df['signal'].iloc[i]
            
            # 开仓
            if position == 0 and signal != 0:
                position = signal
                entry_price = current_price
                
            # 平仓
            elif position != 0:
                # 信号反转或达到出场阈值
                momentum = df['momentum_signal'].iloc[i]
                
                should_exit = False
                if position == 1 and (signal == -1 or momentum < self.exit_threshold):
                    should_exit = True
                elif position == -1 and (signal == 1 or momentum > -self.exit_threshold):
                    should_exit = True
                
                if should_exit:
                    # 计算收益
                    pnl = (current_price - entry_price) * position
                    pnl_pct = pnl / entry_price
                    capital += pnl
                    
                    trades.append({
                        'entry_time': df['timestamp'].iloc[i-1] if 'timestamp' in df.columns else i-1,
                        'exit_time': df['timestamp'].iloc[i] if 'timestamp' in df.columns else i,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position': position,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
                    
                    position = 0
                    entry_price = 0
            
            equity_curve.append(capital)
        
        # 计算统计指标
        if len(trades) > 0:
            pnls = [t['pnl'] for t in trades]
            win_trades = [t for t in trades if t['pnl'] > 0]
            loss_trades = [t for t in trades if t['pnl'] < 0]
            
            total_return = (capital - initial_capital) / initial_capital
            win_rate = len(win_trades) / len(trades) if trades else 0
            
            avg_win = np.mean([t['pnl'] for t in win_trades]) if win_trades else 0
            avg_loss = np.mean([t['pnl'] for t in loss_trades]) if loss_trades else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            
            # 最大回撤
            equity_curve = np.array(equity_curve)
            running_max = np.maximum.accumulate(equity_curve)
            drawdown = (equity_curve - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            # 夏普比率
            returns = np.diff(equity_curve) / equity_curve[:-1]
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            
            stats = {
                'total_trades': len(trades),
                'win_trades': len(win_trades),
                'loss_trades': len(loss_trades),
                'win_rate': win_rate,
                'total_return': total_return,
                'final_capital': capital,
                'profit_factor': profit_factor,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'trades': trades
            }
        else:
            stats = {
                'total_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'final_capital': initial_capital,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
        
        return stats
    
    def get_current_signal(self, df: pd.DataFrame) -> Dict:
        """
        获取当前信号
        
        Returns:
            {
                'signal': 1/0/-1,
                'strength': 0-1,
                'adx': float,
                'momentum': float
            }
        """
        df = self.generate_signals(df)
        
        latest = df.iloc[-1]
        
        return {
            'signal': int(latest['signal']),
            'strength': abs(latest['momentum_signal']),
            'adx': latest['adx'],
            'momentum': latest['momentum_signal'],
            'roc_short': latest['roc_short'],
            'roc_medium': latest['roc_medium'],
            'roc_long': latest['roc_long'],
            'volume_ratio': latest['volume_ratio']
        }


# 测试代码
if __name__ == "__main__":
    print("=" * 70)
    print("🚀 动量策略测试")
    print("=" * 70)
    
    # 生成模拟数据
    np.random.seed(42)
    n = 1000
    
    # 模拟趋势 + 噪声
    trend = np.linspace(2600, 2700, n)
    noise = np.random.randn(n) * 10
    close = trend + noise
    
    high = close + np.abs(np.random.randn(n) * 5)
    low = close - np.abs(np.random.randn(n) * 5)
    open_price = close + np.random.randn(n) * 3
    volume = np.random.randint(1000, 10000, n)
    
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n, freq='1H'),
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    
    print(f"\n📊 数据集: {len(df)} 条记录")
    print(f"价格范围: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # 初始化策略
    strategy = MomentumStrategy(
        short_period=10,
        medium_period=20,
        long_period=50,
        adx_threshold=25.0,
        entry_threshold=0.6,
        exit_threshold=0.3
    )
    
    print("\n" + "=" * 70)
    print("📈 回测中...")
    print("=" * 70)
    
    # 回测
    stats = strategy.backtest(df, initial_capital=100000)
    
    # 打印结果
    print(f"\n✅ 回测完成！")
    print(f"\n📊 交易统计:")
    print(f"   总交易次数: {stats['total_trades']}")
    print(f"   盈利次数: {stats['win_trades']}")
    print(f"   亏损次数: {stats['loss_trades']}")
    print(f"   胜率: {stats['win_rate']:.2%}")
    
    print(f"\n💰 收益统计:")
    print(f"   总收益率: {stats['total_return']:.2%}")
    print(f"   最终资金: ${stats['final_capital']:,.2f}")
    print(f"   盈亏比: {stats['profit_factor']:.2f}")
    print(f"   最大回撤: {stats['max_drawdown']:.2%}")
    print(f"   夏普比率: {stats['sharpe_ratio']:.2f}")
    
    # 测试当前信号
    print("\n" + "=" * 70)
    print("🎯 当前信号测试")
    print("=" * 70)
    
    current_signal = strategy.get_current_signal(df)
    
    signal_name = {1: '📈 多头', 0: '⏸️ 观望', -1: '📉 空头'}
    print(f"\n信号: {signal_name[current_signal['signal']]}")
    print(f"强度: {current_signal['strength']:.2f}")
    print(f"ADX: {current_signal['adx']:.2f}")
    print(f"动量: {current_signal['momentum']:.2f}")
    print(f"短期ROC: {current_signal['roc_short']:.2f}%")
    print(f"中期ROC: {current_signal['roc_medium']:.2f}%")
    print(f"长期ROC: {current_signal['roc_long']:.2f}%")
    print(f"成交量比率: {current_signal['volume_ratio']:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ 动量策略测试完成！")
    print("=" * 70)
    print("\n💡 策略特点:")
    print("   ✅ 多周期动量确认")
    print("   ✅ ADX趋势强度过滤")
    print("   ✅ 成交量配合验证")
    print("   ✅ 动态出场机制")
    print("\n💡 适用场景:")
    print("   • 趋势市场")
    print("   • 突破行情")
    print("   • 单边上涨/下跌")
    print("=" * 70)



