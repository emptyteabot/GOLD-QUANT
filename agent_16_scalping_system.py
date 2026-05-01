from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

import config
from openai_compat_client import call_openai_responses
from scalping_trade_planner import build_trade_plan

logger = logging.getLogger(__name__)


@dataclass
class AgentDecision:
    agent_name: str
    signal: float
    confidence: float
    reason: str
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0


class ScalpingAgent:
    def __init__(self, name: str, strategy_type: str, role_prompt: str):
        self.name = name
        self.strategy_type = strategy_type
        self.role_prompt = role_prompt

    def analyze(self, klines_df: pd.DataFrame, current_price: float) -> AgentDecision:
        raise NotImplementedError


class LLMScalpingAgent(ScalpingAgent):
    def analyze(self, klines_df: pd.DataFrame, current_price: float) -> AgentDecision:
        snapshot = summarize_market(klines_df, current_price)
        system_prompt = (
            "You are one trading sub-agent inside a 16-agent scalping committee. "
            "You must return only a JSON object with keys: signal, confidence, reason. "
            "signal must be a float in [-1,1], where positive means long and negative means short. "
            "confidence must be a float in [0,1]. "
            "reason must be concise and specific. "
            "Do not include markdown, prose, or extra fields."
        )
        user_prompt = (
            f"Agent role: {self.name}\n"
            f"Strategy type: {self.strategy_type}\n"
            f"Role instructions: {self.role_prompt}\n"
            f"Current price: {current_price:.4f}\n"
            f"Market snapshot JSON:\n{json.dumps(snapshot, ensure_ascii=False)}\n"
            "Make an independent decision. Do not hedge for the committee. "
            "If evidence is weak, return signal near 0 and low confidence."
        )
        raw = call_openai_responses(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=getattr(config, "OPENAI_AGENT_TIMEOUT_SEC", 25),
        )
        if not raw:
            return AgentDecision(
                agent_name=self.name,
                signal=0.0,
                confidence=0.0,
                reason="LLM call failed",
                entry_price=current_price,
                stop_loss=current_price,
                take_profit=current_price,
            )

        try:
            signal = float(raw.get("signal", 0.0))
            confidence = float(raw.get("confidence", 0.0))
            reason = str(raw.get("reason", "No reason")).strip()[:240]
        except Exception:
            signal = 0.0
            confidence = 0.0
            reason = "Invalid LLM response"

        signal = max(-1.0, min(1.0, signal))
        confidence = max(0.0, min(1.0, confidence))
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reason=reason,
            entry_price=current_price,
            stop_loss=current_price,
            take_profit=current_price,
        )


def summarize_market(klines_df: pd.DataFrame, current_price: float) -> Dict:
    df = klines_df.tail(120).copy()
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    ema8 = close.ewm(span=8, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    ema55 = close.ewm(span=55, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - 100 / (1 + rs)).fillna(50)

    tp = (high + low + close) / 3
    vwap = ((tp * volume).cumsum() / volume.cumsum().replace(0, np.nan)).fillna(close)
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std

    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()

    volume_ma = volume.rolling(20).mean()
    volume_ratio = (volume / volume_ma.replace(0, np.nan)).fillna(1.0)

    returns_5 = close.pct_change(1).fillna(0)
    returns_12 = close.pct_change(12).fillna(0)

    macd_fast = close.ewm(span=12, adjust=False).mean()
    macd_slow = close.ewm(span=26, adjust=False).mean()
    macd = macd_fast - macd_slow
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - macd_signal

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    atr_14 = atr.replace(0, np.nan)
    plus_di = 100 * plus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr_14
    minus_di = 100 * minus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr_14
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    adx = dx.ewm(alpha=1 / 14, adjust=False).mean().fillna(0)

    return {
        "current_price": current_price,
        "close_last": float(close.iloc[-1]),
        "close_prev": float(close.iloc[-2]),
        "ema8": float(ema8.iloc[-1]),
        "ema21": float(ema21.iloc[-1]),
        "ema55": float(ema55.iloc[-1]),
        "rsi14": float(rsi.iloc[-1]),
        "atr14": float(atr.iloc[-1]),
        "atr_pct": float(atr.iloc[-1] / current_price) if current_price else 0.0,
        "vwap": float(vwap.iloc[-1]),
        "bb_upper": float(bb_upper.iloc[-1]),
        "bb_mid": float(bb_mid.iloc[-1]),
        "bb_lower": float(bb_lower.iloc[-1]),
        "volume_ratio": float(volume_ratio.iloc[-1]),
        "return_5m": float(returns_5.iloc[-1]),
        "return_60m": float(returns_12.iloc[-1]),
        "macd_hist": float(macd_hist.iloc[-1]),
        "macd_signal": float(macd_signal.iloc[-1]),
        "adx14": float(adx.iloc[-1]),
        "plus_di": float(plus_di.iloc[-1]),
        "minus_di": float(minus_di.iloc[-1]),
        "recent_high_8": float(high.tail(8).max()),
        "recent_low_8": float(low.tail(8).min()),
        "recent_high_3": float(high.tail(3).max()),
        "recent_low_3": float(low.tail(3).min()),
        "last_8_closes": [round(v, 4) for v in close.tail(8).tolist()],
        "last_8_volumes": [round(v, 4) for v in volume.tail(8).tolist()],
    }


AGENT_SPECS = [
    ("Macro Regime Agent", "macro", "Focus on higher-level trend alignment using EMA structure, VWAP and ADX. Favor trend continuation, avoid noisy mean reversion calls."),
    ("Orderflow Proxy Agent", "microstructure", "Focus on price-location inside candle range, breakout vs rejection behavior, and volume expansion as a proxy for orderflow."),
    ("Mean Reversion Agent", "reversion", "Focus on Bollinger, VWAP distance, and RSI exhaustion. Look for overshoot and snapback setups."),
    ("Breakout Agent", "breakout", "Focus on fresh highs/lows, volatility expansion, and whether momentum is strong enough to justify continuation."),
    ("Pullback Agent", "pullback", "Focus on entering with the dominant trend after shallow pullbacks to EMA/VWAP support or resistance."),
    ("Volatility Agent", "volatility", "Judge whether current ATR regime supports aggressive entries, smaller targets, or no trade."),
    ("Momentum Agent", "momentum", "Focus on ROC-like directional persistence, MACD histogram, and short-term returns."),
    ("RSI Agent", "oscillator", "Use RSI and exhaustion logic, but avoid blind reversals against strong trend."),
    ("MACD Agent", "oscillator", "Use MACD and histogram slope to assess trend acceleration or loss of momentum."),
    ("Bollinger Agent", "oscillator", "Use Bollinger band stretch and mean reversion context."),
    ("Stochastic Agent", "oscillator", "Use stochastic-style overbought/oversold logic with trend awareness."),
    ("CCI Agent", "oscillator", "Use channel deviation and impulse detection."),
    ("Trend Strength Agent", "trend", "Focus on ADX and DI separation, decide if trend has enough strength to trade."),
    ("Volume Agent", "volume", "Focus on abnormal participation and whether volume confirms or rejects the move."),
    ("Risk Agent", "risk", "Think like a risk manager. If setup quality is poor, vote neutral. If quality is high, support only clean risk-reward situations."),
    ("Execution Agent", "execution", "Think like an execution trader. Favor signals with realistic next-bar entry and avoid late, overstretched entries."),
]


class Agent16ScalpingSystem:
    def __init__(self):
        self.use_llm_agents = bool(getattr(config, "ENABLE_LLM_AGENTS", True))
        self.max_workers = int(getattr(config, "OPENAI_AGENT_MAX_WORKERS", 8))
        if self.use_llm_agents:
            self.agents = [LLMScalpingAgent(name, strategy_type, prompt) for name, strategy_type, prompt in AGENT_SPECS]
        else:
            self.agents = []
        logger.info("✅ 16-Agent系统已初始化，共%s个LLM Agent", len(self.agents))

    def analyze(self, klines_df: pd.DataFrame, current_price: float) -> Dict:
        decisions: List[AgentDecision] = []
        if self.use_llm_agents and self.agents:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_map = {
                    executor.submit(agent.analyze, klines_df, current_price): agent.name
                    for agent in self.agents
                }
                for future in as_completed(future_map):
                    agent_name = future_map[future]
                    try:
                        decisions.append(future.result())
                    except Exception as exc:
                        logger.error("❌ %s 分析失败: %s", agent_name, exc)
                        decisions.append(
                            AgentDecision(
                                agent_name=agent_name,
                                signal=0.0,
                                confidence=0.0,
                                reason="Exception during LLM analysis",
                                entry_price=current_price,
                                stop_loss=current_price,
                                take_profit=current_price,
                            )
                        )

        total_signal = sum(d.signal * d.confidence for d in decisions)
        total_confidence = sum(d.confidence for d in decisions)
        if total_confidence > 0 and decisions:
            avg_signal = total_signal / total_confidence
            avg_confidence = total_confidence / len(decisions)
        else:
            avg_signal = 0.0
            avg_confidence = 0.0

        long_count = sum(1 for d in decisions if d.signal > 0.3)
        short_count = sum(1 for d in decisions if d.signal < -0.3)
        neutral_count = len(decisions) - long_count - short_count

        return build_trade_plan(
            klines_df=klines_df,
            current_price=current_price,
            decisions=decisions,
            avg_signal=avg_signal,
            avg_confidence=avg_confidence,
            long_count=long_count,
            short_count=short_count,
            neutral_count=neutral_count,
        )
