"""
Multi-Agent系统完整回测
验证5个专家协同决策的效果
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from okx_client import OKXClient
from complete_multi_agent import CompleteMultiAgentSystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiAgentBacktest:
    """Multi-Agent系统回测引擎"""
    
    def __init__(self, initial_capital: float = 1000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = None  # {'side': 'long', 'size': 100, 'entry_price': 4800, 'leverage': 10}
        self.trades = []
        self.equity_curve = []
        
        # 初始化Multi-Agent系统
        self.agent_system = CompleteMultiAgentSystem()
        
        logger.info("="*80)
        logger.info("🔥 Multi-Agent系统回测")
        logger.info(f"   初始资金: ${initial_capital:.2f}")
        logger.info(f"   策略: 5个专家协同决策")
        logger.info("="*80)
    
    async def fetch_klines(self, limit: int = 500):
        """获取历史K线数据"""
        try:
            client = OKXClient()
            await client.initialize()
            logger.info("✅ OKX客户端已初始化")
            
            # 获取5分钟K线
            klines = await client.get_klines('XAU-USDT-SWAP', '5m', limit=limit)
            
            if not klines:
                logger.error("❌ 未获取到K线数据")
                await client.close()
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # 反转顺序（从旧到新）
            df = df.iloc[::-1].reset_index(drop=True)
            
            logger.info(f"📊 获取到 {len(df)} 根K线 (XAU-USDT-SWAP, 5m)")
            
            days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds() / 86400
            logger.info(f"✅ 获取到 {len(df)} 根K线（约{days:.1f}天）")
            
            await client.close()
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取K线失败: {e}")
            return None
    
    def calculate_technical_data(self, df: pd.DataFrame, idx: int) -> dict:
        """计算技术指标数据"""
        # 使用到当前索引的所有数据
        data = df.iloc[:idx+1]
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        
        # ADX（简化版）
        adx = data['close'].rolling(14).std().iloc[-1] / data['close'].rolling(14).mean().iloc[-1] * 100 if len(data) >= 14 else 25
        
        # 趋势信号（简化）
        if len(data) >= 20:
            ma20 = data['close'].rolling(20).mean().iloc[-1]
            signal = 1 if data['close'].iloc[-1] > ma20 else -1
        else:
            signal = 0
        
        return {
            'signal': signal,
            'signal_strength': 0.5,
            'rsi': current_rsi,
            'adx': adx
        }
    
    def open_position(self, side: str, price: float, leverage: int, reason: str):
        """开仓"""
        if self.position:
            logger.warning("⚠️ 已有持仓，跳过开仓")
            return
        
        # 计算仓位大小（使用50%资金）
        position_value = self.capital * 0.5 * leverage
        size = position_value / price
        
        self.position = {
            'side': side,
            'size': size,
            'entry_price': price,
            'leverage': leverage,
            'entry_time': None,  # 稍后设置
            'stop_loss': price * (1 - 0.01) if side == 'long' else price * (1 + 0.01)
        }
        
        logger.info(f"   🟢 开{side} {size:.2f}张 @ ${price:.2f} (杠杆{leverage}x)")
    
    def close_position(self, price: float, reason: str, timestamp: datetime):
        """平仓"""
        if not self.position:
            return
        
        # 计算盈亏
        if self.position['side'] == 'long':
            pnl_pct = (price - self.position['entry_price']) / self.position['entry_price']
        else:
            pnl_pct = (self.position['entry_price'] - price) / self.position['entry_price']
        
        pnl_pct *= self.position['leverage']
        pnl = self.capital * 0.5 * pnl_pct
        
        self.capital += pnl
        
        # 记录交易
        trade = {
            'entry_time': self.position['entry_time'],
            'exit_time': timestamp,
            'side': self.position['side'],
            'entry_price': self.position['entry_price'],
            'exit_price': price,
            'size': self.position['size'],
            'leverage': self.position['leverage'],
            'pnl': pnl,
            'pnl_pct': pnl_pct * 100,
            'reason': reason
        }
        self.trades.append(trade)
        
        logger.info(f"   🔴 平仓 @ ${price:.2f} | 盈亏: ${pnl:+.2f} ({pnl_pct*100:+.2f}%) | {reason}")
        
        self.position = None
    
    def check_stop_loss(self, current_price: float, timestamp: datetime):
        """检查止损"""
        if not self.position:
            return False
        
        if self.position['side'] == 'long':
            if current_price <= self.position['stop_loss']:
                self.close_position(current_price, "止损", timestamp)
                return True
        else:
            if current_price >= self.position['stop_loss']:
                self.close_position(current_price, "止损", timestamp)
                return True
        
        return False
    
    async def run(self):
        """运行回测"""
        # 获取K线数据
        df = await self.fetch_klines(limit=500)
        if df is None:
            return
        
        # 训练ML模型
        logger.info("\n🤖 训练机器学习模型...")
        self.agent_system.train_ml_model(df.iloc[:300])  # 用前300根训练
        
        logger.info("\n📈 开始回测...")
        
        # 从第100根开始回测（需要足够的历史数据计算指标）
        start_idx = 100
        total = len(df) - start_idx
        
        for i in range(start_idx, len(df)):
            idx = i - start_idx
            row = df.iloc[i]
            timestamp = row['timestamp']
            price = row['close']
            
            # 进度显示
            if idx % (total // 5) == 0:
                progress = idx / total * 100
                logger.info(f"   进度: {progress:.1f}% | 时间: {timestamp} | 价格: ${price:.2f} | 权益: ${self.capital:.2f} | 交易: {len(self.trades)}")
            
            # 检查止损
            if self.check_stop_loss(price, timestamp):
                continue
            
            # 如果有持仓，检查平仓信号
            if self.position:
                # 简单平仓逻辑：盈利>2%或亏损>1%
                if self.position['side'] == 'long':
                    pnl_pct = (price - self.position['entry_price']) / self.position['entry_price'] * self.position['leverage']
                else:
                    pnl_pct = (self.position['entry_price'] - price) / self.position['entry_price'] * self.position['leverage']
                
                if pnl_pct > 0.02:  # 盈利2%
                    self.close_position(price, "止盈", timestamp)
                    continue
            
            # 如果没有持仓，检查开仓信号
            if not self.position:
                # 准备数据
                klines_window = df.iloc[:i+1]
                tech_data = self.calculate_technical_data(df, i)
                macro_data = {'score': 50}  # 简化：固定宏观评分
                
                # Multi-Agent决策
                decision = self.agent_system.make_decision(
                    macro_data=macro_data,
                    tech_data=tech_data,
                    klines_df=klines_window,
                    price=price
                )
                
                # 如果应该交易
                if decision['should_trade']:
                    side = 'long' if decision['signal'] > 0 else 'short'
                    leverage = decision['leverage']
                    
                    self.open_position(side, price, leverage, decision['reason'])
                    if self.position:
                        self.position['entry_time'] = timestamp
            
            # 记录权益曲线
            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': self.capital
            })
        
        # 如果还有持仓，强制平仓
        if self.position:
            last_price = df.iloc[-1]['close']
            last_time = df.iloc[-1]['timestamp']
            self.close_position(last_price, "回测结束", last_time)
        
        # 输出结果
        self.print_results(df)
    
    def print_results(self, df: pd.DataFrame):
        """输出回测结果"""
        logger.info("\n" + "="*80)
        logger.info("📊 回测结果")
        logger.info("="*80)
        
        total_return = self.capital - self.initial_capital
        total_return_pct = (self.capital / self.initial_capital - 1) * 100
        
        logger.info(f"初始资金: ${self.initial_capital:.2f}")
        logger.info(f"最终资金: ${self.capital:.2f}")
        logger.info(f"总收益: ${total_return:+.2f}")
        logger.info(f"总收益率: {total_return_pct:+.2f}%")
        
        # 计算最大回撤
        equity_series = pd.Series([e['equity'] for e in self.equity_curve])
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        logger.info(f"最大回撤: {abs(max_drawdown):.2f}%")
        
        # 交易统计
        if self.trades:
            logger.info(f"\n交易统计:")
            logger.info(f"  总交易次数: {len(self.trades)}")
            
            days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds() / 86400
            logger.info(f"  每天交易次数: {len(self.trades) / days:.1f}")
            
            winning_trades = [t for t in self.trades if t['pnl'] > 0]
            losing_trades = [t for t in self.trades if t['pnl'] <= 0]
            
            logger.info(f"  盈利次数: {len(winning_trades)}")
            logger.info(f"  亏损次数: {len(losing_trades)}")
            logger.info(f"  胜率: {len(winning_trades)/len(self.trades)*100:.2f}%")
            
            if winning_trades:
                avg_win = np.mean([t['pnl'] for t in winning_trades])
                logger.info(f"  平均盈利: ${avg_win:.2f}")
            
            if losing_trades:
                avg_loss = np.mean([t['pnl'] for t in losing_trades])
                logger.info(f"  平均亏损: ${avg_loss:.2f}")
            
            if winning_trades and losing_trades:
                profit_factor = abs(avg_win / avg_loss)
                logger.info(f"  盈亏比: {profit_factor:.2f}")
            
            # 显示所有交易
            logger.info(f"\n📋 所有交易:")
            for i, trade in enumerate(self.trades, 1):
                entry_time = trade['entry_time'].strftime('%m-%d %H:%M')
                exit_time = trade['exit_time'].strftime('%m-%d %H:%M')
                logger.info(
                    f"  {i}. {entry_time} → {exit_time} | "
                    f"${trade['entry_price']:.2f} → ${trade['exit_price']:.2f} | "
                    f"盈亏: ${trade['pnl']:+.2f} ({trade['pnl_pct']:+.2f}%) | "
                    f"{trade['reason']}"
                )
        
        logger.info("="*80)
        
        # 时间范围
        first_time = df.iloc[0]['timestamp']
        last_time = df.iloc[-1]['timestamp']
        logger.info(f"\n⏰ 回测时间: {first_time} 至 {last_time}")
        logger.info(f"⏰ 回测天数: {(last_time - first_time).total_seconds() / 86400:.1f}天")
        
        # 最终总结
        print("\n" + "="*80)
        print("✅ 回测完成！")
        print("="*80)
        print(f"\n💰 最终收益: ${total_return:+.2f} ({total_return_pct:+.2f}%)")
        if self.trades:
            print(f"📊 胜率: {len(winning_trades)/len(self.trades)*100:.1f}%")
        print(f"📉 最大回撤: {abs(max_drawdown):.1f}%")
        if self.trades:
            print(f"⚡ 每天交易: {len(self.trades) / days:.1f}次")
        print()


async def main():
    backtest = MultiAgentBacktest(initial_capital=1000)
    await backtest.run()


if __name__ == "__main__":
    print("="*80)
    print("🔥 Multi-Agent系统回测（5个专家协同）")
    print("="*80)
    asyncio.run(main())

