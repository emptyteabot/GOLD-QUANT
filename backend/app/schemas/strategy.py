"""策略schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class StrategyBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    symbol: str = "XAU-USDT-SWAP"
    timeframe: str = "15m"
    config: Dict[str, Any]


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class StrategyResponse(StrategyBase):
    id: int
    user_id: int
    status: str
    max_leverage: float
    max_position_ratio: float
    stop_loss_ratio: float
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    total: int
    items: list[StrategyResponse]
