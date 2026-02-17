"""AURUM FastAPI主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, users, strategies, trading, market

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="黄金量化交易系统API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["策略"])
app.include_router(trading.router, prefix="/api/v1", tags=["交易"])
app.include_router(market.router, prefix="/api/v1/market", tags=["市场数据"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
