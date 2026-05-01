from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional

import aiohttp

import config


class WEEXContractClient:
    def __init__(self):
        self.api_key = config.WEEX_API_KEY
        self.secret_key = config.WEEX_SECRET_KEY
        self.passphrase = config.WEEX_PASSPHRASE
        self.base_url = config.WEEX_BASE_URL.rstrip("/")
        self.locale = config.WEEX_LOCALE
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session is not None:
            await self.session.close()
            self.session = None

    def _timestamp(self) -> str:
        return str(int(time.time() * 1000))

    @staticmethod
    def _trade_symbol(symbol: str) -> str:
        symbol = symbol.strip()
        if symbol.lower().startswith("cmt_"):
            return symbol[4:].upper()
        return symbol.upper()

    @staticmethod
    def _market_symbol(symbol: str) -> str:
        symbol = symbol.strip()
        if symbol.lower().startswith("cmt_"):
            return symbol.lower()
        return f"cmt_{symbol.lower()}"

    def _sign(self, timestamp: str, method: str, request_path: str, query_string: str = "", body: str = "") -> str:
        message = timestamp + method.upper() + request_path + query_string + body
        digest = hmac.new(self.secret_key.encode(), message.encode(), hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    def _headers(self, signature: str, timestamp: str) -> Dict[str, str]:
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": self.locale,
        }

    async def _request(
        self,
        method: str,
        request_path: str,
        *,
        query: Dict[str, Any] | None = None,
        body: Dict[str, Any] | None = None,
        auth: bool = True,
    ) -> Any:
        if self.session is None:
            raise RuntimeError("WEEX client not initialized")

        query = query or {}
        body = body or {}
        query_string = ""
        if query:
            query_string = "?" + "&".join(f"{k}={v}" for k, v in query.items() if v is not None)
        body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=False) if body else ""
        url = f"{self.base_url}{request_path}{query_string}"

        headers = {"Content-Type": "application/json", "locale": self.locale}
        if auth:
            ts = self._timestamp()
            signature = self._sign(ts, method, request_path, query_string, body_json)
            headers = self._headers(signature, ts)

        proxy = config.HTTP_PROXY
        async with self.session.request(
            method.upper(),
            url,
            headers=headers,
            data=body_json if method.upper() != "GET" and body_json else None,
            timeout=20,
            proxy=proxy,
        ) as resp:
            text = await resp.text()
            try:
                return json.loads(text)
            except Exception:
                return {"http_status": resp.status, "raw_text": text}

    async def ping(self) -> Dict[str, Any]:
        return await self._request("GET", "/capi/v2/market/time", auth=False)

    async def get_market_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        data = await self._request("GET", "/capi/v2/market/ticker", query={"symbol": self._market_symbol(symbol)}, auth=False)
        return data if isinstance(data, dict) else None

    async def get_market_depth(self, symbol: str, size: int = 10) -> Optional[Dict[str, Any]]:
        data = await self._request("GET", "/capi/v2/market/depth", query={"symbol": self._market_symbol(symbol), "size": size}, auth=False)
        return data if isinstance(data, dict) else None

    async def get_market_candles(self, symbol: str, granularity: str = "1m", limit: int = 100, price_type: str = "LAST") -> Optional[List]:
        data = await self._request(
            "GET",
            "/capi/v2/market/candles",
            query={
                "symbol": self._market_symbol(symbol),
                "granularity": granularity,
                "limit": limit,
                "priceType": price_type,
            },
            auth=False,
        )
        return data if isinstance(data, list) else None

    async def get_contract_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        data = await self._request("GET", "/capi/v2/market/contracts", query={"symbol": self._market_symbol(symbol)}, auth=False)
        if isinstance(data, list) and data:
            return data[0]
        return None

    async def get_account_assets(self) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/capi/v2/account/assets")
        return data if isinstance(data, list) else []

    async def get_single_position(self, symbol: str) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/capi/v2/account/position/singlePosition", query={"symbol": self._market_symbol(symbol)})
        return data if isinstance(data, list) else ([] if data is None else [data] if isinstance(data, dict) else [])

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        body = {
            "symbol": self._market_symbol(symbol),
            "marginMode": config.WEEX_MARGIN_MODE,
            "longLeverage": str(leverage),
            "shortLeverage": str(leverage),
        }
        data = await self._request("POST", "/capi/v2/account/leverage", body=body)
        return isinstance(data, dict) and str(data.get("code")) in {"200", "00000"}

    async def place_order(
        self,
        *,
        symbol: str,
        side: str,
        position_side: str,
        quantity: float,
        leverage: int,
        take_profit_price: float | None = None,
        stop_loss_price: float | None = None,
        client_oid: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        trade_symbol = self._trade_symbol(symbol)
        side = side.upper()
        position_side = position_side.upper()
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if position_side not in {"LONG", "SHORT"}:
            raise ValueError("position_side must be LONG or SHORT")

        order_body: Dict[str, Any] = {
            "symbol": trade_symbol,
            "newClientOrderId": client_oid or f"aurum{int(time.time()*1000)}",
            "quantity": str(quantity),
            "side": side,
            "positionSide": position_side,
            "type": "MARKET",
        }
        if take_profit_price:
            order_body["tpTriggerPrice"] = str(take_profit_price)
            order_body["TpWorkingType"] = "MARK_PRICE"
        if stop_loss_price:
            order_body["slTriggerPrice"] = str(stop_loss_price)
            order_body["SlWorkingType"] = "MARK_PRICE"

        await self.set_leverage(symbol, leverage)
        data = await self._request("POST", "/capi/v3/order", body=order_body)
        if isinstance(data, dict) and (data.get("orderId") or data.get("order_id")):
            return data
        if isinstance(data, list) and data:
            return data[0]
        return None

    async def close_positions(self, symbol: str) -> Any:
        return await self._request("POST", "/capi/v3/closePositions", body={"symbol": self._trade_symbol(symbol)})

    async def place_position_tpsl(
        self,
        *,
        symbol: str,
        position_side: str,
        size: float,
        take_profit_price: float | None = None,
        stop_loss_price: float | None = None,
    ) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        if take_profit_price:
            results["tp"] = await self._request(
                "POST",
                "/capi/v2/order/placeTpSlOrder",
                body={
                    "symbol": symbol,
                    "clientOrderId": f"tp-{int(time.time()*1000)}",
                    "planType": "profit_plan",
                    "triggerPrice": str(take_profit_price),
                    "executePrice": "0",
                    "size": str(size),
                    "positionSide": position_side,
                    "marginMode": config.WEEX_MARGIN_MODE,
                },
            )
        if stop_loss_price:
            results["sl"] = await self._request(
                "POST",
                "/capi/v2/order/placeTpSlOrder",
                body={
                    "symbol": symbol,
                    "clientOrderId": f"sl-{int(time.time()*1000)}",
                    "planType": "loss_plan",
                    "triggerPrice": str(stop_loss_price),
                    "executePrice": "0",
                    "size": str(size),
                    "positionSide": position_side,
                    "marginMode": config.WEEX_MARGIN_MODE,
                },
            )
        return results

    async def get_current_orders(self, symbol: str) -> Any:
        return await self._request("GET", "/capi/v3/openOrders", query={"symbol": self._trade_symbol(symbol)})

    async def get_current_plan_orders(self, symbol: str) -> Any:
        return await self._request("GET", "/capi/v2/order/currentPlan", query={"symbol": self._market_symbol(symbol)})


async def _smoke_test():
    client = WEEXContractClient()
    await client.initialize()
    try:
        print(await client.ping())
        print(await client.get_contract_info(config.EXECUTION_SYMBOL))
        print(await client.get_account_assets())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(_smoke_test())
