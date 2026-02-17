"""GOD MODE 回测"""
import asyncio
import logging
import pandas as pd
import numpy as np
from okx_client import OKXClient
from god_mode_agent import GodModeAgent
from enhanced_macro_analyst import EnhancedMacroAnalyst
from technical_agent import TechnicalAnalyst
from risk_manager_enhanced import RiskManager
import config

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def run_god_mode_backtest():
    logger.info("="*80)
    logger.info("🔥🔥🔥 GOD MODE BACKTEST 🔥🔥🔥")
    logger.info("="*80)
    
    capital = 1000.0
    god = GodModeAgent()
    macro = EnhancedMacroAnalyst()
    tech = TechnicalAnalyst()
    risk = RiskManager()
    
    logger.info("\n📊 获取历史数据...")
    okx = OKXClient()
    await okx.initialize()
    klines = await okx.get_klines(config.INST_ID, '15m', 500)
    await okx.close()
    
    df = pd.DataFrame(klines)
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm']
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    
    logger.info(f"✅ 获取{len(df)}根K线")
    logger.info("\n🔥 GOD MODE 训练...")
    god.train(df)
    
    logger.info("\n📈 开始回测...")
    trades = []
    position = None
    equity_curve = [capital]
    
    for i in range(150, len(df)):
        window = df.iloc[:i+1]
        price = window['close'].iloc[-1]
        
        macro_data = await macro.analyze_all()
        tech_data = tech.analyze(window)
        decision = god.decide(macro_data, tech_data, window, price)
        
        if position is None and decision['should_trade']:
            if decision['signal'] > 0:
                account = {'total_equity': capital, 'available': capital}
                pos_info = risk.calculate_position_size(
                    account, price, decision['leverage'], 
                    stop_loss_pct=0.015, klines_df=window, use_kelly=True
                )
                
                if pos_info:
                    position = {
                        'side': 'long',
                        'entry': price,
                        'size': pos_info['oz_size'],
                        'stop': pos_info['stop_loss'],
                        'target': pos_info['take_profit']
                    }
                    logger.info(f"\n[{i}] 🔥 开多 @${price:.2f} 仓位={pos_info['oz_size']:.3f} 杠杆={decision['leverage']}x")
        
        elif position:
            if position['side'] == 'long':
                pnl_pct = (price - position['entry']) / position['entry']
                
                if pnl_pct > 0.01:
                    new_stop = max(position['stop'], position['entry'] * 1.005)
                    position['stop'] = new_stop
                
                if price <= position['stop'] or price >= position['target'] or pnl_pct >= 0.05:
                    pnl = (price - position['entry']) * position['size']
                    capital += pnl
                    trades.append({'pnl': pnl, 'pnl_pct': pnl_pct})
                    risk.record_trade(pnl)
                    
                    reason = '止损' if price <= position['stop'] else ('止盈' if price >= position['target'] else '目标')
                    logger.info(f"[{i}] 💰 平多 @${price:.2f} {reason} ${pnl:+.2f} ({pnl_pct:+.1%})")
                    position = None
        
        equity_curve.append(capital)
    
    logger.info("\n" + "="*80)
    logger.info("🔥 GOD MODE 回测结果")
    logger.info("="*80)
    logger.info(f"初始资金: $1000.00")
    logger.info(f"最终资金: ${capital:.2f}")
    logger.info(f"总收益: ${capital-1000:+.2f} ({(capital/1000-1)*100:+.2f}%)")
    logger.info(f"交易次数: {len(trades)}")
    
    if trades:
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] < 0]
        logger.info(f"胜率: {len(wins)/len(trades)*100:.1f}%")
        if wins:
            logger.info(f"盈利: {len(wins)}笔, 平均${np.mean([t['pnl'] for t in wins]):.2f}")
        if losses:
            logger.info(f"亏损: {len(losses)}笔, 平均${np.mean([t['pnl'] for t in losses]):.2f}")
        
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_dd = abs(drawdown.min()) * 100
        logger.info(f"最大回撤: {max_dd:.2f}%")
    
    logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(run_god_mode_backtest())
