"""快速回测 - GOD MODE"""
import asyncio
import logging
import pandas as pd
import numpy as np
from okx_client import OKXClient
from god_mode_agent import GodModeAgent
from technical_agent import TechnicalAnalyst
from risk_manager_enhanced import RiskManager
import config

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def quick_backtest():
    print("="*80)
    print("🔥 GOD MODE 快速回测")
    print("="*80)
    
    capital = 1000.0
    god = GodModeAgent()
    tech = TechnicalAnalyst()
    risk = RiskManager()
    
    print("\n📊 获取数据...")
    okx = OKXClient()
    await okx.initialize()
    klines = await okx.get_klines(config.INST_ID, '15m', 500)
    await okx.close()
    
    df = pd.DataFrame(klines)
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm']
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    
    print(f"✅ {len(df)}根K线")
    print("\n🔥 训练...")
    god.train(df)
    
    print("\n📈 回测...")
    trades = []
    position = None
    
    for i in range(150, len(df), 5):  # 每5根K线决策一次
        window = df.iloc[:i+1]
        price = window['close'].iloc[-1]
        
        # 简化宏观数据
        macro_data = {'score': 50}
        tech_data = tech.analyze(window, price)
        decision = god.decide(macro_data, tech_data, window, price)
        
        if position is None and decision['should_trade'] and decision['signal'] > 0:
            account = {'total_equity': capital, 'available': capital}
            pos_info = risk.calculate_position_size(
                account, price, decision['leverage'], 
                stop_loss_pct=0.015, klines_df=window, use_kelly=True
            )
            
            if pos_info:
                position = {
                    'entry': price,
                    'size': pos_info['oz_size'],
                    'stop': pos_info['stop_loss'],
                    'target': pos_info['take_profit']
                }
                print(f"[{i}] 🔥 开多 @${price:.2f} {pos_info['oz_size']:.3f}oz {decision['leverage']}x")
        
        elif position:
            pnl_pct = (price - position['entry']) / position['entry']
            
            if price <= position['stop'] or price >= position['target'] or pnl_pct >= 0.05:
                pnl = (price - position['entry']) * position['size']
                capital += pnl
                trades.append({'pnl': pnl, 'pct': pnl_pct})
                risk.record_trade(pnl)
                
                print(f"[{i}] 💰 平多 @${price:.2f} ${pnl:+.2f} ({pnl_pct:+.1%})")
                position = None
    
    print("\n" + "="*80)
    print("🔥 GOD MODE 结果")
    print("="*80)
    print(f"初始: $1000.00")
    print(f"最终: ${capital:.2f}")
    print(f"收益: ${capital-1000:+.2f} ({(capital/1000-1)*100:+.2f}%)")
    print(f"交易: {len(trades)}笔")
    
    if trades:
        wins = [t for t in trades if t['pnl'] > 0]
        print(f"胜率: {len(wins)/len(trades)*100:.1f}%")
        if wins:
            print(f"平均盈利: ${np.mean([t['pnl'] for t in wins]):.2f}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(quick_backtest())
