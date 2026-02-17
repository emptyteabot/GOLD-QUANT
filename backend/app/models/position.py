"""持仓模型"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, func, ForeignKey, UniqueConstraint
from app.database import Base


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # long, short
    quantity = Column(Numeric(20, 8), nullable=False)
    avg_entry_price = Column(Numeric(20, 8), nullable=False)
    current_price = Column(Numeric(20, 8))
    leverage = Column(Numeric(5, 2), nullable=False)
    margin = Column(Numeric(20, 8), nullable=False)
    unrealized_pnl = Column(Numeric(20, 8), default=0)
    stop_loss_price = Column(Numeric(20, 8))
    take_profit_price = Column(Numeric(20, 8))
    status = Column(String(20), default="open", index=True)  # open, closed
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True))
