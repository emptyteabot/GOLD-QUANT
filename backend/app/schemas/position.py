"""持仓schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PositionResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: Decimal
    avg_entry_price: Decimal
    current_price: Optional[Decimal] = None
    leverage: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_ratio: Optional[float] = None
    stop_loss_price: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None
    opened_at: datetime

    class Config:
        from_attributes = True


class PositionListResponse(BaseModel):
    total: int
    items: list[PositionResponse]


class PositionClose(BaseModel):
    quantity: Optional[Decimal] = None
    order_type: str = "market"
