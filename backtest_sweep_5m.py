from __future__ import annotations

import argparse
import asyncio
import csv
import itertools
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from backtest_scalping_5m import Position, ScalpingBacktester


@dataclass(frozen=True)
class SweepConfig:
    bars: int
    warmup_bars: int
    risk_reward: float
    hold_bars: int
    entry_band_scale: float
    atr_stop_scale: float
    consensus_floor: float
    signal_floor: float
    confidence_floor: float
    trend_bias_floor: float


class SweepBacktester(ScalpingBacktester):
    def __init__(self, config: SweepConfig, initial_capital: float = 1000.0):
        super().__init__(initial_capital=initial_capital)
        self.sweep_config = config

    def _apply_overrides(self, analysis: Dict) -> Dict:
        updated = dict(analysis)
        if updated.get("action") not in {"做多", "做空"}:
            updated["tradeable"] = False
            return updated

        snapshot = dict(updated.get("market_snapshot", {}))
        if (
            abs(float(updated.get("signal", 0.0))) < self.sweep_config.signal_floor
            or float(updated.get("consensus_ratio", 0.0)) < self.sweep_config.consensus_floor
            or float(updated.get("confidence", 0.0)) < self.sweep_config.confidence_floor
        ):
            updated["tradeable"] = False
            return updated

        trend_bias = float(snapshot.get("trend_bias", 0.0))
        if updated["action"] == "做多" and trend_bias < self.sweep_config.trend_bias_floor:
            updated["tradeable"] = False
            return updated
        if updated["action"] == "做空" and trend_bias > -self.sweep_config.trend_bias_floor:
            updated["tradeable"] = False
            return updated

        entry_price = float(updated["entry_price"])
        stop_distance = abs(entry_price - float(updated["stop_loss"]))
        atr = float(snapshot.get("atr", stop_distance))
        scaled_stop_distance = max(stop_distance * self.sweep_config.atr_stop_scale, atr * 0.35)
        target_distance = scaled_stop_distance * self.sweep_config.risk_reward

        if updated["action"] == "做多":
            updated["stop_loss"] = entry_price - scaled_stop_distance
            updated["take_profit"] = entry_price + target_distance
            updated["take_profit_1"] = entry_price + scaled_stop_distance
            updated["take_profit_2"] = entry_price + scaled_stop_distance * max(1.3, self.sweep_config.risk_reward - 0.2)
        else:
            updated["stop_loss"] = entry_price + scaled_stop_distance
            updated["take_profit"] = entry_price - target_distance
            updated["take_profit_1"] = entry_price - scaled_stop_distance
            updated["take_profit_2"] = entry_price - scaled_stop_distance * max(1.3, self.sweep_config.risk_reward - 0.2)

        entry_min = float(updated.get("entry_min", entry_price))
        entry_max = float(updated.get("entry_max", entry_price))
        lower_width = max(entry_price - entry_min, atr * 0.05)
        upper_width = max(entry_max - entry_price, atr * 0.05)
        updated["entry_min"] = entry_price - lower_width * self.sweep_config.entry_band_scale
        updated["entry_max"] = entry_price + upper_width * self.sweep_config.entry_band_scale
        updated["expected_hold_minutes"] = self.sweep_config.hold_bars * 5
        updated["risk_reward"] = self.sweep_config.risk_reward
        updated["tradeable"] = True
        return updated

    def run_on_dataframe(self, df, warmup_bars: Optional[int] = None) -> Dict:
        warmup = warmup_bars if warmup_bars is not None else self.sweep_config.warmup_bars
        if len(df) <= warmup + 2:
            raise ValueError("Not enough candles for sweep run.")

        equity = self.initial_capital
        peak_equity = equity
        max_drawdown = 0.0
        trades: List[Dict] = []
        equity_curve: List[Dict] = []
        position: Optional[Position] = None

        for idx in range(warmup, len(df) - 1):
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
            analysis = self._apply_overrides(analysis)
            if not analysis.get("tradeable"):
                continue

            candidate = self._create_position(analysis, next_bar, equity)
            if candidate is not None:
                candidate.planned_hold_bars = self.sweep_config.hold_bars
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
        reasons = Counter(t["reason"] for t in trades)

        return {
            "bars": len(df),
            "start": df["timestamp"].iloc[0],
            "end": df["timestamp"].iloc[-1],
            "days": (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds() / 86400,
            "initial_capital": self.initial_capital,
            "final_capital": equity,
            "net_pnl": equity - self.initial_capital,
            "return_pct": (equity / self.initial_capital - 1) if self.initial_capital else 0.0,
            "trades": len(trades),
            "win_rate": len(wins) / len(trades) if trades else 0.0,
            "profit_factor": gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0),
            "avg_pnl": sum(t["pnl"] for t in trades) / len(trades) if trades else 0.0,
            "avg_hold_bars": avg_hold_bars,
            "avg_hold_minutes": avg_hold_bars * 5,
            "max_drawdown_pct": max_drawdown,
            "time_exit_rate": reasons.get("time_exit", 0) / len(trades) if trades else 0.0,
            "take_profit_rate": reasons.get("take_profit", 0) / len(trades) if trades else 0.0,
            "stop_loss_rate": reasons.get("stop_loss", 0) / len(trades) if trades else 0.0,
            "trade_log": trades,
        }


def _parse_list(values: Optional[List[str]], cast):
    if not values:
        return []
    parsed = []
    for chunk in values:
        for item in chunk.split(","):
            item = item.strip()
            if item:
                parsed.append(cast(item))
    return parsed


def _write_csv(path: Path, rows: List[Dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


async def run_sweep(args) -> Path:
    bars_list = _parse_list(args.bars, int) or [500]
    warmup_list = _parse_list(args.warmup, int) or [120]
    rr_list = _parse_list(args.risk_reward, float) or [1.25, 1.55, 1.85]
    hold_list = _parse_list(args.hold_bars, int) or [2, 4, 6]
    entry_band_list = _parse_list(args.entry_band_scale, float) or [0.75, 1.0, 1.25]
    atr_stop_list = _parse_list(args.atr_stop_scale, float) or [0.8, 1.0, 1.2]
    consensus_list = _parse_list(args.consensus_floor, float) or [0.35, 0.45]
    signal_list = _parse_list(args.signal_floor, float) or [0.15, 0.25]
    confidence_list = _parse_list(args.confidence_floor, float) or [0.5, 0.6]
    trend_bias_list = _parse_list(args.trend_bias_floor, float) or [0.55, 0.7]

    base_fetcher = ScalpingBacktester(initial_capital=args.capital)
    candle_cache: Dict[int, object] = {}
    output_rows: List[Dict] = []

    combos = list(
        itertools.product(
            bars_list,
            warmup_list,
            rr_list,
            hold_list,
            entry_band_list,
            atr_stop_list,
            consensus_list,
            signal_list,
            confidence_list,
            trend_bias_list,
        )
    )

    if args.max_runs:
        combos = combos[: args.max_runs]

    for index, combo in enumerate(combos, start=1):
        cfg = SweepConfig(*combo)
        if cfg.bars not in candle_cache:
            candle_cache[cfg.bars] = await base_fetcher.fetch_klines(cfg.bars)
        df = candle_cache[cfg.bars]
        tester = SweepBacktester(cfg, initial_capital=args.capital)
        result = tester.run_on_dataframe(df, warmup_bars=cfg.warmup_bars)
        row = {
            **asdict(cfg),
            "trades": result["trades"],
            "win_rate": round(result["win_rate"], 6),
            "return_pct": round(result["return_pct"], 6),
            "net_pnl": round(result["net_pnl"], 4),
            "profit_factor": round(result["profit_factor"], 6) if result["profit_factor"] != float("inf") else "inf",
            "avg_hold_bars": round(result["avg_hold_bars"], 4),
            "max_drawdown_pct": round(result["max_drawdown_pct"], 6),
            "time_exit_rate": round(result["time_exit_rate"], 6),
            "take_profit_rate": round(result["take_profit_rate"], 6),
            "stop_loss_rate": round(result["stop_loss_rate"], 6),
        }
        output_rows.append(row)
        print(
            f"[{index}/{len(combos)}] bars={cfg.bars} rr={cfg.risk_reward} hold={cfg.hold_bars} "
            f"entry_band={cfg.entry_band_scale} atr_stop={cfg.atr_stop_scale} "
            f"consensus={cfg.consensus_floor} signal={cfg.signal_floor} "
            f"conf={cfg.confidence_floor} trend={cfg.trend_bias_floor} "
            f"trades={row['trades']} ret={row['return_pct']:.4f} pf={row['profit_factor']} "
            f"time_exit={row['time_exit_rate']:.4f}"
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"backtest_sweep_5m_{timestamp}.csv"
    _write_csv(csv_path, output_rows)
    return csv_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parameter sweep for the 5m scalping backtest.")
    parser.add_argument("--bars", action="append", help="Comma-separated bar counts, e.g. 500,2000")
    parser.add_argument("--warmup", action="append", help="Comma-separated warmup bar counts")
    parser.add_argument("--risk-reward", action="append", help="Comma-separated RR targets")
    parser.add_argument("--hold-bars", action="append", help="Comma-separated planned hold bars")
    parser.add_argument("--entry-band-scale", action="append", help="Comma-separated entry band scales")
    parser.add_argument("--atr-stop-scale", action="append", help="Comma-separated ATR stop multipliers")
    parser.add_argument("--consensus-floor", action="append", help="Comma-separated consensus floors")
    parser.add_argument("--signal-floor", action="append", help="Comma-separated signal floors")
    parser.add_argument("--confidence-floor", action="append", help="Comma-separated confidence floors")
    parser.add_argument("--trend-bias-floor", action="append", help="Comma-separated trend bias floors")
    parser.add_argument("--capital", type=float, default=1000.0)
    parser.add_argument("--max-runs", type=int, default=24, help="Cap runs to keep the sweep tractable")
    parser.add_argument("--output-dir", default=str(Path("C:/Users/cyh/Desktop/GOLD-QUANT/_tmp")))
    return parser


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    csv_path = await run_sweep(args)
    print(f"Results written to {csv_path}")


if __name__ == "__main__":
    asyncio.run(main())
