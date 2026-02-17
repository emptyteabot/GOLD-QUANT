"""
🧠 智能交易系统回测
验证行情识别 + 策略选择的历史表现
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from okx_client import OKXClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SmartStrategyBacktest:
    """智能策略回测"""
    
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = None  # {'side': 'long', 'entry_price': xxx, 'size': xxx}
        self.trades = []
        self.equity_curve = []
    
    def calculate_features(self, df: pd.DataFrame, idx: int) -> dict:
        """计算指标"""
        close = df['close'].iloc[:idx+1]
        
        if len(close) < 50:
            return None
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])
        
        # 趋势
        x = np.arange(20)
        slope, _ = np.polyfit(x, close.iloc[-20:], 1)
        trend_strength = slope / close.iloc[-1] * 100
        
        # 距离高低点
        high_20 = close.iloc[-20:].max()
        low_20 = close.iloc[-20:].min()
        dist_from_low = (close.iloc[-1] - low_20) / low_20 * 100
        
        # 连续上涨/下跌
        consecutive_up = 0
        consecutive_down = 0
        for i in range(-1, -min(10, len(close)), -1):
            if close.iloc[i] > close.iloc[i-1]:
                consecutive_up += 1
            else:
                break
        for i in range(-1, -min(10, len(close)), -1):
            if close.iloc[i] < close.iloc[i-1]:
                consecutive_down += 1
            else:
                break
        
        return {
            'rsi': current_rsi,
            'trend_strength': trend_strength,
            'dist_from_low': dist_from_low,
            'consecutive_up': consecutive_up,
            'consecutive_down': consecutive_down,
            'price': float(close.iloc[-1])
        }
    
    def classify_regime(self, features: dict) -> str:
        """分类行情"""
        rsi = features['rsi']
        trend = features['trend_strength']
        dist_low = features['dist_from_low']
        
        # 倒车接人！
        if rsi < 35 and dist_low < 3 and features['consecutive_up'] >= 1:
            return 'REVERSAL'
        
        # 暴跌中
        if rsi < 30 and features['consecutive_down'] >= 3:
            return 'CRASH'
        
        # 上涨趋势
        if trend > 0.05 and 50 < rsi < 75:
            return 'TREND_UP'
        
        # 下跌趋势
        if trend < -0.05 and 25 < rsi < 50:
            return 'TREND_DOWN'
        
        return 'RANGE'
    
    def get_signal(self, regime: str, rsi: float) -> tuple:
        """
        获取交易信号
        返回: (action, stop_loss_pct, take_profit_pct)
        """
        if regime == 'REVERSAL':
            return ('BUY', 0.03, 0.10)  # 3%止损，10%止盈
        elif regime == 'TREND_UP' and rsi < 60:
            return ('BUY', 0.05, 0.15)  # 5%止损，15%止盈
        elif rsi > 75:
            return ('SELL', 0, 0)  # 超买平仓
        else:
            return ('HOLD', 0, 0)
    
    async def run(self):
        """运行回测"""
        logger.info("="*60)
        logger.info("🧠 智能交易系统回测")
        logger.info(f"   初始资金: ${self.initial_capital:.2f}")
        logger.info("="*60)
        
        # 获取数据
        client = OKXClient()
        await client.initialize()
        klines = await client.get_klines("XAU-USDT-SWAP", "5m", 1000)
        await client.close()
        
        if not klines:
            logger.error("❌ 获取数据失败")
            return
        
        # 解析数据
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        df = df.iloc[::-1].reset_index(drop=True)
        
        logger.info(f"✅ 获取到 {len(df)} 根K线")
        logger.info(f"   时间范围: {df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")
        
        # 回测
        logger.info("\n📈 开始回测...")
        
        regime_counts = {'REVERSAL': 0, 'CRASH': 0, 'TREND_UP': 0, 'TREND_DOWN': 0, 'RANGE': 0}
        
        for i in range(50, len(df)):
            features = self.calculate_features(df, i)
            if not features:
                continue
            
            price = features['price']
            rsi = features['rsi']
            regime = self.classify_regime(features)
            regime_counts[regime] += 1
            
            # 记录权益
            if self.position:
                unrealized_pnl = (price - self.position['entry_price']) / self.position['entry_price']
                current_equity = self.capital * (1 + unrealized_pnl * self.position['size_ratio'])
            else:
                current_equity = self.capital
            
            self.equity_curve.append({
                'timestamp': df['timestamp'].iloc[i],
                'equity': current_equity,
                'price': price,
                'rsi': rsi,
                'regime': regime
            })
            
            # 获取信号
            action, sl_pct, tp_pct = self.get_signal(regime, rsi)
            
            # 执行交易
            if self.position is None:
                # 无持仓，检查开仓
                if action == 'BUY':
                    size_ratio = 0.3  # 30%仓位
                    self.position = {
                        'entry_price': price,
                        'size_ratio': size_ratio,
                        'stop_loss': price * (1 - sl_pct),
                        'take_profit': price * (1 + tp_pct),
                        'entry_time': df['timestamp'].iloc[i],
                        'regime': regime
                    }
                    logger.info(f"🟢 开多 @ ${price:.2f} | {regime} | RSI={rsi:.0f}")
            else:
                # 有持仓，检查平仓
                entry = self.position['entry_price']
                pnl_pct = (price - entry) / entry
                
                should_close = False
                close_reason = ""
                
                # 止损
                if price <= self.position['stop_loss']:
                    should_close = True
                    close_reason = "止损"
                # 止盈
                elif price >= self.position['take_profit']:
                    should_close = True
                    close_reason = "止盈"
                # 超买平仓
                elif action == 'SELL':
                    should_close = True
                    close_reason = "RSI超买"
                
                if should_close:
                    profit = self.capital * self.position['size_ratio'] * pnl_pct
                    self.capital += profit
                    
                    self.trades.append({
                        'entry_time': self.position['entry_time'],
                        'exit_time': df['timestamp'].iloc[i],
                        'entry_price': entry,
                        'exit_price': price,
                        'pnl_pct': pnl_pct,
                        'profit': profit,
                        'reason': close_reason,
                        'regime': self.position['regime']
                    })
                    
                    emoji = "🟢" if pnl_pct > 0 else "🔴"
                    logger.info(f"{emoji} 平仓 @ ${price:.2f} | {close_reason} | 盈亏: {pnl_pct:.1%} (${profit:.2f})")
                    
                    self.position = None
        
        # 强制平仓
        if self.position:
            price = df['close'].iloc[-1]
            entry = self.position['entry_price']
            pnl_pct = (price - entry) / entry
            profit = self.capital * self.position['size_ratio'] * pnl_pct
            self.capital += profit
            self.trades.append({
                'entry_time': self.position['entry_time'],
                'exit_time': df['timestamp'].iloc[-1],
                'entry_price': entry,
                'exit_price': price,
                'pnl_pct': pnl_pct,
                'profit': profit,
                'reason': '回测结束',
                'regime': self.position['regime']
            })
            logger.info(f"📊 回测结束平仓 @ ${price:.2f} | 盈亏: {pnl_pct:.1%}")
        
        # 统计结果
        self._print_results(regime_counts)
        self._plot_results(df)
    
    def _print_results(self, regime_counts: dict):
        """打印结果"""
        logger.info("\n" + "="*60)
        logger.info("📊 回测结果")
        logger.info("="*60)
        
        # 行情分布
        logger.info("\n📈 行情分布:")
        total = sum(regime_counts.values())
        for regime, count in regime_counts.items():
            pct = count / total * 100 if total > 0 else 0
            logger.info(f"   {regime}: {count} ({pct:.1f}%)")
        
        # 交易统计
        if self.trades:
            wins = [t for t in self.trades if t['pnl_pct'] > 0]
            losses = [t for t in self.trades if t['pnl_pct'] <= 0]
            
            total_return = (self.capital - self.initial_capital) / self.initial_capital * 100
            win_rate = len(wins) / len(self.trades) * 100
            
            avg_win = np.mean([t['pnl_pct'] for t in wins]) * 100 if wins else 0
            avg_loss = np.mean([t['pnl_pct'] for t in losses]) * 100 if losses else 0
            
            logger.info(f"\n💰 交易统计:")
            logger.info(f"   总交易次数: {len(self.trades)}")
            logger.info(f"   盈利次数: {len(wins)}")
            logger.info(f"   亏损次数: {len(losses)}")
            logger.info(f"   胜率: {win_rate:.1f}%")
            logger.info(f"   平均盈利: {avg_win:.1f}%")
            logger.info(f"   平均亏损: {avg_loss:.1f}%")
            
            logger.info(f"\n📈 收益:")
            logger.info(f"   初始资金: ${self.initial_capital:.2f}")
            logger.info(f"   最终资金: ${self.capital:.2f}")
            logger.info(f"   总收益率: {total_return:.2f}%")
            
            # 按行情类型分析
            logger.info(f"\n📊 按行情类型:")
            for regime in ['REVERSAL', 'TREND_UP']:
                regime_trades = [t for t in self.trades if t['regime'] == regime]
                if regime_trades:
                    regime_wins = len([t for t in regime_trades if t['pnl_pct'] > 0])
                    regime_total = sum(t['pnl_pct'] for t in regime_trades) * 100
                    logger.info(f"   {regime}: {len(regime_trades)}笔, 胜率{regime_wins/len(regime_trades)*100:.0f}%, 总收益{regime_total:.1f}%")
        else:
            logger.info("\n⚠️ 没有交易！策略可能太保守")
    
    def _plot_results(self, df: pd.DataFrame):
        """绘制结果"""
        if not self.equity_curve:
            return
        
        eq_df = pd.DataFrame(self.equity_curve)
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        
        # 1. 价格和交易点
        ax1 = axes[0]
        ax1.plot(eq_df['timestamp'], eq_df['price'], 'b-', linewidth=0.8, label='价格')
        
        # 标记交易
        for trade in self.trades:
            color = 'green' if trade['pnl_pct'] > 0 else 'red'
            ax1.scatter(trade['entry_time'], trade['entry_price'], color='green', marker='^', s=100, zorder=5)
            ax1.scatter(trade['exit_time'], trade['exit_price'], color=color, marker='v', s=100, zorder=5)
        
        ax1.set_title('价格走势和交易点')
        ax1.set_ylabel('价格 ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. RSI
        ax2 = axes[1]
        ax2.plot(eq_df['timestamp'], eq_df['rsi'], 'purple', linewidth=0.8)
        ax2.axhline(y=35, color='green', linestyle='--', alpha=0.5, label='超卖线(35)')
        ax2.axhline(y=75, color='red', linestyle='--', alpha=0.5, label='超买线(75)')
        ax2.fill_between(eq_df['timestamp'], 0, 35, alpha=0.1, color='green')
        ax2.fill_between(eq_df['timestamp'], 75, 100, alpha=0.1, color='red')
        ax2.set_title('RSI指标')
        ax2.set_ylabel('RSI')
        ax2.set_ylim(0, 100)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 权益曲线
        ax3 = axes[2]
        ax3.plot(eq_df['timestamp'], eq_df['equity'], 'g-', linewidth=1.5, label='权益')
        ax3.axhline(y=self.initial_capital, color='red', linestyle='--', alpha=0.5, label=f'初始资金 ${self.initial_capital}')
        ax3.fill_between(eq_df['timestamp'], self.initial_capital, eq_df['equity'], 
                        where=(eq_df['equity'] >= self.initial_capital), alpha=0.3, color='green')
        ax3.fill_between(eq_df['timestamp'], self.initial_capital, eq_df['equity'], 
                        where=(eq_df['equity'] < self.initial_capital), alpha=0.3, color='red')
        ax3.set_title('权益曲线')
        ax3.set_ylabel('权益 ($)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存
        filename = f"backtest_smart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        logger.info(f"\n📊 图表已保存: {filename}")
        plt.show()


async def main():
    backtest = SmartStrategyBacktest(initial_capital=1000)
    await backtest.run()


if __name__ == "__main__":
    asyncio.run(main())
