from __future__ import annotations

from typing import Dict, List, Optional

import aiohttp

import config


class OKXMarketDataClient:
    def __init__(self):
        self.base_url = config.OKX_BASE_URL.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def _get_json(self, url: str) -> Dict:
        if self.session is None:
            raise RuntimeError("OKX market data client not initialized")
        async with self.session.get(url, timeout=20, proxy=config.HTTP_PROXY) as resp:
            return await resp.json()

    async def get_ticker(self, inst_id: str) -> Optional[Dict]:
        data = await self._get_json(f"{self.base_url}/api/v5/market/ticker?instId={inst_id}")
        if data.get("code") == "0" and data.get("data"):
            return data["data"][0]
        return None

    async def get_order_book(self, inst_id: str, depth: int = 10) -> Optional[Dict]:
        data = await self._get_json(f"{self.base_url}/api/v5/market/books?instId={inst_id}&sz={depth}")
        if data.get("code") == "0" and data.get("data"):
            return data["data"][0]
        return None

    async def get_klines(self, inst_id: str, bar: str = "5m", limit: int = 100, endpoint: str = "history-candles") -> Optional[List]:
        rows: List = []
        after = None
        while len(rows) < limit:
            batch = min(300, limit - len(rows))
            url = f"{self.base_url}/api/v5/market/{endpoint}?instId={inst_id}&bar={bar}&limit={batch}"
            if after:
                url += f"&after={after}"
            data = await self._get_json(url)
            if data.get("code") != "0" or not data.get("data"):
                break
            batch_rows = data["data"]
            rows.extend(batch_rows)
            after = batch_rows[-1][0]
            if len(batch_rows) < batch:
                break
        if not rows and endpoint == "history-candles":
            return await self.get_klines(inst_id, bar=bar, limit=limit, endpoint="candles")
        return rows or None
