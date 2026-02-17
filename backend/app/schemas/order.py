"""订单schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class OrderBase(BaseModel):
    symbol: str
    side: str = Field(..., pattern="^(buy|sell)$")
    order_type: str = Field(..., pattern="^(market|limit|stop)$")
    quantity: Decimal = Field(..., gt=0)
    leverage: Optional[Decimal] = None


class OrderCreate(OrderBase):
    price: Optional[Decimal] = None


class OrderResponse(OrderBase):
    id: int
    user_id: int
    strategy_id: Optional[int] = None
    order_id: str
    price: Optional[Decimal] = None
    filled_quantity: Decimal
    status: str
    fee: Decimal
    pnl: Optional[Decimal] = None
    created_at: datetime
    filled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    total: int
    items: list[OrderResponse]
