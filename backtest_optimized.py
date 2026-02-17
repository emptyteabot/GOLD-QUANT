"""
回测系统
使用真实历史数据测试策略表现
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import matplotlib.pyplot as plt
from okx_client import OKXClient
from complete_multi_agent import CompleteMultiAgentSystem
from enhanced_macro_analyst import EnhancedMacroAnalyst
from technical_agent import TechnicalAnalyst
from multi_timeframe_monitor import MultiTimeframeMonitor
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
        # 初始化分析模块
        self.multi_agent = CompleteMultiAgentSystem()
        self.macro_analyst = EnhancedMacroAnalyst()
        self.technical_analyst = TechnicalAnalyst()
        self.mtf_monitor = MultiTimeframeMonitor()
        
    async def run_backtest(
        self, 
        start_date: str,
        end_date: str,
        timeframe: str = '15m'
    ) -> Dict:
        """
        运行回测
        
        参数：
        - start_date: 开始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)
        - timeframe: K线周期 (15m, 5m, 1m)
        
        返回：
        - 回测结果统计
        """
        logger.info("="*80)
        logger.info(f"🔍 开始回测")
        logger.info(f"   时间范围: {start_date} 至 {end_date}")
        logger.info(f"   K线周期: {timeframe}")
        logger.info(f"   初始资金: ${self.initial_capital:.2f}")
        logger.info("="*80)
        
        # 1. 获取历史数据
        logger.info("\n📊 获取历史数据...")
        okx_client = OKXClient()
        await okx_client.initialize()
        
        # 计算需要获取多少根K线
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end_dt - start_dt).days
        
        # 根据周期计算K线数量
        if timeframe == '15m':
            bars = days * 24 * 4  # 每天96根15分钟K线
        elif timeframe == '5m':
            bars = days * 24 * 12  # 每天288根5分钟K线
        elif timeframe == '1m':
            bars = days * 24 * 60  # 每天1440根1分钟K线
        else:
            bars = 1000
        
        bars = min(bars, 1000)  # OKX限制最多1000根
        
        klines = await okx_client.get_klines(config.INST_ID, timeframe, bars)
        await okx_client.close()
        
        if not klines:
            logger.error("❌ 无法获取历史数据")
            return {}
        
        df = self._parse_klines(klines)
        logger.info(f"✅ 获取到 {len(df)} 根K线")
        
        # 2. 训练ML模型
        logger.info("\n🤖 训练ML模型...")
        self.multi_agent.train_ml_model(df)
        
        # 3. 逐根K线回测
        logger.info("\n📈 开始逐根K线回测...")
        
        # 🔧 修复：从第50根开始（不是300根！），确保有历史数据但也能交易
        start_idx = min(50, len(df) - 10)  # 至少留10根K线用于回测
        for i in range(start_idx, len(df)):
            # 获取当前K线之前的数据
            historical_df = df.iloc[:i].copy()
            current_bar = df.iloc[i]
            current_price = float(current_bar['close'])
            current_time = current_bar['timestamp']
            
            # 记录权益
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': self.capital,
                'price': current_price
            })
            
            # 每50根K线显示一次进度
            if i % 50 == 0:
                progress = (i - start_idx) / (len(df) - start_idx) * 100
                logger.info(f"   进度: {progress:.1f}% | 时间: {current_time} | 价格: ${current_price:.2f} | 权益: ${self.capital:.2f}")
            
            # 宏观分析（简化版，使用固定评分）
            macro_result = {'score': 50}
            
            # 技术分析
            tech_result = self.technical_analyst.analyze(historical_df, current_price)
            
            # Multi-Agent决策
            decision = self.multi_agent.make_decision(
                macro_result, tech_result, historical_df, current_price
            )
            
            # 检查持仓
            if self.positions:
                # 有持仓，检查止损止盈
                self._check_exit(current_price, current_time)
            else:
                # 无持仓，检查入场信号
                # 🔧 大幅降低阈值：信号>0.05且置信度>30%就可以交易
                can_trade = (
                    abs(decision['signal']) > 0.05 and  # 信号强度>5%
                    decision['confidence'] > 0.30  # 置信度>30%
                )
                
                if can_trade:
                    # 确定方向
                    side = 'long' if decision['signal'] > 0 else 'short'
                    self._enter_position(
                        current_price, 
                        current_time, 
                        decision['leverage'] if decision['leverage'] > 0 else 8,  # 默认8倍杠杆
                        decision['confidence'],
                        side
                    )
        
        # 4. 平掉所有持仓
        if self.positions:
            final_price = float(df.iloc[-1]['close'])
            final_time = df.iloc[-1]['timestamp']
            self._close_all_positions(final_price, final_time, "回测结束")
        
        # 5. 计算统计数据
        stats = self._calculate_statistics()
        
        # 6. 显示结果
        self._print_results(stats)
        
        # 7. 绘制图表
        self._plot_results(df)
        
        return stats
    
    def _enter_position(
        self, 
        price: float, 
        timestamp: pd.Timestamp,
        leverage: int,
        confidence: float,
        side: str = 'long'
    ):
        """开仓"""
        # 计算仓位大小
        position_size = self.capital * leverage * 0.5  # 使用50%资金（更保守）
        contracts = position_size / price
        
        # 计算止损价（根据方向）
        if side == 'long':
            stop_loss = price * (1 - 0.02 / leverage)
        else:
            stop_loss = price * (1 + 0.02 / leverage)
        
        position = {
            'entry_price': price,
            'entry_time': timestamp,
            'contracts': contracts,
            'leverage': leverage,
            'stop_loss': stop_loss,
            'confidence': confidence,
            'side': side
        }
        
        self.positions.append(position)
        
        action = "开多" if side == 'long' else "开空"
        logger.info(f"   🟢 {action} {contracts:.2f}张 @ ${price:.2f} (杠杆{leverage}x, 止损${stop_loss:.2f})")
    
    def _check_exit(self, price: float, timestamp: pd.Timestamp):
        """检查是否应该平仓 - 优化版：移动止损锁利润"""
        for pos in self.positions[:]:
            side = pos.get('side', 'long')
            entry = pos['entry_price']
            
            # 计算盈亏（根据方向）
            if side == 'long':
                pnl = (price - entry) * pos['contracts']
                pnl_pct = (price - entry) / entry
                hit_stop = price <= pos['stop_loss']
            else:
                pnl = (entry - price) * pos['contracts']
                pnl_pct = (entry - price) / entry
                hit_stop = price >= pos['stop_loss']
            
            # 1. 硬止损
            if hit_stop:
                self._close_position(pos, price, timestamp, "止损")
                continue
            
            # 2. 移动止损（关键优化！）
            if side == 'long':
                # 盈利1%：保本止损
                if pnl_pct >= 0.01 and pos['stop_loss'] < entry:
                    pos['stop_loss'] = entry
                # 盈利2%：锁定1%利润
                if pnl_pct >= 0.02:
                    new_stop = entry * 1.01
                    pos['stop_loss'] = max(pos['stop_loss'], new_stop)
                # 盈利3%：锁定2%利润
                if pnl_pct >= 0.03:
                    new_stop = entry * 1.02
                    pos['stop_loss'] = max(pos['stop_loss'], new_stop)
                # 盈利5%：锁定3.5%利润
                if pnl_pct >= 0.05:
                    new_stop = entry * 1.035
                    pos['stop_loss'] = max(pos['stop_loss'], new_stop)
                # 盈利10%：锁定8%利润
                if pnl_pct >= 0.10:
                    new_stop = entry * 1.08
                    pos['stop_loss'] = max(pos['stop_loss'], new_stop)
            else:  # short
                if pnl_pct >= 0.01 and pos['stop_loss'] > entry:
                    pos['stop_loss'] = entry
                if pnl_pct >= 0.02:
                    new_stop = entry * 0.99
                    pos['stop_loss'] = min(pos['stop_loss'], new_stop)
                if pnl_pct >= 0.03:
                    new_stop = entry * 0.98
                    pos['stop_loss'] = min(pos['stop_loss'], new_stop)
            
            # 3. 最大止盈15%（防止贪心）
            if pnl_pct >= 0.15:
                self._close_position(pos, price, timestamp, "止盈15%")
                continue
    
    def _close_position(
        self, 
        position: Dict, 
        price: float, 
        timestamp: pd.Timestamp,
        reason: str
    ):
        """平仓"""
        side = position.get('side', 'long')
        
        # 计算盈亏（根据方向）
        if side == 'long':
            pnl = (price - position['entry_price']) * position['contracts']
            pnl_pct = (price - position['entry_price']) / position['entry_price']
        else:  # short
            pnl = (position['entry_price'] - price) * position['contracts']
            pnl_pct = (position['entry_price'] - price) / position['entry_price']
        
        # 更新资金
        self.capital += pnl
        
        # 记录交易
        trade = {
            'entry_time': position['entry_time'],
            'exit_time': timestamp,
            'entry_price': position['entry_price'],
            'exit_price': price,
            'contracts': position['contracts'],
            'leverage': position['leverage'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': reason
        }
        
        self.trades.append(trade)
        self.positions.remove(position)
        
        logger.info(f"   🔴 平仓 @ ${price:.2f} | 盈亏: ${pnl:+.2f} ({pnl_pct:+.2%}) | 原因: {reason}")
    
    def _close_all_positions(self, price: float, timestamp: pd.Timestamp, reason: str):
        """平掉所有持仓"""
        for pos in self.positions[:]:
            self._close_position(pos, price, timestamp, reason)
    
    def _calculate_statistics(self) -> Dict:
        """计算统计数据"""
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
                'profit_factor': 0
            }
        
        # 总交易次数
        total_trades = len(self.trades)
        
        # 胜率
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # 总收益率
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
        
        # 平均盈亏
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        # 盈亏比
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
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
            'profit_factor': profit_factor
        }
    
    def _print_results(self, stats: Dict):
        """打印回测结果"""
        logger.info("\n" + "="*80)
        logger.info("📊 回测结果")
        logger.info("="*80)
        logger.info(f"初始资金: ${self.initial_capital:.2f}")
        logger.info(f"最终资金: ${stats['final_capital']:.2f}")
        logger.info(f"总收益率: {stats['total_return']:+.2%}")
        logger.info(f"最大回撤: {stats['max_drawdown']:.2%}")
        logger.info(f"\n交易统计:")
        logger.info(f"  总交易次数: {stats['total_trades']}")
        logger.info(f"  盈利次数: {stats['winning_trades']}")
        logger.info(f"  亏损次数: {stats['losing_trades']}")
        logger.info(f"  胜率: {stats['win_rate']:.2%}")
        logger.info(f"  平均盈利: ${stats['avg_win']:.2f}")
        logger.info(f"  平均亏损: ${stats['avg_loss']:.2f}")
        logger.info(f"  盈亏比: {stats['profit_factor']:.2f}")
        logger.info("="*80)
    
    def _plot_results(self, df: pd.DataFrame):
        """绘制回测图表"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # 使用非交互式后端
            
            # 如果没有交易，跳过绘图
            if not self.trades:
                logger.info("📊 无交易记录，跳过图表绘制")
                return
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
            
            # 价格曲线
            ax1.plot(df['timestamp'], df['close'], label='价格', color='blue', alpha=0.7)
            
            # 标记交易
            for trade in self.trades:
                ax1.scatter(trade['entry_time'], trade['entry_price'], 
                           color='green', marker='^', s=100, zorder=5)
                ax1.scatter(trade['exit_time'], trade['exit_price'], 
                           color='red', marker='v', s=100, zorder=5)
            
            ax1.set_title('价格与交易点位')
            ax1.set_xlabel('时间')
            ax1.set_ylabel('价格 ($)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 权益曲线
            equity_df = pd.DataFrame(self.equity_curve)
            ax2.plot(equity_df['timestamp'], equity_df['equity'], 
                    label='权益', color='green', linewidth=2)
            ax2.axhline(y=self.initial_capital, color='red', 
                       linestyle='--', label='初始资金')
            
            ax2.set_title('权益曲线')
            ax2.set_xlabel('时间')
            ax2.set_ylabel('权益 ($)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            filename = f"backtest_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename, dpi=150)
            logger.info(f"\n📊 图表已保存: {filename}")
            
        except Exception as e:
            logger.warning(f"⚠️ 无法绘制图表: {e}")
    
    def _parse_klines(self, klines: list) -> pd.DataFrame:
        """解析K线数据"""
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 
            'volume', 'volCcy', 'volCcyQuote', 'confirm'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # OKX返回的是从新到旧，需要反转
        df = df.iloc[::-1].reset_index(drop=True)
        
        return df


async def main():
    """主函数"""
    print("="*80)
    print("🔍 AURUM回测系统")
    print("="*80)
    
    # 创建回测引擎
    engine = BacktestEngine(initial_capital=1000.0)
    
    # 运行回测（最近30天）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    stats = await engine.run_backtest(
        start_date=start_date,
        end_date=end_date,
        timeframe='15m'
    )
    
    print("\n✅ 回测完成！")


if __name__ == "__main__":
    asyncio.run(main())

