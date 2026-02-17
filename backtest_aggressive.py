"""
回测系统 - 激进版（一天10次交易）
使用5分钟K线 + 极低阈值
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from okx_client import OKXClient
from complete_multi_agent import CompleteMultiAgentSystem
from enhanced_macro_analyst import EnhancedMacroAnalyst
from technical_agent import TechnicalAnalyst
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BacktestEngineAggressive:
    """回测引擎（激进版 - 一天10次交易）"""
    
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
        
    async def run_backtest(
        self, 
        start_date: str,
        end_date: str,
        timeframe: str = '5m'  # 使用5分钟K线
    ) -> Dict:
        """运行回测"""
        logger.info("="*80)
        logger.info(f"🔥 开始回测（激进版 - 一天10次交易）")
        logger.info(f"   时间范围: {start_date} 至 {end_date}")
        logger.info(f"   K线周期: {timeframe}")
        logger.info(f"   初始资金: ${self.initial_capital:.2f}")
        logger.info(f"   ⚡ 激进模式：信号阈值0.05，置信度阈值30%，快速止盈止损")
        logger.info("="*80)
        
        # 1. 获取历史数据
        logger.info("\n📊 获取历史数据...")
        okx_client = OKXClient()
        await okx_client.initialize()
        
        # 获取1000根5分钟K线（约3.5天）
        bars = 1000
        
        klines = await okx_client.get_klines(config.INST_ID, timeframe, bars)
        await okx_client.close()
        
        if not klines:
            logger.error("❌ 无法获取历史数据")
            return {}
        
        df = self._parse_klines(klines)
        logger.info(f"✅ 获取到 {len(df)} 根K线（约{len(df)*5/60/24:.1f}天）")
        
        # 2. 训练ML模型
        logger.info("\n🤖 训练ML模型...")
        self.multi_agent.train_ml_model(df)
        
        # 3. 逐根K线回测
        logger.info("\n📈 开始逐根K线回测...")
        
        for i in range(100, len(df)):  # 从第100根开始
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
            if (i - 100) % 50 == 0:
                progress = (i - 100) / (len(df) - 100) * 100
                logger.info(f"   进度: {progress:.1f}% | 时间: {current_time} | 价格: ${current_price:.2f} | 权益: ${self.capital:.2f} | 交易: {len(self.trades)}")
            
            # 宏观分析（简化版）
            macro_result = {'score': 50}
            
            # 技术分析
            tech_result = self.technical_analyst.analyze(historical_df, current_price)
            
            # Multi-Agent决策
            decision = self.multi_agent.make_decision(
                macro_result, tech_result, historical_df, current_price
            )
            
            # 检查持仓
            if self.positions:
                # 有持仓，检查止损止盈（更激进）
                self._check_exit_aggressive(current_price, current_time)
            else:
                # 无持仓，检查入场信号（极低阈值）
                # 信号 > 0.05 且 置信度 > 30%
                if decision['signal'] > 0.05 and decision['confidence'] > 0.30:
                    self._enter_position(
                        current_price, 
                        current_time, 
                        decision['leverage'],
                        decision['confidence']
                    )
        
        # 4. 平掉所有持仓
        if self.positions:
            final_price = float(df.iloc[-1]['close'])
            final_time = df.iloc[-1]['timestamp']
            self._close_all_positions(final_price, final_time, "回测结束")
        
        # 5. 计算统计数据
        stats = self._calculate_statistics()
        
        # 6. 显示结果
        self._print_results(stats, df)
        
        return stats
    
    def _enter_position(
        self, 
        price: float, 
        timestamp: pd.Timestamp,
        leverage: int,
        confidence: float
    ):
        """开仓"""
        # 使用较小的仓位（50%资金）
        position_size = self.capital * leverage * 0.5
        contracts = position_size / price
        
        # 更紧的止损（1%）
        stop_loss = price * (1 - 0.01 / leverage)
        
        position = {
            'entry_price': price,
            'entry_time': timestamp,
            'contracts': contracts,
            'leverage': leverage,
            'stop_loss': stop_loss,
            'confidence': confidence
        }
        
        self.positions.append(position)
        
        logger.info(f"   🟢 开多 {contracts:.2f}张 @ ${price:.2f} (杠杆{leverage}x, 止损${stop_loss:.2f}, 置信度{confidence:.1%})")
    
    def _check_exit_aggressive(self, price: float, timestamp: pd.Timestamp):
        """检查是否应该平仓（激进版）"""
        for pos in self.positions[:]:
            pnl = (price - pos['entry_price']) * pos['contracts']
            pnl_pct = (price - pos['entry_price']) / pos['entry_price']
            
            # 止损（1%）
            if price <= pos['stop_loss']:
                self._close_position(pos, price, timestamp, "止损")
                continue
            
            # 快速止盈（2%就平仓）
            if pnl_pct >= 0.02:
                self._close_position(pos, price, timestamp, "止盈")
                continue
            
            # 移动止损（盈利0.5%就移动）
            if pnl_pct >= 0.005:
                new_stop = max(pos['stop_loss'], pos['entry_price'])
                if new_stop > pos['stop_loss']:
                    pos['stop_loss'] = new_stop
    
    def _close_position(
        self, 
        position: Dict, 
        price: float, 
        timestamp: pd.Timestamp,
        reason: str
    ):
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
                'profit_factor': 0,
                'trades_per_day': 0
            }
        
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
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
        
        # 计算每天交易次数
        if self.trades:
            first_trade = self.trades[0]['entry_time']
            last_trade = self.trades[-1]['exit_time']
            days = (last_trade - first_trade).total_seconds() / 86400
            trades_per_day = total_trades / days if days > 0 else 0
        else:
            trades_per_day = 0
        
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
        """打印回测结果"""
        logger.info("\n" + "="*80)
        logger.info("📊 回测结果（激进版）")
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
        
        # 显示前10笔和后10笔交易
        if self.trades:
            logger.info(f"\n📋 前10笔交易:")
            for i, trade in enumerate(self.trades[:10], 1):
                logger.info(
                    f"  {i}. {trade['entry_time'].strftime('%m-%d %H:%M')} → {trade['exit_time'].strftime('%m-%d %H:%M')} | "
                    f"${trade['entry_price']:.2f} → ${trade['exit_price']:.2f} | "
                    f"盈亏: ${trade['pnl']:+.2f} ({trade['pnl_pct']:+.2%}) | "
                    f"{trade['reason']}"
                )
            
            if len(self.trades) > 10:
                logger.info(f"\n📋 后10笔交易:")
                for i, trade in enumerate(self.trades[-10:], len(self.trades)-9):
                    logger.info(
                        f"  {i}. {trade['entry_time'].strftime('%m-%d %H:%M')} → {trade['exit_time'].strftime('%m-%d %H:%M')} | "
                        f"${trade['entry_price']:.2f} → ${trade['exit_price']:.2f} | "
                        f"盈亏: ${trade['pnl']:+.2f} ({trade['pnl_pct']:+.2%}) | "
                        f"{trade['reason']}"
                    )
        
        logger.info("="*80)
        
        # 计算回测时间范围
        first_time = df.iloc[0]['timestamp']
        last_time = df.iloc[-1]['timestamp']
        logger.info(f"\n⏰ 回测时间: {first_time} 至 {last_time}")
        logger.info(f"⏰ 回测天数: {(last_time - first_time).total_seconds() / 86400:.1f}天")
    
    def _parse_klines(self, klines: list) -> pd.DataFrame:
        """解析K线数据"""
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 
            'volume', 'volCcy', 'volCcyQuote', 'confirm'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df = df.iloc[::-1].reset_index(drop=True)
        
        return df


async def main():
    """主函数"""
    print("="*80)
    print("🔥 AURUM回测系统（激进版 - 一天10次交易）")
    print("="*80)
    
    engine = BacktestEngineAggressive(initial_capital=1000.0)
    
    # 运行回测（最近30天，但只能获取1000根5分钟K线≈3.5天）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    stats = await engine.run_backtest(
        start_date=start_date,
        end_date=end_date,
        timeframe='5m'
    )
    
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
