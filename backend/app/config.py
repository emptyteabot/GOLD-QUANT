"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "AURUM API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/aurum_db"
    TIMESCALE_URL: str = "postgresql://postgres:password@localhost:5432/aurum_timeseries"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # CORS配置
    CORS_ORIGINS: list = ["*"]

    # API密钥加密
    ENCRYPTION_KEY: str = "your-encryption-key-32-bytes-long"

    # 限流配置
    RATE_LIMIT_PER_MINUTE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
