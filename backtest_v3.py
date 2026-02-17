"""
V3回测引擎 - 快速版
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from okx_client import OKXClient
from super_agent_v3 import SuperAgentV3
from enhanced_macro_analyst import EnhancedMacroAnalyst
from technical_agent import TechnicalAnalyst
from risk_manager_enhanced import RiskManager
import config

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def run_backtest_v3():
    """运行V3回测"""
    logger.info("="*80)
    logger.info("🚀 SuperAgent V3.0 回测")
    logger.info("="*80)
    
    # 初始化
    capital = 1000.0
    agent = SuperAgentV3()
    macro = EnhancedMacroAnalyst()
    tech = TechnicalAnalyst()
    risk = RiskManager()
    
    # 获取数据
    okx = OKXClient()
    await okx.initialize()
    klines = await okx.get_klines(config.INST_ID, '15m', 300)
    await okx.close()
    
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy'])
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    logger.info(f"✅ 获取{len(df)}根K线")
    
    # 训练
    logger.info("\n🤖 训练模型...")
    agent.train(df)
    
    # 回测
    logger.info("\n📈 开始回测...")
    trades = []
    position = None
    
    for i in range(100, len(df)):
        window = df.iloc[:i+1]
        price = window['close'].iloc[-1]
        
        # 分析
        macro_data = await macro.analyze()
        tech_data = tech.analyze(window)
        decision = agent.decide(macro_data, tech_data, window, price)
        
        # 交易逻辑
        if position is None and decision['should_trade']:
            if decision['signal'] > 0:
                # 开多
                account = {'total_equity': capital, 'available': capital}
                pos_info = risk.calculate_position_size(account, price, decision['leverage'], klines_df=window)
                if pos_info:
                    position = {
                        'side': 'long',
                        'entry': price,
                        'size': pos_info['oz_size'],
                        'stop': pos_info['stop_loss']
                    }
                    logger.info(f"\n[{i}] 开多 @{price:.2f} 仓位={pos_info['oz_size']:.3f}")
        
        elif position:
            # 检查止损止盈
            if position['side'] == 'long':
                pnl_pct = (price - position['entry']) / position['entry']
                
                if price <= position['stop'] or pnl_pct >= 0.03:
                    # 平仓
                    pnl = (price - position['entry']) * position['size']
                    capital += pnl
                    trades.append({'pnl': pnl, 'pnl_pct': pnl_pct})
                    risk.record_trade(pnl)
                    
                    logger.info(f"[{i}] 平多 @{price:.2f} 盈亏=${pnl:+.2f} ({pnl_pct:+.1%})")
                    position = None
    
    # 统计
    logger.info("\n" + "="*80)
    logger.info("📊 V3回测结果")
    logger.info("="*80)
    logger.info(f"初始资金: ${1000:.2f}")
    logger.info(f"最终资金: ${capital:.2f}")
    logger.info(f"收益: ${capital-1000:+.2f} ({(capital/1000-1)*100:+.1f}%)")
    logger.info(f"交易次数: {len(trades)}")
    
    if trades:
        wins = [t for t in trades if t['pnl'] > 0]
        logger.info(f"胜率: {len(wins)/len(trades)*100:.1f}%")
        logger.info(f"平均盈利: {np.mean([t['pnl'] for t in wins]):.2f}" if wins else "")


if __name__ == "__main__":
    asyncio.run(run_backtest_v3())
