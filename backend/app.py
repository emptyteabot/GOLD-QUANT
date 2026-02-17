"""
Gold Advisor Pro™ v3.0 — FastAPI Backend
提供 REST API，供 Next.js 前端调用
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.WARNING)

# ── 导入策略引擎 ──
import gold_config as cfg
from ashare_provider import AShareGoldProvider
from gold_strategy_engine import (
    GoldStrategyEngine, TechnicalIndicators, RegimeDetector,
    CandlestickPatterns, MacroSignalAnalyzer,
)

# ── FastAPI App ──
app = FastAPI(
    title="Gold Advisor Pro API",
    version="3.0.0",
    description="A股黄金日内智能交易策略 API",
)

# 配置CORS - 支持本地开发和Railway部署
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.railway.app",  # Railway前端域名
    "https://*.vercel.app",   # Vercel部署
]

# 从环境变量读取额外的允许域名
import os
extra_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
ALLOWED_ORIGINS.extend([o.strip() for o in extra_origins if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if os.getenv("ENVIRONMENT") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全局实例 ──
provider = AShareGoldProvider()
engine = GoldStrategyEngine()
ti = TechnicalIndicators()


# ══════════════════════════════════════════════
#  Pydantic Models
# ══════════════════════════════════════════════
class QuoteItem(BaseModel):
    code: str
    name: str
    price: float
    change_pct: float
    change_amt: float = 0
    volume: float = 0
    amount: float = 0
    open: float = 0
    high: float = 0
    low: float = 0
    prev_close: float = 0
    turnover_rate: float = 0
    amplitude: float = 0
    t0: bool = False
    type: str = ""


class SignalItem(BaseModel):
    code: str
    name: str
    direction: str
    score: float
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    reason: str
    urgency: str
    regime: str
    regime_desc: str
    is_t0: bool
    macro_bias: float
    patterns: List[Dict[str, Any]]
    strategies: Dict[str, Any]


class KlineBar(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MacroData(BaseModel):
    bias: float
    confidence: float
    summary: str
    factors: Dict[str, Any]


# ══════════════════════════════════════════════
#  API Routes
# ══════════════════════════════════════════════

@app.get("/")
def root():
    return {
        "name": cfg.PRODUCT_NAME,
        "version": cfg.PRODUCT_VERSION,
        "status": "running",
        "market": provider.get_market_status(),
        "time": datetime.now().isoformat(),
    }


@app.get("/health")
def health_check():
    """健康检查端点 - 用于Railway/Docker监控"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "backend",
    }


@app.get("/api/ping")
def ping():
    """简单的连通性测试"""
    return {"message": "pong", "timestamp": datetime.now().isoformat()}


@app.get("/api/instruments")
def get_instruments():
    """获取所有支持的标的"""
    result = []
    for code, info in cfg.ALL_INSTRUMENTS.items():
        result.append({
            "code": code,
            "name": info["name"],
            "type": info.get("type", ""),
            "market": info.get("market", ""),
            "t0": info.get("t0", False),
            "desc": info.get("desc", ""),
        })
    return result


@app.get("/api/market-status")
def get_market_status():
    """市场状态"""
    return {
        "status": provider.get_market_status(),
        "icon": provider.get_market_status_icon(),
        "is_trading": provider.is_trading_time(),
        "time": datetime.now().strftime("%H:%M:%S"),
    }


@app.get("/api/quotes", response_model=List[QuoteItem])
def get_quotes(codes: str = Query(default=",".join(cfg.DEFAULT_WATCHLIST))):
    """批量获取实时行情"""
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    raw = provider.get_batch_realtime(code_list)
    result = []
    for code in code_list:
        q = raw.get(code)
        if not q:
            continue
        info = cfg.ALL_INSTRUMENTS.get(code, {})
        result.append(QuoteItem(
            code=code,
            name=q.get("name", info.get("name", "")),
            price=q.get("price", 0),
            change_pct=q.get("change_pct", 0),
            change_amt=q.get("change_amt", 0),
            volume=q.get("volume", 0),
            amount=q.get("amount", 0),
            open=q.get("open", 0),
            high=q.get("high", 0),
            low=q.get("low", 0),
            prev_close=q.get("prev_close", 0),
            turnover_rate=q.get("turnover_rate", 0),
            amplitude=q.get("amplitude", 0),
            t0=info.get("t0", False),
            type=info.get("type", ""),
        ))
    return result


@app.get("/api/klines", response_model=List[KlineBar])
def get_klines(
    code: str = "518880",
    period: str = "5",
    days: int = 5,
):
    """获取K线数据"""
    info = cfg.ALL_INSTRUMENTS.get(code, {})
    market = info.get("market", "SH")

    if period == "daily":
        df = provider.get_daily_klines(code, days=days)
    else:
        df = provider.get_intraday_klines(code, period=period, days=days, market=market)

    if df is None or df.empty:
        return []

    result = []
    for _, row in df.iterrows():
        result.append(KlineBar(
            time=str(row.get("timestamp", "")),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row.get("volume", 0)),
        ))
    return result


@app.get("/api/signals", response_model=List[SignalItem])
def get_signals(codes: str = Query(default=",".join(cfg.DEFAULT_WATCHLIST))):
    """获取交易信号"""
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    quotes = provider.get_batch_realtime(code_list)
    result = []

    for code in code_list:
        info = cfg.ALL_INSTRUMENTS.get(code, {})
        name = info.get("name", code)
        market = info.get("market", "SH")
        is_t0 = info.get("t0", False)

        df = provider.get_intraday_klines(code, period="5", days=5, market=market)
        if df is None or df.empty:
            df = provider.get_daily_klines(code, days=60)

        q = quotes.get(code, {})
        price = q.get("price", 0)
        if price <= 0 and df is not None and not df.empty:
            price = float(df["close"].iloc[-1])

        if price <= 0 or df is None or df.empty:
            continue

        sig = engine.analyze(code, name, df, price, is_t0)
        result.append(SignalItem(
            code=sig.code,
            name=sig.name,
            direction=sig.direction,
            score=sig.score,
            confidence=sig.confidence,
            entry_price=sig.entry_price,
            stop_loss=sig.stop_loss,
            take_profit=sig.take_profit,
            risk_reward=sig.risk_reward,
            reason=sig.reason,
            urgency=sig.urgency,
            regime=sig.regime,
            regime_desc=sig.regime_desc,
            is_t0=sig.is_t0,
            macro_bias=sig.macro_bias,
            patterns=sig.patterns,
            strategies=sig.strategies,
        ))

    result.sort(key=lambda s: abs(s.score), reverse=True)
    return result


@app.get("/api/macro", response_model=MacroData)
def get_macro():
    """宏观分析"""
    data = engine.macro_analyzer.get_macro_bias()
    return MacroData(**data)


@app.get("/api/regime")
def get_regime(code: str = "518880"):
    """行情识别"""
    info = cfg.ALL_INSTRUMENTS.get(code, {})
    market = info.get("market", "SH")
    df = provider.get_intraday_klines(code, period="5", days=5, market=market)
    if df is None or df.empty:
        return {"regime": "UNKNOWN", "description": "数据不足"}
    result = engine.regime_detector.detect(df)
    return result


# ══════════════════════════════════════════════
#  启动
# ══════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn

    # Railway会提供PORT环境变量
    port = int(os.getenv("PORT", 8000))

    print(f"\n  🥇 {cfg.PRODUCT_NAME} API Server")
    print(f"  http://0.0.0.0:{port}/docs\n")

    uvicorn.run(app, host="0.0.0.0", port=port)



