"""详细回测"""
import asyncio, logging, pandas as pd, numpy as np
from okx_client import OKXClient
from god_mode_agent import GodModeAgent
from technical_agent import TechnicalAnalyst
from risk_manager_enhanced import RiskManager
import config

logging.basicConfig(level=logging.ERROR)

async def run():
    print("="*80)
    print("🔥 GOD MODE 详细回测")
    print("="*80)
    
    capital = 1000.0
    god = GodModeAgent()
    tech = TechnicalAnalyst()
    risk = RiskManager()
    
    print("
📊 获取数据...")
    okx = OKXClient()
    await okx.initialize()
    klines = await okx.get_klines(config.INST_ID, '15m', 500)
    await okx.close()
    
    df = pd.DataFrame(klines)
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm']
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    
    print(f"✅ {len(df)}根K线, 价格${df['close'].min():.0f}-${df['close'].max():.0f}")
    print("
🔥 训练...")
    god.train(df)
    
    print("
📈 回测...")
    trades = []
    position = None
    equity = [capital]
    
    for i in range(150, len(df), 3):
        window = df.iloc[:i+1]
        price = window['close'].iloc[-1]
        
        decision = god.decide({'score': 50}, tech.analyze(window, price), window, price)
        
        if position is None and decision['should_trade'] and decision['signal'] > 0:
            account = {'total_equity': capital, 'available': capital}
            pos = risk.calculate_position_size(account, price, decision['leverage'], 0.015, window, True)
            
            if pos:
                position = {'entry': price, 'size': pos['oz_size'], 'stop': pos['stop_loss'], 
                           'target': pos['take_profit'], 'idx': i}
                print(f"[{i}] 🔥 开多 ${price:.2f} {pos['oz_size']:.3f}oz {decision['leverage']}x")
        
        elif position:
            pnl_pct = (price - position['entry']) / position['entry']
            if pnl_pct > 0.01:
                position['stop'] = max(position['stop'], position['entry'] * 1.005)
            
            if price <= position['stop'] or price >= position['target'] or pnl_pct >= 0.05:
                pnl = (price - position['entry']) * position['size']
                capital += pnl
                reason = '止损' if price <= position['stop'] else ('止盈' if price >= position['target'] else '目标')
                trades.append({'pnl': pnl, 'pct': pnl_pct, 'bars': i - position['idx']})
                risk.record_trade(pnl)
                print(f"[{i}] 💰 平多 ${price:.2f} {reason} ${pnl:+.2f} ({pnl_pct:+.1%})")
                position = None
        
        equity.append(capital)
    
    print("
" + "="*80)
    print("📊 结果")
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
        losses = [t for t in trades if t['pnl'] < 0]
        if losses:
            print(f"平均亏损: ${np.mean([t['pnl'] for t in losses]):.2f}")
        
        eq = np.array(equity)
        dd = (eq - np.maximum.accumulate(eq)) / np.maximum.accumulate(eq)
        print(f"最大回撤: {abs(dd.min())*100:.2f}%")
        
        print("
交易明细:")
        for i, t in enumerate(trades, 1):
            print(f"  #{i}: ${t['pnl']:+.2f} ({t['pct']:+.1%}) 持仓{t['bars']}根")
    
    print("="*80)

asyncio.run(run())
