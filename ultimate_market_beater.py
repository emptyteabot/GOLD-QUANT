"""终极战胜市场系统"""
import logging
import numpy as np
import pandas as pd
from typing import Dict

logger = logging.getLogger(__name__)

class UltimateMarketBeater:
    def __init__(self):
        logger.info("✅ 终极系统初始化")
    
    def order_flow(self, df):
        """订单流失衡"""
        df = df.tail(20).copy()
        df['buy'] = df.apply(lambda x: x['volume'] * (x['close']-x['low'])/(x['high']-x['low']+0.01), axis=1)
        df['sell'] = df.apply(lambda x: x['volume'] * (x['high']-x['close'])/(x['high']-x['low']+0.01), axis=1)
        imbalance = (df['buy'].sum() - df['sell'].sum()) / (df['buy'].sum() + df['sell'].sum() + 0.01)
        return imbalance
    
    def smart_money(self, df):
        """聪明钱追踪"""
        volume_threshold = df['volume'].quantile(0.8)
        big_trades = df[df['volume'] > volume_threshold]
        if len(big_trades) > 0:
            return np.sign(big_trades['close'] - big_trades['open']).mean()
        return 0
    
    def regime(self, df):
        """市场状态"""
        sma20 = df['close'].rolling(20).mean().iloc[-1]
        sma50 = df['close'].rolling(50).mean().iloc[-1] if len(df)>=50 else sma20
        return 1 if sma20 > sma50 else -1
    
    def liquidity_hunt(self, df):
        """流动性猎杀"""
        high = df['high'].tail(20).max()
        low = df['low'].tail(20).min()
        price = df['close'].iloc[-1]
        if (high - price) / price < 0.005:
            return -0.8
        elif (price - low) / price < 0.005:
            return 0.8
        return 0
    
    def volatility_breakout(self, df):
        """波动率突破"""
        std = df['close'].rolling(20).std().iloc[-1]
        sma = df['close'].rolling(20).mean().iloc[-1]
        bb_width = std / (sma + 0.01)
        if bb_width < 0.02:
            return 0.5
        return 0
    
    def analyze(self, klines_df, macro_data=None):
        """终极分析"""
        of = self.order_flow(klines_df)
        sm = self.smart_money(klines_df)
        rg = self.regime(klines_df)
        lq = self.liquidity_hunt(klines_df)
        vb = self.volatility_breakout(klines_df)
        
        signal = of*0.25 + sm*0.25 + rg*0.25 + lq*0.15 + vb*0.10
        
        logger.info(f"⚡ Ultimate: OF={of:+.2f} SM={sm:+.2f} RG={rg:+.2f} LQ={lq:+.2f} VB={vb:+.2f} → {signal:+.2f}")
        
        return {'signal': signal}
