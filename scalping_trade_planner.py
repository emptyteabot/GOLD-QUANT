from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

import config


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)


def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, adjust=False).mean()


def _calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    up_move = df["high"].diff()
    down_move = -df["low"].diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    atr = _calculate_atr(df, period).replace(0, np.nan)
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    return dx.ewm(alpha=1 / period, adjust=False).mean().fillna(0)


def _build_market_snapshot(klines_df: pd.DataFrame, current_price: float) -> Dict:
    df = klines_df.tail(120).copy()
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    ema_fast = close.ewm(span=8, adjust=False).mean()
    ema_mid = close.ewm(span=21, adjust=False).mean()
    ema_slow = close.ewm(span=55, adjust=False).mean()
    atr = _calculate_atr(df, 14)
    rsi = _calculate_rsi(close, 14)
    adx = _calculate_adx(df, 14)
    typical = (high + low + close) / 3
    vwap = ((typical * volume).cumsum() / volume.cumsum().replace(0, np.nan)).fillna(close)

    current_atr = float(atr.iloc[-1]) if len(atr) else current_price * 0.003
    atr_pct = current_atr / current_price if current_price else 0.0
    current_adx = float(adx.iloc[-1]) if len(adx) else 0.0
    current_rsi = float(rsi.iloc[-1]) if len(rsi) else 50.0
    current_vwap = float(vwap.iloc[-1]) if len(vwap) else current_price

    volume_ma = float(volume.tail(20).mean()) if len(volume) >= 20 else float(volume.mean())
    volume_ratio = float(volume.iloc[-1] / volume_ma) if volume_ma else 1.0

    fast_now = float(ema_fast.iloc[-1])
    mid_now = float(ema_mid.iloc[-1])
    slow_now = float(ema_slow.iloc[-1])
    fast_slope = float(ema_fast.iloc[-1] - ema_fast.iloc[-3]) if len(ema_fast) >= 3 else 0.0
    slow_slope = float(ema_slow.iloc[-1] - ema_slow.iloc[-3]) if len(ema_slow) >= 3 else 0.0

    trend_bias = 0.0
    if current_price > fast_now > mid_now > slow_now:
        trend_bias += 0.70
    elif current_price < fast_now < mid_now < slow_now:
        trend_bias -= 0.70

    if fast_slope > 0 and slow_slope >= 0:
        trend_bias += 0.25
    elif fast_slope < 0 and slow_slope <= 0:
        trend_bias -= 0.25

    trend_bias += 0.10 if current_price > current_vwap else -0.10

    return {
        "ema_fast": fast_now,
        "ema_mid": mid_now,
        "ema_slow": slow_now,
        "atr": current_atr,
        "atr_pct": atr_pct,
        "adx": current_adx,
        "rsi": current_rsi,
        "vwap": current_vwap,
        "volume_ratio": volume_ratio,
        "trend_bias": _clamp(trend_bias, -1.0, 1.0),
        "trend_strength": _clamp(current_adx / 35.0, 0.0, 1.0),
        "regime": "trend" if current_adx >= 24 else "range",
        "volatility_state": "high" if atr_pct >= 0.0045 else "normal" if atr_pct >= 0.0025 else "low",
        "recent_high": float(high.tail(8).max()),
        "recent_low": float(low.tail(8).min()),
        "micro_high": float(high.tail(3).max()),
        "micro_low": float(low.tail(3).min()),
    }


def _build_execution_plan(
    snapshot: Dict,
    action: str,
    confidence: float,
    consensus_ratio: float,
    adjusted_signal: float,
) -> Dict:
    current_price = snapshot["vwap"] + (snapshot["ema_fast"] - snapshot["vwap"]) * 0.35
    atr = max(snapshot["atr"], max(snapshot["ema_fast"], 1.0) * 0.001)
    entry_buffer = max(atr * 0.10, snapshot["ema_fast"] * 0.00035)

    if action == "观望":
        return {
            "entry_price": current_price,
            "entry_min": current_price,
            "entry_max": current_price,
            "stop_loss": current_price,
            "take_profit": current_price,
            "take_profit_1": current_price,
            "take_profit_2": current_price,
            "risk_reward": 0.0,
            "leverage": config.MIN_LEVERAGE,
            "position_size_pct": 0.0,
            "position_advice": "观望，等待下一根 5m K 线确认。",
            "setup_type": "standby",
            "expected_hold_minutes": 0,
            "reason_summary": "共识或趋势强度不足，不开仓。",
            "tradeable": False,
        }

    direction = 1 if action == "做多" else -1
    quality = _clamp(
        confidence * 0.45 + consensus_ratio * 0.30 + snapshot["trend_strength"] * 0.25,
        0.0,
        1.0,
    )
    breakout_mode = snapshot["volume_ratio"] >= 1.2 and abs(adjusted_signal) >= 0.58
    setup_type = "breakout" if breakout_mode else "pullback"

    if direction > 0:
        raw_entry = max(snapshot["ema_fast"], snapshot["vwap"])
        entry_price = max(raw_entry, snapshot["micro_high"] if breakout_mode else raw_entry)
        stop_anchor = min(snapshot["recent_low"], snapshot["ema_mid"] - atr * 0.7)
        stop_loss = min(stop_anchor, entry_price - max(atr * 0.85, entry_price * 0.0016))
    else:
        raw_entry = min(snapshot["ema_fast"], snapshot["vwap"])
        entry_price = min(raw_entry, snapshot["micro_low"] if breakout_mode else raw_entry)
        stop_anchor = max(snapshot["recent_high"], snapshot["ema_mid"] + atr * 0.7)
        stop_loss = max(stop_anchor, entry_price + max(atr * 0.85, entry_price * 0.0016))

    risk_per_unit = abs(entry_price - stop_loss)
    if risk_per_unit <= 0:
        stop_loss = entry_price - atr if direction > 0 else entry_price + atr
        risk_per_unit = abs(entry_price - stop_loss)

    base_rr = 1.45 + quality * 0.90
    if snapshot["regime"] == "trend":
        base_rr += 0.15
    if snapshot["volatility_state"] == "high":
        base_rr -= 0.10
    risk_reward = _clamp(base_rr, 1.35, 2.60)

    if direction > 0:
        take_profit_1 = entry_price + risk_per_unit * 1.0
        take_profit_2 = entry_price + risk_per_unit * max(1.4, risk_reward - 0.2)
        take_profit = entry_price + risk_per_unit * risk_reward
        entry_min = entry_price - entry_buffer * 0.7
        entry_max = entry_price + entry_buffer
    else:
        take_profit_1 = entry_price - risk_per_unit * 1.0
        take_profit_2 = entry_price - risk_per_unit * max(1.4, risk_reward - 0.2)
        take_profit = entry_price - risk_per_unit * risk_reward
        entry_min = entry_price - entry_buffer
        entry_max = entry_price + entry_buffer * 0.7

    raw_leverage = (
        config.MIN_LEVERAGE
        + (config.BASE_LEVERAGE - config.MIN_LEVERAGE) * quality
        + max(0.0, quality - 0.65) * (config.MAX_LEVERAGE - config.BASE_LEVERAGE)
    )
    if snapshot["volatility_state"] == "high":
        raw_leverage *= 0.75
    elif snapshot["volatility_state"] == "low":
        raw_leverage *= 1.08
    if risk_reward < 1.5:
        raw_leverage *= 0.85
    leverage = int(round(_clamp(raw_leverage, config.MIN_LEVERAGE, config.MAX_LEVERAGE)))

    base_position_pct = config.POSITION_SIZE_PCT * (0.65 + quality * 0.75)
    if snapshot["volatility_state"] == "high":
        base_position_pct *= 0.75
    if consensus_ratio < 0.62:
        base_position_pct *= 0.85
    position_size_pct = _clamp(base_position_pct, 0.05, min(config.MAX_TOTAL_POSITION, 0.25))

    expected_hold_minutes = 8 if breakout_mode else 12
    if snapshot["regime"] != "trend":
        expected_hold_minutes += 3

    tradeable = confidence >= max(0.58, config.MIN_CONFIDENCE) and risk_reward >= 1.4
    position_advice = (
        f"建议使用 {position_size_pct:.0%} 资金，{leverage}x 杠杆，"
        f"{setup_type} 模式，预计持仓 {expected_hold_minutes} 分钟。"
    )
    reason_summary = (
        f"trend={snapshot['regime']}, adx={snapshot['adx']:.1f}, "
        f"rsi={snapshot['rsi']:.1f}, vol_ratio={snapshot['volume_ratio']:.2f}, "
        f"consensus={consensus_ratio:.0%}"
    )

    return {
        "entry_price": entry_price,
        "entry_min": entry_min,
        "entry_max": entry_max,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "take_profit_1": take_profit_1,
        "take_profit_2": take_profit_2,
        "risk_reward": risk_reward,
        "leverage": leverage,
        "position_size_pct": position_size_pct,
        "position_advice": position_advice,
        "setup_type": setup_type,
        "expected_hold_minutes": expected_hold_minutes,
        "reason_summary": reason_summary,
        "tradeable": tradeable,
    }


def build_trade_plan(
    klines_df: pd.DataFrame,
    current_price: float,
    decisions: List,
    avg_signal: float,
    avg_confidence: float,
    long_count: int,
    short_count: int,
    neutral_count: int,
) -> Dict:
    if not decisions:
        return {
            "action": "观望",
            "signal": 0.0,
            "confidence": 0.0,
            "long_count": 0,
            "short_count": 0,
            "neutral_count": 0,
            "consensus_ratio": 0.0,
            "decisions": [],
            "entry_price": current_price,
            "entry_min": current_price,
            "entry_max": current_price,
            "stop_loss": current_price,
            "take_profit": current_price,
            "take_profit_1": current_price,
            "take_profit_2": current_price,
            "risk_reward": 0.0,
            "leverage": config.MIN_LEVERAGE,
            "position_size_pct": 0.0,
            "position_advice": "观望",
            "setup_type": "no_data",
            "expected_hold_minutes": 0,
            "reason_summary": "No valid agent decisions.",
            "market_snapshot": {},
            "tradeable": False,
        }

    consensus_ratio = max(long_count, short_count) / len(decisions)
    snapshot = _build_market_snapshot(klines_df, current_price)
    adjusted_signal = _clamp(avg_signal * 0.65 + snapshot["trend_bias"] * 0.35, -1.0, 1.0)
    confidence_boost = min(0.15, max(0.0, consensus_ratio - 0.5) * 0.30)
    final_confidence = min(0.97, avg_confidence + confidence_boost)

    trend_override_long = (
        snapshot["trend_bias"] >= 0.72
        and adjusted_signal >= 0.18
        and snapshot["adx"] >= 24
    )
    trend_override_short = (
        snapshot["trend_bias"] <= -0.72
        and adjusted_signal <= -0.18
        and snapshot["adx"] >= 24
    )

    if (adjusted_signal > 0.42 and long_count >= 7 and consensus_ratio >= 0.44) or trend_override_long:
        action = "做多"
        final_confidence = max(final_confidence, 0.62 if trend_override_long else final_confidence)
    elif (adjusted_signal < -0.42 and short_count >= 7 and consensus_ratio >= 0.44) or trend_override_short:
        action = "做空"
        final_confidence = max(final_confidence, 0.62 if trend_override_short else final_confidence)
    else:
        action = "观望"
        final_confidence = 0.0

    execution_plan = _build_execution_plan(
        snapshot=snapshot,
        action=action,
        confidence=final_confidence,
        consensus_ratio=consensus_ratio,
        adjusted_signal=adjusted_signal,
    )

    return {
        "action": action,
        "signal": adjusted_signal,
        "confidence": final_confidence,
        "long_count": long_count,
        "short_count": short_count,
        "neutral_count": neutral_count,
        "consensus_ratio": consensus_ratio,
        "decisions": decisions,
        "market_snapshot": snapshot,
        **execution_plan,
    }
