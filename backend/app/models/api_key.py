"""API密钥模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, func, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)  # okx, binance, huobi
    api_key_encrypted = Column(Text, nullable=False)
    secret_key_encrypted = Column(Text, nullable=False)
    passphrase_encrypted = Column(Text)
    permissions = Column(JSONB, default={"trade": True, "read": True})
    status = Column(String(20), default="active", index=True)  # active, expired, revoked
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint('user_id', 'exchange', name='unique_user_exchange'),
    )
