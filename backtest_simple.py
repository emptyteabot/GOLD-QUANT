"""
回测系统 - 超激进版（确保有交易）
直接修改Multi-Agent的阈值
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
from okx_client import OKXClient
from enhanced_macro_analyst import EnhancedMacroAnalyst
from technical_agent import TechnicalAnalyst
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleBacktest:
    """简单回测 - 绕过Multi-Agent，直接用技术指标"""
    
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
        self.technical_analyst = TechnicalAnalyst()
        
    async def run_backtest(self):
        """运行回测"""
        logger.info("="*80)
        logger.info(f"🔥 简单回测 - 直接用技术指标交易")
        logger.info(f"   初始资金: ${self.initial_capital:.2f}")
        logger.info(f"   策略: RSI<40做多，RSI>60平仓")
        logger.info("="*80)
        
        # 获取数据
        okx_client = OKXClient()
        await okx_client.initialize()
        
        klines = await okx_client.get_klines(config.INST_ID, '5m', 1000)
        await okx_client.close()
        
        if not klines:
            logger.error("❌ 无法获取历史数据")
            return {}
        
        df = self._parse_klines(klines)
        logger.info(f"✅ 获取到 {len(df)} 根K线（约{len(df)*5/60/24:.1f}天）")
        
        # 计算RSI
        df = self._calculate_rsi(df)
        
        logger.info("\n📈 开始回测...")
        
        for i in range(50, len(df)):
            current_bar = df.iloc[i]
            current_price = float(current_bar['close'])
            current_time = current_bar['timestamp']
            current_rsi = current_bar['rsi']
            
            # 记录权益
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': self.capital,
                'price': current_price
            })
            
            # 显示进度
            if (i - 50) % 100 == 0:
                progress = (i - 50) / (len(df) - 50) * 100
                logger.info(f"   进度: {progress:.1f}% | 时间: {current_time} | 价格: ${current_price:.2f} | RSI: {current_rsi:.1f} | 权益: ${self.capital:.2f} | 交易: {len(self.trades)}")
            
            # 检查持仓
            if self.positions:
                # 有持仓，检查平仓条件
                pos = self.positions[0]
                pnl_pct = (current_price - pos['entry_price']) / pos['entry_price']
                
                # 平仓条件：RSI>60 或 盈利>2% 或 亏损>1%
                if current_rsi > 60 or pnl_pct > 0.02 or pnl_pct < -0.01:
                    reason = "RSI>60" if current_rsi > 60 else ("止盈" if pnl_pct > 0.02 else "止损")
                    self._close_position(pos, current_price, current_time, reason)
            else:
                # 无持仓，检查开仓条件
                # 开仓条件：RSI<40（超卖）
                if current_rsi < 40:
                    self._enter_position(current_price, current_time, current_rsi)
        
        # 平掉所有持仓
        if self.positions:
            final_price = float(df.iloc[-1]['close'])
            final_time = df.iloc[-1]['timestamp']
            self._close_position(self.positions[0], final_price, final_time, "回测结束")
        
        # 计算统计
        stats = self._calculate_statistics(df)
        self._print_results(stats, df)
        
        return stats
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df
    
    def _enter_position(self, price: float, timestamp: pd.Timestamp, rsi: float):
        """开仓"""
        leverage = 8
        position_size = self.capital * leverage * 0.5
        contracts = position_size / price
        stop_loss = price * (1 - 0.01 / leverage)
        
        position = {
            'entry_price': price,
            'entry_time': timestamp,
            'contracts': contracts,
            'leverage': leverage,
            'stop_loss': stop_loss,
            'entry_rsi': rsi
        }
        
        self.positions.append(position)
        logger.info(f"   🟢 开多 {contracts:.2f}张 @ ${price:.2f} (RSI={rsi:.1f})")
    
    def _close_position(self, position: Dict, price: float, timestamp: pd.Timestamp, reason: str):
        """平仓"""
        pnl = (price - position['entry_price']) * position['contracts']
        pnl_pct = (price - position['entry_price']) / position['entry_price']
        
        self.capital += pnl
        
        trade = {
            'entry_time': position['entry_time'],
            'exit_time': timestamp,
            'entry_price': position['entry_price'],
            'exit_price': price,
            'contracts': position['contracts'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': reason
        }
        
        self.trades.append(trade)
        self.positions.remove(position)
        
        logger.info(f"   🔴 平仓 @ ${price:.2f} | 盈亏: ${pnl:+.2f} ({pnl_pct:+.2%}) | {reason}")
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """计算统计"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'final_capital': self.capital,
                'max_drawdown': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'trades_per_day': 0
            }
        
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / total_trades
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        
        # 最大回撤
        equity_values = [e['equity'] for e in self.equity_curve]
        max_drawdown = 0
        peak = equity_values[0]
        for equity in equity_values:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # 每天交易次数
        first_trade = self.trades[0]['entry_time']
        last_trade = self.trades[-1]['exit_time']
        days = (last_trade - first_trade).total_seconds() / 86400
        trades_per_day = total_trades / days if days > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_return': total_return,
            'final_capital': self.capital,
            'max_drawdown': max_drawdown,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades_per_day': trades_per_day
        }
    
    def _print_results(self, stats: Dict, df: pd.DataFrame):
        """打印结果"""
        logger.info("\n" + "="*80)
        logger.info("📊 回测结果")
        logger.info("="*80)
        logger.info(f"初始资金: ${self.initial_capital:.2f}")
        logger.info(f"最终资金: ${stats['final_capital']:.2f}")
        logger.info(f"总收益: ${stats['final_capital'] - self.initial_capital:+.2f}")
        logger.info(f"总收益率: {stats['total_return']:+.2%}")
        logger.info(f"最大回撤: {stats['max_drawdown']:.2%}")
        logger.info(f"\n交易统计:")
        logger.info(f"  总交易次数: {stats['total_trades']}")
        logger.info(f"  每天交易次数: {stats['trades_per_day']:.1f}")
        logger.info(f"  盈利次数: {stats['winning_trades']}")
        logger.info(f"  亏损次数: {stats['losing_trades']}")
        logger.info(f"  胜率: {stats['win_rate']:.2%}")
        logger.info(f"  平均盈利: ${stats['avg_win']:.2f}")
        logger.info(f"  平均亏损: ${stats['avg_loss']:.2f}")
        logger.info(f"  盈亏比: {stats['profit_factor']:.2f}")
        
        if self.trades:
            logger.info(f"\n📋 所有交易:")
            for i, trade in enumerate(self.trades, 1):
                logger.info(
                    f"  {i}. {trade['entry_time'].strftime('%m-%d %H:%M')} → {trade['exit_time'].strftime('%m-%d %H:%M')} | "
                    f"${trade['entry_price']:.2f} → ${trade['exit_price']:.2f} | "
                    f"盈亏: ${trade['pnl']:+.2f} ({trade['pnl_pct']:+.2%}) | "
                    f"{trade['reason']}"
                )
        
        logger.info("="*80)
        
        first_time = df.iloc[0]['timestamp']
        last_time = df.iloc[-1]['timestamp']
        logger.info(f"\n⏰ 回测时间: {first_time} 至 {last_time}")
        logger.info(f"⏰ 回测天数: {(last_time - first_time).total_seconds() / 86400:.1f}天")
        
        # 绘制图表
        self._plot_results(df)
    
    def _parse_klines(self, klines: list) -> pd.DataFrame:
        """解析K线"""
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 
            'volume', 'volCcy', 'volCcyQuote', 'confirm'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df = df.iloc[::-1].reset_index(drop=True)
        
        return df
    
    def _plot_results(self, df: pd.DataFrame):
        """绘制回测图表"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
            
            # 1. 价格曲线 + 交易点位
            ax1.plot(df['timestamp'], df['close'], label='价格', color='blue', alpha=0.7, linewidth=1.5)
            
            # 标记交易
            for trade in self.trades:
                ax1.scatter(trade['entry_time'], trade['entry_price'], 
                           color='green', marker='^', s=150, zorder=5, label='开仓' if trade == self.trades[0] else '')
                ax1.scatter(trade['exit_time'], trade['exit_price'], 
                           color='red', marker='v', s=150, zorder=5, label='平仓' if trade == self.trades[0] else '')
                
                # 连线
                ax1.plot([trade['entry_time'], trade['exit_time']], 
                        [trade['entry_price'], trade['exit_price']], 
                        color='green' if trade['pnl'] > 0 else 'red', 
                        alpha=0.3, linewidth=2)
            
            ax1.set_title('价格与交易点位', fontsize=14, fontweight='bold')
            ax1.set_ylabel('价格 ($)', fontsize=12)
            ax1.legend(loc='best')
            ax1.grid(True, alpha=0.3)
            
            # 2. RSI指标
            ax2.plot(df['timestamp'], df['rsi'], label='RSI', color='purple', linewidth=1.5)
            ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='超买(70)')
            ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='超卖(30)')
            ax2.axhline(y=40, color='orange', linestyle='--', alpha=0.5, label='开仓线(40)')
            ax2.axhline(y=60, color='blue', linestyle='--', alpha=0.5, label='平仓线(60)')
            ax2.fill_between(df['timestamp'], 30, 40, alpha=0.1, color='green', label='开仓区')
            ax2.fill_between(df['timestamp'], 60, 70, alpha=0.1, color='red', label='平仓区')
            
            ax2.set_title('RSI指标', fontsize=14, fontweight='bold')
            ax2.set_ylabel('RSI', fontsize=12)
            ax2.set_ylim(0, 100)
            ax2.legend(loc='best')
            ax2.grid(True, alpha=0.3)
            
            # 3. 权益曲线
            equity_df = pd.DataFrame(self.equity_curve)
            ax3.plot(equity_df['timestamp'], equity_df['equity'], 
                    label='权益', color='green', linewidth=2)
            ax3.axhline(y=self.initial_capital, color='red', 
                       linestyle='--', label=f'初始资金 ${self.initial_capital}', alpha=0.7)
            
            # 填充盈利区域
            ax3.fill_between(equity_df['timestamp'], self.initial_capital, equity_df['equity'], 
                            where=(equity_df['equity'] >= self.initial_capital), 
                            alpha=0.3, color='green', label='盈利区')
            ax3.fill_between(equity_df['timestamp'], self.initial_capital, equity_df['equity'], 
                            where=(equity_df['equity'] < self.initial_capital), 
                            alpha=0.3, color='red', label='亏损区')
            
            ax3.set_title('权益曲线', fontsize=14, fontweight='bold')
            ax3.set_xlabel('时间', fontsize=12)
            ax3.set_ylabel('权益 ($)', fontsize=12)
            ax3.legend(loc='best')
            ax3.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            filename = f"backtest_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            logger.info(f"\n📊 图表已保存: {filename}")
            
            plt.close()
            
        except Exception as e:
            logger.warning(f"⚠️ 无法绘制图表: {e}")


async def main():
    """主函数"""
    print("="*80)
    print("🔥 AURUM简单回测（RSI策略）")
    print("="*80)
    
    engine = SimpleBacktest(initial_capital=1000.0)
    stats = await engine.run_backtest()
    
    print("\n✅ 回测完成！")
    
    if stats['total_trades'] > 0:
        print(f"\n💰 最终收益: ${stats['final_capital'] - 1000:+.2f} ({stats['total_return']:+.2%})")
        print(f"📊 胜率: {stats['win_rate']:.1%}")
        print(f"📉 最大回撤: {stats['max_drawdown']:.1%}")
        print(f"⚡ 每天交易: {stats['trades_per_day']:.1f}次")
    else:
        print("\n⚠️ 没有产生交易")


if __name__ == "__main__":
    asyncio.run(main())

