"""订单模型"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, func, ForeignKey
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    order_id = Column(String(50), unique=True, nullable=False, index=True)  # 交易所订单ID
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), nullable=False)  # market, limit, stop
    price = Column(Numeric(20, 8))
    quantity = Column(Numeric(20, 8), nullable=False)
    filled_quantity = Column(Numeric(20, 8), default=0)
    status = Column(String(20), default="pending", index=True)  # pending, filled, cancelled, failed
    leverage = Column(Numeric(5, 2))
    fee = Column(Numeric(20, 8), default=0)
    pnl = Column(Numeric(20, 8))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    filled_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
