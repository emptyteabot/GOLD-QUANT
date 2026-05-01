from __future__ import annotations

import argparse
import asyncio
import math
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional

import aiohttp
import numpy as np
import pandas as pd

import config


@dataclass
class Position:
    side: str
    entry_time: pd.Timestamp
    entry_price: float
    stop_loss: float
    take_profit: float
    units: float
    planned_hold_bars: int
    bars_held: int = 0


class XautFairValueBacktester:
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.base_url = "https://www.okx.com"

    async def fetch_klines(self, inst_id: str, limit: int, bar: str = "5m", endpoint: str = "history-candles") -> pd.DataFrame:
        raw: List[List[str]] = []
        after = None
        async with aiohttp.ClientSession() as session:
            while len(raw) < limit:
                batch = min(300, limit - len(raw))
                url = f"{self.base_url}/api/v5/market/{endpoint}?instId={inst_id}&bar={bar}&limit={batch}"
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

        if not raw and endpoint == "history-candles":
            return await self.fetch_klines(inst_id, limit, bar=bar, endpoint="candles")

        if not raw:
            raise RuntimeError(f"No historical candles returned for {inst_id}.")

        cols = ["timestamp", "open", "high", "low", "close", "volume", "volCcy", "volCcyQuote", "confirm"]
        df = pd.DataFrame(raw, columns=cols[: len(raw[0])])
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        df = df.iloc[::-1].reset_index(drop=True)
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df.columns = ["timestamp"] + [f"{inst_id}_{c}" for c in ["open", "high", "low", "close", "volume"]]
        return df

    async def build_dataset(self, limit: int) -> pd.DataFrame:
        xaut = await self.fetch_klines("XAUT-USDT", limit)
        xau_swap = await self.fetch_klines("XAU-USDT-SWAP", limit)
        try:
            usdt_usd = await self.fetch_klines("USDT-USD", limit)
        except Exception:
            usdc_usdt = await self.fetch_klines("USDC-USDT", limit)
            usdc_usdt["USDT-USD_close"] = 1 / usdc_usdt["USDC-USDT_close"]
            usdc_usdt["USDT-USD_open"] = 1 / usdc_usdt["USDC-USDT_open"]
            usdc_usdt["USDT-USD_high"] = 1 / usdc_usdt["USDC-USDT_low"]
            usdc_usdt["USDT-USD_low"] = 1 / usdc_usdt["USDC-USDT_high"]
            usdc_usdt["USDT-USD_volume"] = usdc_usdt["USDC-USDT_volume"]
            usdt_usd = usdc_usdt[["timestamp", "USDT-USD_open", "USDT-USD_high", "USDT-USD_low", "USDT-USD_close", "USDT-USD_volume"]]
        try:
            paxg = await self.fetch_klines("PAXG-USDT", limit)
        except Exception:
            paxg = pd.DataFrame({"timestamp": xaut["timestamp"]})

        df = xaut.merge(xau_swap, on="timestamp", how="inner")
        df = df.merge(usdt_usd, on="timestamp", how="inner")
        df = df.merge(paxg, on="timestamp", how="left")
        df = df.sort_values("timestamp").reset_index(drop=True)

        df["fair_value"] = df["XAU-USDT-SWAP_close"] * df["USDT-USD_close"]
        df["spread_pct"] = (df["XAUT-USDT_close"] - df["fair_value"]) / df["fair_value"]
        df["residual_log"] = np.log(df["XAUT-USDT_close"] / df["fair_value"])
        df["spread_mean"] = df["spread_pct"].rolling(120).mean()
        df["spread_std"] = df["spread_pct"].rolling(120).std()
        df["zscore"] = (df["spread_pct"] - df["spread_mean"]) / df["spread_std"]
        df["resid_median"] = df["residual_log"].rolling(120).median()
        df["resid_mad"] = df["residual_log"].rolling(120).apply(
            lambda x: np.median(np.abs(x - np.median(x))), raw=True
        )
        df["robust_zscore"] = (df["residual_log"] - df["resid_median"]) / (1.4826 * df["resid_mad"].replace(0, np.nan))
        if "PAXG-USDT_close" in df:
            df["premium_to_paxg"] = (df["XAUT-USDT_close"] - df["PAXG-USDT_close"]) / df["PAXG-USDT_close"]
            df["premium_to_paxg"] = df["premium_to_paxg"].fillna(0.0)
        else:
            df["premium_to_paxg"] = 0.0
        df["trend_ema_fast"] = df["XAU-USDT-SWAP_close"].ewm(span=24, adjust=False).mean()
        df["trend_ema_slow"] = df["XAU-USDT-SWAP_close"].ewm(span=72, adjust=False).mean()
        df["trend_bias"] = df["trend_ema_fast"] - df["trend_ema_slow"]
        df["price_return"] = df["XAUT-USDT_close"].pct_change()
        df["volume_ma"] = df["XAUT-USDT_volume"].rolling(48).mean()
        df["volume_std"] = df["XAUT-USDT_volume"].rolling(48).std()
        df["volume_z"] = (df["XAUT-USDT_volume"] - df["volume_ma"]) / df["volume_std"]
        candle_range = (df["XAUT-USDT_high"] - df["XAUT-USDT_low"]).replace(0, np.nan)
        df["obi_proxy"] = ((2 * df["XAUT-USDT_close"] - df["XAUT-USDT_high"] - df["XAUT-USDT_low"]) / candle_range).clip(-1, 1)
        df["obi_proxy_delta_3"] = df["obi_proxy"] - df["obi_proxy"].shift(3)
        df["rolling_low_6"] = df["XAUT-USDT_low"].rolling(6).min()
        df["rolling_high_6"] = df["XAUT-USDT_high"].rolling(6).max()
        df["absorption_bullish"] = (
            (df["XAUT-USDT_low"] <= df["rolling_low_6"].shift(1))
            & (df["obi_proxy_delta_3"] > 0.20)
            & (df["volume_z"] > 0.5)
        )
        df["absorption_bearish"] = (
            (df["XAUT-USDT_high"] >= df["rolling_high_6"].shift(1))
            & (df["obi_proxy_delta_3"] < -0.20)
            & (df["volume_z"] > 0.5)
        )
        df["volume_climax_long"] = (df["volume_z"] > 1.2) & (df["price_return"] < -0.0015)
        df["volume_climax_short"] = (df["volume_z"] > 1.2) & (df["price_return"] > 0.0015)

        lagged = df["residual_log"].shift(1)
        delta = df["residual_log"] - lagged
        cov = lagged.rolling(120).cov(delta)
        var = lagged.rolling(120).var()
        df["ou_lambda"] = cov / var.replace(0, np.nan)
        df["ou_half_life"] = np.where(
            df["ou_lambda"] < 0,
            np.log(2) / (-df["ou_lambda"]),
            np.nan,
        )

        required = [
            "fair_value",
            "spread_pct",
            "spread_mean",
            "spread_std",
            "zscore",
            "robust_zscore",
            "trend_ema_fast",
            "trend_ema_slow",
            "trend_bias",
            "volume_z",
            "obi_proxy",
            "ou_lambda",
            "ou_half_life",
        ]
        return df.dropna(subset=required).reset_index(drop=True)

    def _mark_to_market(self, equity: float, position: Optional[Position], price: float) -> float:
        if not position:
            return equity
        sign = 1 if position.side == "long" else -1
        return equity + (price - position.entry_price) * position.units * sign

    def _entry_signal(
        self,
        row: pd.Series,
        entry_z: float,
        exit_z: float,
        long_only: bool,
        mode: str = "advanced",
    ) -> Optional[str]:
        zscore = float(row["zscore"])
        robust_z = float(row.get("robust_zscore", zscore))
        usdt_ok = 0.998 <= float(row["USDT-USD_close"]) <= 1.002
        if not usdt_ok:
            return None

        bullish_filter = float(row["trend_bias"]) >= 0
        bearish_filter = float(row["trend_bias"]) <= 0
        paxg_confirm = abs(float(row.get("premium_to_paxg", 0.0))) <= 0.01
        half_life = float(row.get("ou_half_life", np.nan))
        ou_ok = np.isfinite(half_life) and 2 <= half_life <= 48

        if mode == "basic":
            if zscore <= -entry_z and bullish_filter and paxg_confirm:
                return "long"
            if not long_only and zscore >= entry_z and bearish_filter and paxg_confirm:
                return "short"
            return None

        long_capitulation = bool(row.get("volume_climax_long", False)) or bool(row.get("absorption_bullish", False))
        short_capitulation = bool(row.get("volume_climax_short", False)) or bool(row.get("absorption_bearish", False))
        volume_ok = float(row.get("volume_z", 0.0)) > -0.5
        bullish_gate = bullish_filter or long_capitulation
        bearish_gate = bearish_filter or short_capitulation

        if robust_z <= -entry_z and bullish_gate and paxg_confirm and ou_ok and volume_ok:
            return "long"
        if not long_only and robust_z >= entry_z and bearish_gate and paxg_confirm and ou_ok and volume_ok:
            return "short"
        return None

    def run_backtest(
        self,
        df: pd.DataFrame,
        entry_z: float = 2.0,
        exit_z: float = 0.35,
        stop_loss_pct: float = 0.006,
        take_profit_pct: float = 0.012,
        hold_bars: int = 12,
        position_pct: float = 0.20,
        long_only: bool = True,
        mode: str = "advanced",
    ) -> Dict:
        equity = self.initial_capital
        peak_equity = equity
        max_drawdown = 0.0
        trades: List[Dict] = []
        position: Optional[Position] = None

        for idx in range(1, len(df) - 1):
            row = df.iloc[idx]
            next_row = df.iloc[idx + 1]
            current_close = float(row["XAUT-USDT_close"])

            if position and row["timestamp"] >= position.entry_time:
                position.bars_held += 1
                stop_hit = False
                tp_hit = False
                low = float(row["XAUT-USDT_low"])
                high = float(row["XAUT-USDT_high"])
                if position.side == "long":
                    stop_hit = low <= position.stop_loss
                    tp_hit = high >= position.take_profit
                else:
                    stop_hit = high >= position.stop_loss
                    tp_hit = low <= position.take_profit

                if stop_hit and tp_hit:
                    reason = "stop_and_tp_same_bar_stop_first"
                    exit_price = position.stop_loss
                elif stop_hit:
                    reason = "stop_loss"
                    exit_price = position.stop_loss
                elif tp_hit:
                    reason = "take_profit"
                    exit_price = position.take_profit
                elif position.bars_held >= position.planned_hold_bars or abs(float(row.get("robust_zscore", row["zscore"]))) <= exit_z:
                    reason = "time_or_mean_revert_exit"
                    exit_price = current_close
                else:
                    exit_price = None
                    reason = ""

                if exit_price is not None:
                    sign = 1 if position.side == "long" else -1
                    pnl = (exit_price - position.entry_price) * position.units * sign
                    trades.append(
                        {
                            "entry_time": position.entry_time,
                            "exit_time": row["timestamp"],
                            "side": position.side,
                            "entry_price": position.entry_price,
                            "exit_price": exit_price,
                            "units": position.units,
                            "bars_held": position.bars_held,
                            "pnl": pnl,
                            "reason": reason,
                            "entry_zscore": position.entry_price,  # placeholder kept for schema stability
                        }
                    )
                    equity += pnl
                    position = None

            marked = self._mark_to_market(equity, position, current_close)
            peak_equity = max(peak_equity, marked)
            if peak_equity:
                max_drawdown = min(max_drawdown, (marked - peak_equity) / peak_equity)

            if position is not None:
                continue

            side = self._entry_signal(row, entry_z=entry_z, exit_z=exit_z, long_only=long_only, mode=mode)
            if side is None:
                continue

            next_open = float(next_row["XAUT-USDT_open"])
            notional = equity * position_pct
            units = notional / next_open
            if units <= 0:
                continue

            if side == "long":
                stop_loss = next_open * (1 - stop_loss_pct)
                take_profit = next_open * (1 + take_profit_pct)
            else:
                stop_loss = next_open * (1 + stop_loss_pct)
                take_profit = next_open * (1 - take_profit_pct)

            position = Position(
                side=side,
                entry_time=next_row["timestamp"],
                entry_price=next_open,
                stop_loss=stop_loss,
                take_profit=take_profit,
                units=units,
                planned_hold_bars=hold_bars,
            )

        if position is not None:
            last = df.iloc[-1]
            final_price = float(last["XAUT-USDT_close"])
            sign = 1 if position.side == "long" else -1
            pnl = (final_price - position.entry_price) * position.units * sign
            trades.append(
                {
                    "entry_time": position.entry_time,
                    "exit_time": last["timestamp"],
                    "side": position.side,
                    "entry_price": position.entry_price,
                    "exit_price": final_price,
                    "units": position.units,
                    "bars_held": position.bars_held,
                    "pnl": pnl,
                    "reason": "end_of_backtest",
                    "entry_zscore": position.entry_price,
                }
            )
            equity += pnl

        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        reasons = Counter(t["reason"] for t in trades)
        gross_profit = sum(t["pnl"] for t in wins)
        gross_loss = abs(sum(t["pnl"] for t in losses))

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
            "max_drawdown_pct": max_drawdown,
            "avg_hold_bars": sum(t["bars_held"] for t in trades) / len(trades) if trades else 0.0,
            "exit_reason_distribution": dict(reasons),
            "mode": mode,
            "trade_log": trades,
        }


def print_summary(name: str, result: Dict) -> None:
    print("=" * 80)
    print(name)
    print(f"Range: {result['start']} -> {result['end']} ({result['days']:.2f} days)")
    print(f"Bars: {result['bars']}")
    print(f"Trades: {result['trades']}")
    print(f"Win rate: {result['win_rate']:.2%}")
    print(f"Return: {result['return_pct']:.2%}")
    print(f"Net PnL: ${result['net_pnl']:.2f}")
    print(f"Profit factor: {result['profit_factor']:.2f}")
    print(f"Max drawdown: {result['max_drawdown_pct']:.2%}")
    print(f"Avg hold bars: {result['avg_hold_bars']:.2f}")
    print(f"Exit reasons: {result['exit_reason_distribution']}")
    print("=" * 80)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest XAUT fair value mean reversion.")
    parser.add_argument("--bars", type=int, action="append", default=None, help="Candle counts to test.")
    parser.add_argument("--entry-z", type=float, default=2.0)
    parser.add_argument("--exit-z", type=float, default=0.35)
    parser.add_argument("--stop-loss-pct", type=float, default=0.006)
    parser.add_argument("--take-profit-pct", type=float, default=0.012)
    parser.add_argument("--hold-bars", type=int, default=12)
    parser.add_argument("--position-pct", type=float, default=0.20)
    parser.add_argument("--capital", type=float, default=1000.0)
    parser.add_argument("--allow-short", action="store_true")
    parser.add_argument("--mode", choices=["basic", "advanced"], default="advanced")
    args = parser.parse_args()

    sizes = args.bars or [500, 2000]
    backtester = XautFairValueBacktester(initial_capital=args.capital)
    for bars in sizes:
        df = await backtester.build_dataset(bars)
        result = backtester.run_backtest(
            df,
            entry_z=args.entry_z,
            exit_z=args.exit_z,
            stop_loss_pct=args.stop_loss_pct,
            take_profit_pct=args.take_profit_pct,
            hold_bars=args.hold_bars,
            position_pct=args.position_pct,
            long_only=not args.allow_short,
            mode=args.mode,
        )
        print_summary(f"XAUT fair value backtest [{args.mode}] ({bars} bars)", result)


if __name__ == "__main__":
    asyncio.run(main())
