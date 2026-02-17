"""临时测试脚本"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gold_config
print(f"✅ gold_config OK - {gold_config.PRODUCT_NAME} v{gold_config.PRODUCT_VERSION}")
print(f"   ETFs: {len(gold_config.GOLD_ETFS)}  Stocks: {len(gold_config.GOLD_STOCKS)}")

from ashare_provider import AShareGoldProvider
print("✅ ashare_provider OK")

from gold_strategy_engine import GoldStrategyEngine, TechnicalIndicators
print("✅ gold_strategy_engine OK")

# 快速策略测试
import pandas as pd
import numpy as np
np.random.seed(42)
n = 100
prices = 6.5 + np.random.randn(n).cumsum() * 0.02
df = pd.DataFrame({
    'timestamp': pd.date_range('2026-01-01', periods=n, freq='5min'),
    'open': prices + np.random.randn(n) * 0.01,
    'high': prices + abs(np.random.randn(n) * 0.02),
    'low': prices - abs(np.random.randn(n) * 0.02),
    'close': prices,
    'volume': np.random.randint(10000, 100000, n).astype(float),
})

eng = GoldStrategyEngine()
sig = eng.analyze('518880', '黄金ETF', df, float(prices[-1]), is_t0=True)
print(f"✅ 策略测试OK: {sig.direction} score={sig.score:+.2f} confidence={sig.confidence:.0%}")
print(f"\n🎉 所有模块验证通过！系统可以正常运行。")

