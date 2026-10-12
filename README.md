# AURUM · Gold Quant Research Workspace

A research workspace for gold-market data, technical signals, model ensembles, backtesting, risk controls and monitoring. The repository preserves several iterations of the system in one place.

## Review path

1. `AURUM项目全景.md` — system map.
2. `complete_multi_agent.py` and `ultimate_quant_orchestrator.py` — orchestration experiments.
3. `backtest_engine.py` and `backtest_*.py` — backtesting paths.
4. `risk_manager.py` and `risk_manager_enhanced_v2.py` — risk controls.
5. `backend/` and `frontend/` — service and dashboard implementations.
6. `tests/` and `test_risk_manager_v2.py` — checks.

## Main components

- Market data adapters for OKX, Tushare and Alpha Vantage.
- Technical, macro and machine-learning signal experiments.
- Multi-Agent decision aggregation and reasoning gates.
- Backtesting with fees, slippage and walk-forward variants.
- Position sizing, stop-loss, take-profit and circuit-breaker rules.
- Streamlit and web dashboard prototypes.
- Feishu notification and service-monitoring utilities.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Choose an entry point from `QUICK_START.md`, `QUICK_REFERENCE.md` or the specific strategy document you want to reproduce.

## Evidence and limits

Backtest images and reported metrics in this workspace belong to specific data windows and configurations. They are research outputs rather than verified live performance. Reproduce a result from its script and configuration before comparing strategies or considering deployment.

## Credential handling

Keep exchange credentials and webhook URLs in local files covered by `.gitignore`. The tracked `env.trading` file is a placeholder template only.
