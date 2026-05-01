from __future__ import annotations

import argparse
import asyncio
import math
from dataclasses import dataclass
from typing import Dict, List, Optional

import aiohttp
import pandas as pd

import config
from agent_16_scalping_system import Agent16ScalpingSystem
from risk_manager import RiskManager


@dataclass
class Position:
    side: str
    entry_time: pd.Timestamp
    entry_price: float
    stop_loss: float
    take_profit: float
    oz_size: float
    leverage: int
    setup_type: str
    risk_reward: float
    planned_hold_bars: int
    bars_held: int = 0


class ScalpingBacktester:
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.agent_system = Agent16ScalpingSystem()
        self.risk_manager = RiskManager()

    async def fetch_klines(self, limit: int) -> pd.DataFrame:
        raw: List[List[str]] = []
        after = None
        async with aiohttp.ClientSession() as session:
            while len(raw) < limit:
                batch = min(300, limit - len(raw))
                url = (
                    f"https://www.okx.com/api/v5/market/history-candles"
                    f"?instId={config.INST_ID}&bar=5m&limit={batch}"
                )
                if after:
                    url += f"&after={after}"
                async with session.get(url, timeout=15, proxy=config.HTTP_PROXY) as resp:
                    data = await resp.json()
                    rows = data.get("data", [])
                    if not rows:
                        break
                    raw.extend(rows)
                    after = rows[-1][0]
                    if len(rows) < batch:
                        break

        if not raw:
            raise RuntimeError("No historical candles returned from OKX.")

        columns = ["timestamp", "open", "high", "low", "close", "volume", "volCcy", "volCcyQuote", "confirm"]
        df = pd.DataFrame(raw, columns=columns[: len(raw[0])])
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df.iloc[::-1].reset_index(drop=True)

    def _mark_to_market(self, equity: float, position: Optional[Position], close_price: float) -> float:
        if not position:
            return equity
        sign = 1 if position.side == "long" else -1
        return equity + (close_price - position.entry_price) * position.oz_size * sign

    def _create_position(self, analysis: Dict, next_bar: pd.Series, equity: float) -> Optional[Position]:
        side = "long" if analysis["action"] == "做多" else "short"
        next_open = float(next_bar["open"])
        entry_min = float(analysis.get("entry_min", analysis["entry_price"]))
        entry_max = float(analysis.get("entry_max", analysis["entry_price"]))
        if not (entry_min <= next_open <= entry_max):
            return None

        entry_ref = float(analysis["entry_price"])
        stop_distance = abs(entry_ref - float(analysis["stop_loss"]))
        target_distance = abs(float(analysis["take_profit"]) - entry_ref)
        if stop_distance <= 0 or target_distance <= 0:
            return None

        if side == "long":
            stop_loss = next_open - stop_distance
            take_profit = next_open + target_distance
        else:
            stop_loss = next_open + stop_distance
            take_profit = next_open - target_distance

        position_info = self.risk_manager.calculate_scalping_position_size(
            account={"total_equity": equity, "available": equity},
            price=next_open,
            leverage=int(analysis["leverage"]),
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            position_size_pct=float(analysis["position_size_pct"]),
            confidence=float(analysis["confidence"]),
        )
        if not position_info:
            return None

        hold_minutes = int(analysis.get("expected_hold_minutes", 10))
        hold_bars = max(1, math.ceil(hold_minutes / 5))

        return Position(
            side=side,
            entry_time=next_bar["timestamp"],
            entry_price=next_open,
            stop_loss=stop_loss,
            take_profit=take_profit,
            oz_size=float(position_info["oz_size"]),
            leverage=int(analysis["leverage"]),
            setup_type=str(analysis.get("setup_type", "unknown")),
            risk_reward=float(analysis.get("risk_reward", 0.0)),
            planned_hold_bars=hold_bars,
        )

    def _close_trade(
        self,
        position: Position,
        exit_time: pd.Timestamp,
        exit_price: float,
        reason: str,
        equity: float,
    ) -> Dict:
        sign = 1 if position.side == "long" else -1
        pnl = (exit_price - position.entry_price) * position.oz_size * sign
        pnl_pct = pnl / equity if equity else 0.0
        return {
            "entry_time": position.entry_time,
            "exit_time": exit_time,
            "side": position.side,
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "oz_size": position.oz_size,
            "leverage": position.leverage,
            "setup_type": position.setup_type,
            "risk_reward": position.risk_reward,
            "bars_held": position.bars_held,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "reason": reason,
        }

    def run_on_dataframe(self, df: pd.DataFrame, warmup_bars: int = 120) -> Dict:
        if len(df) <= warmup_bars + 2:
            raise ValueError("Not enough candles for backtest.")

        equity = self.initial_capital
        peak_equity = equity
        max_drawdown = 0.0
        trades: List[Dict] = []
        equity_curve: List[Dict] = []
        position: Optional[Position] = None

        for idx in range(warmup_bars, len(df) - 1):
            current_bar = df.iloc[idx]
            next_bar = df.iloc[idx + 1]

            if position and current_bar["timestamp"] >= position.entry_time:
                position.bars_held += 1

                stop_hit = False
                tp_hit = False
                if position.side == "long":
                    stop_hit = current_bar["low"] <= position.stop_loss
                    tp_hit = current_bar["high"] >= position.take_profit
                else:
                    stop_hit = current_bar["high"] >= position.stop_loss
                    tp_hit = current_bar["low"] <= position.take_profit

                if stop_hit and tp_hit:
                    reason = "stop_and_tp_same_bar_stop_first"
                    exit_price = position.stop_loss
                elif stop_hit:
                    reason = "stop_loss"
                    exit_price = position.stop_loss
                elif tp_hit:
                    reason = "take_profit"
                    exit_price = position.take_profit
                elif position.bars_held >= position.planned_hold_bars:
                    reason = "time_exit"
                    exit_price = float(current_bar["close"])
                else:
                    exit_price = None
                    reason = ""

                if exit_price is not None:
                    trade = self._close_trade(position, current_bar["timestamp"], exit_price, reason, equity)
                    equity += trade["pnl"]
                    trades.append(trade)
                    position = None

            marked_equity = self._mark_to_market(equity, position, float(current_bar["close"]))
            peak_equity = max(peak_equity, marked_equity)
            drawdown = (marked_equity - peak_equity) / peak_equity if peak_equity else 0.0
            max_drawdown = min(max_drawdown, drawdown)
            equity_curve.append({"timestamp": current_bar["timestamp"], "equity": marked_equity})

            if position is not None:
                continue

            history = df.iloc[: idx + 1].copy()
            analysis = self.agent_system.analyze(history, float(current_bar["close"]))
            if not analysis.get("tradeable"):
                continue
            if analysis["action"] not in {"做多", "做空"}:
                continue

            candidate = self._create_position(analysis, next_bar, equity)
            if candidate is not None:
                position = candidate

        if position is not None:
            last_bar = df.iloc[-1]
            trade = self._close_trade(position, last_bar["timestamp"], float(last_bar["close"]), "end_of_backtest", equity)
            equity += trade["pnl"]
            trades.append(trade)

        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        gross_profit = sum(t["pnl"] for t in wins)
        gross_loss = abs(sum(t["pnl"] for t in losses))
        avg_hold_bars = sum(t["bars_held"] for t in trades) / len(trades) if trades else 0.0

        return {
            "bars": len(df),
            "timeframe": "5m",
            "start": df["timestamp"].iloc[0],
            "end": df["timestamp"].iloc[-1],
            "days": (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds() / 86400,
            "initial_capital": self.initial_capital,
            "final_capital": equity,
            "net_pnl": equity - self.initial_capital,
            "return_pct": (equity / self.initial_capital - 1) if self.initial_capital else 0.0,
            "trades": len(trades),
            "win_rate": len(wins) / len(trades) if trades else 0.0,
            "profit_factor": gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0,
            "avg_pnl": sum(t["pnl"] for t in trades) / len(trades) if trades else 0.0,
            "avg_hold_bars": avg_hold_bars,
            "avg_hold_minutes": avg_hold_bars * 5,
            "max_drawdown_pct": max_drawdown,
            "equity_curve": equity_curve,
            "trade_log": trades,
        }


def _print_summary(result: Dict) -> None:
    print("=" * 80)
    print(f"5m backtest over {result['bars']} candles")
    print(f"Range: {result['start']} -> {result['end']} ({result['days']:.2f} days)")
    print(f"Trades: {result['trades']}")
    print(f"Win rate: {result['win_rate']:.2%}")
    print(f"Return: {result['return_pct']:.2%}")
    print(f"Net PnL: ${result['net_pnl']:.2f}")
    print(f"Profit factor: {result['profit_factor']:.2f}")
    print(f"Avg PnL / trade: ${result['avg_pnl']:.2f}")
    print(f"Avg hold: {result['avg_hold_bars']:.2f} bars ({result['avg_hold_minutes']:.1f} min)")
    print(f"Max drawdown: {result['max_drawdown_pct']:.2%}")
    print("=" * 80)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest current 5m scalping planner.")
    parser.add_argument("--bars", type=int, action="append", default=None, help="Number of 5m candles to test.")
    parser.add_argument("--capital", type=float, default=1000.0, help="Initial capital.")
    parser.add_argument("--warmup", type=int, default=120, help="Warmup candles before first decision.")
    args = parser.parse_args()

    test_sizes = args.bars or [500, 2000]
    tester = ScalpingBacktester(initial_capital=args.capital)

    for bar_count in test_sizes:
        df = await tester.fetch_klines(bar_count)
        result = tester.run_on_dataframe(df, warmup_bars=args.warmup)
        _print_summary(result)


if __name__ == "__main__":
    asyncio.run(main())
