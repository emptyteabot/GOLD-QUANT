"""
Lightweight trader skills filters (price-action heuristics).
"""
from __future__ import annotations

from typing import Dict
import pandas as pd


def _calc_atr_pct(df: pd.DataFrame, period: int = 14) -> float:
    if len(df) < period + 1:
        return 0.0
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    tr = pd.concat(
        [
            (high - low),
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    price = close.iloc[-1]
    return float(atr / price) if price else 0.0


def _liquidity_sweep(df: pd.DataFrame, direction: int) -> bool:
    if len(df) < 3:
        return False
    last = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(last["close"] - last["open"])
    upper_wick = last["high"] - max(last["close"], last["open"])
    lower_wick = min(last["close"], last["open"]) - last["low"]

    # Long: sweep below previous low and close back above it with long lower wick
    if direction > 0:
        return last["low"] < prev["low"] and last["close"] > prev["low"] and lower_wick > body * 2
    # Short: sweep above previous high and close back below it with long upper wick
    if direction < 0:
        return last["high"] > prev["high"] and last["close"] < prev["high"] and upper_wick > body * 2
    return False


def evaluate_trader_skills(df: pd.DataFrame, direction: int) -> Dict:
    """
    direction: +1 long, -1 short, 0 neutral
    Returns a score in [-1, +1] and detail flags.
    """
    if len(df) < 200:
        return {"score": 0.0, "trend_ok": False, "vol_ok": False, "sweep": False, "notes": "insufficient_data"}

    close = df["close"].astype(float)
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]

    trend_ok = False
    if direction > 0:
        trend_ok = ma50 > ma200
    elif direction < 0:
        trend_ok = ma50 < ma200

    atr_pct = _calc_atr_pct(df, period=14)
    # Volatility window: 0.15% - 2.0% per bar (5m)
    vol_ok = 0.0015 <= atr_pct <= 0.02

    sweep = _liquidity_sweep(df, direction)

    score = 0.0
    score += 0.4 if trend_ok else -0.1
    score += 0.2 if vol_ok else -0.1
    score += 0.4 if sweep else 0.0

    return {
        "score": float(max(-1.0, min(1.0, score))),
        "trend_ok": trend_ok,
        "vol_ok": vol_ok,
        "sweep": sweep,
        "notes": f"atr_pct={atr_pct:.4f}"
    }
