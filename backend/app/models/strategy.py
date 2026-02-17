"""策略模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, func, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    config = Column(JSONB, nullable=False)  # 策略配置
    status = Column(String(20), default="stopped", index=True)  # running, stopped, paused
    symbol = Column(String(20), default="XAU-USDT-SWAP", index=True)
    timeframe = Column(String(10), default="15m")
    max_leverage = Column(Numeric(5, 2), default=10.00)
    max_position_ratio = Column(Numeric(5, 4), default=0.80)
    stop_loss_ratio = Column(Numeric(5, 4), default=0.015)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    stopped_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint('max_leverage >= 1 AND max_leverage <= 20', name='check_leverage'),
        CheckConstraint('max_position_ratio > 0 AND max_position_ratio <= 1', name='check_position_ratio'),
    )
