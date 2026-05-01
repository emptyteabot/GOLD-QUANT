from __future__ import annotations

import asyncio
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import requests

import config
from enhanced_macro_analyst import EnhancedMacroAnalyst
from weex_contract_client import WEEXContractClient


def parse_weex_candles(klines: List[List[str]]) -> pd.DataFrame:
    cols = ["timestamp", "open", "high", "low", "close", "volume", "quote_volume"]
    df = pd.DataFrame(klines, columns=cols[: len(klines[0])])
    df["timestamp"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df.iloc[::-1].reset_index(drop=True)


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    work = df.copy().set_index("timestamp")
    out = work.resample(rule, label="right", closed="right").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    ).dropna().reset_index()
    return out


def compute_micro_features(last_df: pd.DataFrame, index_df: pd.DataFrame, mark_df: pd.DataFrame) -> pd.DataFrame:
    df = last_df.merge(index_df, on="timestamp", suffixes=("_last", "_index"))
    df = df.merge(mark_df, on="timestamp")
    df = df.rename(
        columns={
            "open": "open_mark",
            "high": "high_mark",
            "low": "low_mark",
            "close": "close_mark",
            "volume": "volume_mark",
        }
    )
    df["fair_value"] = df["close_index"]
    df["mark_price"] = df["close_mark"]
    df["spread_pct"] = (df["close_last"] - df["fair_value"]) / df["fair_value"]
    df["premium_to_mark"] = (df["close_last"] - df["mark_price"]) / df["mark_price"]
    ratio = (df["close_last"] / df["fair_value"]).replace(0, np.nan)
    df["residual_log"] = np.log(ratio)
    df["spread_mean"] = df["spread_pct"].rolling(100).mean()
    df["spread_std"] = df["spread_pct"].rolling(100).std()
    df["zscore"] = (df["spread_pct"] - df["spread_mean"]) / df["spread_std"]
    df["resid_median"] = df["residual_log"].rolling(100).median()
    df["resid_mad"] = df["residual_log"].rolling(100).apply(
        lambda x: np.median(np.abs(x - np.median(x))),
        raw=True,
    )
    df["robust_zscore"] = (df["residual_log"] - df["resid_median"]) / (1.4826 * df["resid_mad"].replace(0, np.nan))
    df["trend_ema_fast"] = df["close_last"].ewm(span=24, adjust=False).mean()
    df["trend_ema_slow"] = df["close_last"].ewm(span=72, adjust=False).mean()
    df["trend_bias"] = df["trend_ema_fast"] - df["trend_ema_slow"]
    df["price_return"] = df["close_last"].pct_change()
    df["volume_ma"] = df["volume_last"].rolling(48).mean()
    df["volume_std"] = df["volume_last"].rolling(48).std()
    df["volume_z"] = (df["volume_last"] - df["volume_ma"]) / df["volume_std"]
    candle_range = (df["high_last"] - df["low_last"]).replace(0, pd.NA)
    df["obi_proxy"] = ((2 * df["close_last"] - df["high_last"] - df["low_last"]) / candle_range).clip(-1, 1)
    lagged = df["residual_log"].shift(1)
    delta = df["residual_log"] - lagged
    cov = lagged.rolling(100).cov(delta)
    var = lagged.rolling(100).var()
    df["ou_lambda"] = cov / var.replace(0, pd.NA)
    df["ou_half_life"] = np.nan
    mask = df["ou_lambda"] < 0
    df.loc[mask, "ou_half_life"] = (0.69314718056 / (-df.loc[mask, "ou_lambda"])).astype(float)
    return df.dropna(subset=["fair_value", "mark_price", "spread_pct", "zscore", "robust_zscore", "trend_bias", "volume_z", "obi_proxy"])


def fallback_technical(df: pd.DataFrame, price: float) -> Dict:
    close = df["close"]
    ema8 = close.ewm(span=8, adjust=False).mean().iloc[-1]
    ema21 = close.ewm(span=21, adjust=False).mean().iloc[-1]
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    rsi = float((100 - 100 / (1 + rs)).fillna(50).iloc[-1])
    signal = 1 if ema8 > ema21 else -1 if ema8 < ema21 else 0
    strength = min(abs((ema8 - ema21) / price) * 150, 1.0)
    return {
        "signal": signal,
        "signal_strength": strength,
        "rsi": rsi,
        "ema8": float(ema8),
        "ema21": float(ema21),
    }


def fetch_google_news(query: str, limit: int = 8) -> List[Dict]:
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    resp = requests.get(rss_url, timeout=20)
    root = ET.fromstring(resp.text)
    items = []
    for item in root.findall(".//item")[:limit]:
        items.append(
            {
                "title": item.findtext("title", default=""),
                "link": item.findtext("link", default=""),
                "pubDate": item.findtext("pubDate", default=""),
            }
        )
    return items


@dataclass
class AggregatedContext:
    timestamp: str
    account: Dict
    position: Optional[Dict]
    plans: List[Dict]
    ticker_24h: Dict
    order_book: Dict
    timeframes: Dict[str, pd.DataFrame]
    micro_features: Dict
    macro: Dict
    news: List[Dict]

    def to_payload(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "account": self.account,
            "position": self.position,
            "plans": self.plans,
            "ticker_24h": self.ticker_24h,
            "order_book": self.order_book,
            "micro_features": self.micro_features,
            "macro": self.macro,
            "news": self.news,
            "timeframes": {
                k: {
                    "bars": len(v),
                    "latest": {
                        "timestamp": str(v["timestamp"].iloc[-1]),
                        "open": float(v["open"].iloc[-1]),
                        "high": float(v["high"].iloc[-1]),
                        "low": float(v["low"].iloc[-1]),
                        "close": float(v["close"].iloc[-1]),
                        "volume": float(v["volume"].iloc[-1]),
                    },
                }
                for k, v in self.timeframes.items()
            },
        }


class MarketContextAggregator:
    def __init__(self):
        self.exec_client = WEEXContractClient()
        self.macro = EnhancedMacroAnalyst()

    async def initialize(self):
        await self.exec_client.initialize()

    async def close(self):
        await self.exec_client.close()

    async def _get_usdt_account(self) -> Dict:
        assets = await self.exec_client.get_account_assets()
        for item in assets:
            if item.get("coinName") == "USDT":
                return item
        return {}

    async def collect(self, symbol: str = None) -> AggregatedContext:
        symbol = symbol or config.EXECUTION_SYMBOL
        ticker = await self.exec_client.get_market_ticker(symbol)
        depth = await self.exec_client.get_market_depth(symbol, size=10)
        kl_1m_last = await self.exec_client.get_market_candles(symbol, granularity="1m", limit=300, price_type="LAST")
        kl_1m_index = await self.exec_client.get_market_candles(symbol, granularity="1m", limit=300, price_type="INDEX")
        kl_1m_mark = await self.exec_client.get_market_candles(symbol, granularity="1m", limit=300, price_type="MARK")
        kl_5m_24h = await self.exec_client.get_market_candles(symbol, granularity="5m", limit=288, price_type="LAST")
        position = await self.exec_client._request("GET", "/capi/v2/account/position/singlePosition", query={"symbol": self.exec_client._market_symbol(symbol)})
        plans = await self.exec_client.get_current_plan_orders(symbol)
        account = await self._get_usdt_account()

        last_1m = parse_weex_candles(kl_1m_last)
        index_1m = parse_weex_candles(kl_1m_index)
        mark_1m = parse_weex_candles(kl_1m_mark)
        micro_df = compute_micro_features(last_1m, index_1m, mark_1m)
        latest = micro_df.iloc[-1]

        bid_qty = sum(float(x[1]) for x in depth.get("bids", [])[:5]) if depth else 0.0
        ask_qty = sum(float(x[1]) for x in depth.get("asks", [])[:5]) if depth else 0.0
        order_book_obi = (bid_qty - ask_qty) / (bid_qty + ask_qty) if (bid_qty + ask_qty) else 0.0

        frames = {
            "1m": last_1m.tail(100),
            "3m": resample_ohlcv(last_1m, "3min").tail(100),
            "5m": resample_ohlcv(last_1m, "5min").tail(100),
        }
        macro = self._sanitize_macro(self.macro.calculate_enhanced_macro_score())
        news = fetch_google_news('XAUT OR "Tether Gold" OR "gold price" OR "USDT depeg"', limit=8)

        return AggregatedContext(
            timestamp=str(datetime.now()),
            account=account,
            position=position[0] if position else None,
            plans=plans if isinstance(plans, list) else [],
            ticker_24h={
                "last": float(ticker["last"]),
                "index_price": float(ticker["indexPrice"]),
                "mark_price": float(ticker["markPrice"]),
                "change_24h_pct": float(ticker["priceChangePercent"]),
                "high_24h": float(ticker["high_24h"]),
                "low_24h": float(ticker["low_24h"]),
                "quote_volume_24h": float(ticker["volume_24h"]),
                "bars_5m_24h": [
                    {
                        **row,
                        "timestamp": str(row["timestamp"]),
                    }
                    for row in parse_weex_candles(kl_5m_24h).to_dict(orient="records")
                ],
            },
            order_book={
                "best_bid": float(ticker["best_bid"]),
                "best_ask": float(ticker["best_ask"]),
                "obi": order_book_obi,
                "top_bids": depth.get("bids", [])[:10] if depth else [],
                "top_asks": depth.get("asks", [])[:10] if depth else [],
            },
            timeframes=frames,
            micro_features={
                "premium_to_index_pct": float((float(ticker["last"]) - float(ticker["indexPrice"])) / float(ticker["indexPrice"])),
                "premium_to_mark_pct": float((float(ticker["last"]) - float(ticker["markPrice"])) / float(ticker["markPrice"])),
                "spread_pct": float(latest["spread_pct"]),
                "zscore": float(latest["zscore"]),
                "robust_zscore": float(latest["robust_zscore"]),
                "trend_bias": float(latest["trend_bias"]),
                "volume_z": float(latest["volume_z"]),
                "obi_proxy": float(latest["obi_proxy"]),
                "ou_half_life": float(latest["ou_half_life"]),
            },
            macro=macro,
            news=news,
        )

    @staticmethod
    def _sanitize_macro(macro_result: Dict) -> Dict:
        score = float(macro_result.get("score", 0))
        details = list(macro_result.get("details", [])) if isinstance(macro_result.get("details", []), list) else []
        details_text = " ".join(str(x) for x in details)
        suspicious = any(token in details_text for token in ["326.", "-322.", "CPI"])
        if suspicious or abs(score) > 95:
            return {"score": 0, "details": ["macro_data_sanitized_to_neutral"]}
        return macro_result
