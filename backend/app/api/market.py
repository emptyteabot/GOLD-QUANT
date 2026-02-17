"""市场数据API"""
from fastapi import APIRouter, Query
from typing import Optional
from app.schemas.response import APIResponse

router = APIRouter()


@router.get("/klines", response_model=APIResponse)
def get_klines(
    symbol: str = "XAU-USDT-SWAP",
    timeframe: str = "15m",
    limit: int = Query(100, ge=1, le=1000)
):
    """获取K线数据"""
    # 这里应该从TimescaleDB或交易所API获取K线数据
    # 简化实现，返回模拟数据
    return APIResponse(
        code=200,
        data={
            "symbol": symbol,
            "timeframe": timeframe,
            "items": []
        }
    )


@router.get("/ticker", response_model=APIResponse)
def get_ticker(symbol: str = "XAU-USDT-SWAP"):
    """获取实时价格"""
    # 这里应该从Redis缓存或交易所API获取实时价格
    return APIResponse(
        code=200,
        data={
            "symbol": symbol,
            "last": 4819.20,
            "bid": 4819.10,
            "ask": 4819.30,
            "volume_24h": 1234567.89,
            "change_24h": 1.35
        }
    )


@router.get("/macro", response_model=APIResponse)
def get_macro(indicators: Optional[str] = "dxy,vix,us10y"):
    """获取宏观数据"""
    # 这里应该从数据源获取宏观数据
    return APIResponse(
        code=200,
        data={
            "dxy": {"value": 103.45, "change": -0.25},
            "vix": {"value": 18.32, "change": 1.15},
            "us10y": {"value": 4.25, "change": -0.05}
        }
    )
