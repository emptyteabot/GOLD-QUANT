from __future__ import annotations

import argparse
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import config
from agent_16_scalping_system import Agent16ScalpingSystem
from context_aggregator import AggregatedContext, MarketContextAggregator, fallback_technical
from feishu_notifier import send_feishu
from reasoning_gate import run_reasoning_gate
from risk_manager import RiskManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TIMEFRAME_WEIGHTS = {
    "1m": 0.20,
    "3m": 0.30,
    "5m": 0.50,
}


def summarize_committee(result: Dict) -> Dict:
    ranked = sorted(
        result.get("decisions", []),
        key=lambda d: abs(float(d.signal)) * float(d.confidence),
        reverse=True,
    )
    return {
        "action": result.get("action"),
        "signal": float(result.get("signal", 0)),
        "confidence": float(result.get("confidence", 0)),
        "risk_reward": float(result.get("risk_reward", 0)),
        "long_count": int(result.get("long_count", 0)),
        "short_count": int(result.get("short_count", 0)),
        "neutral_count": int(result.get("neutral_count", 0)),
        "reason_summary": result.get("reason_summary", ""),
        "decisions": [
            {
                "agent_name": d.agent_name,
                "signal": float(d.signal),
                "confidence": float(d.confidence),
                "reason": str(d.reason),
            }
            for d in ranked[:6]
        ],
    }


def aggregate_committees(committees: Dict[str, Dict]) -> Dict:
    signal = sum(TIMEFRAME_WEIGHTS[tf] * float(data["signal"]) for tf, data in committees.items())
    long_vote = sum(TIMEFRAME_WEIGHTS[tf] * (float(data["long_count"]) / 16.0) for tf, data in committees.items())
    short_vote = sum(TIMEFRAME_WEIGHTS[tf] * (float(data["short_count"]) / 16.0) for tf, data in committees.items())
    neutral_vote = sum(TIMEFRAME_WEIGHTS[tf] * (float(data["neutral_count"]) / 16.0) for tf, data in committees.items())
    consensus = max(0.0, abs(long_vote - short_vote))
    dominant_side = "buy" if signal > 0 else "sell" if signal < 0 else "flat"
    return {
        "signal": signal,
        "consensus": consensus,
        "long_vote": long_vote,
        "short_vote": short_vote,
        "neutral_vote": neutral_vote,
        "dominant_side": dominant_side,
    }


class OKXWeexXautService:
    def __init__(self):
        self.context = MarketContextAggregator()
        self.risk_manager = RiskManager()
        self.llm_agents = Agent16ScalpingSystem()

    async def initialize(self):
        await self.context.initialize()

    async def close(self):
        await self.context.close()

    def _risk_state_path(self) -> Path:
        path = Path(config.WEEX_DAILY_RISK_STATE_PATH)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _update_daily_risk_state(self, current_equity: float) -> Dict:
        today = datetime.now().date().isoformat()
        path = self._risk_state_path()
        state = {}
        if path.exists():
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                state = {}

        if state.get("date") != today:
            state = {
                "date": today,
                "start_equity": current_equity,
                "peak_equity": current_equity,
            }

        state["peak_equity"] = max(float(state.get("peak_equity", current_equity)), current_equity)
        state["last_equity"] = current_equity
        peak = max(float(state.get("peak_equity", current_equity)), 1e-9)
        start = max(float(state.get("start_equity", current_equity)), 1e-9)
        state["daily_drawdown_from_peak_pct"] = max(0.0, (peak - current_equity) / peak)
        state["daily_pnl_pct"] = (current_equity - start) / start
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return state

    def _run_committees(self, ctx: AggregatedContext) -> Dict[str, Dict]:
        outputs: Dict[str, Dict] = {}
        price = ctx.ticker_24h["last"]
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.llm_agents.analyze, df, price): timeframe
                for timeframe, df in ctx.timeframes.items()
            }
            for future in as_completed(futures):
                timeframe = futures[future]
                outputs[timeframe] = summarize_committee(future.result())
        return outputs

    async def gather_market_state(self) -> Dict:
        ctx = await self.context.collect(config.EXECUTION_SYMBOL)
        committees = self._run_committees(ctx)
        combined_committee = aggregate_committees(committees)
        tech_analysis = fallback_technical(ctx.timeframes["5m"], ctx.ticker_24h["last"])
        return {
            "context": ctx,
            "committees": committees,
            "combined_committee": combined_committee,
            "tech_analysis": tech_analysis,
        }

    def build_trade_decision(self, market_state: Dict) -> Dict:
        ctx: AggregatedContext = market_state["context"]
        committees = market_state["committees"]
        combined = market_state["combined_committee"]
        tech = market_state["tech_analysis"]
        micro = ctx.micro_features
        price = float(ctx.ticker_24h["last"])
        spread_pct = float(micro["spread_pct"])
        robust_z = abs(float(micro["robust_zscore"]))
        order_book_obi = float(ctx.order_book["obi"])
        obi_proxy = float(micro["obi_proxy"])
        trend_bias = float(micro["trend_bias"])

        fair_signal = 0.0
        if spread_pct <= -config.WEEX_MICRO_MIN_SPREAD_PCT:
            fair_signal = 1.0
        elif spread_pct >= config.WEEX_MICRO_MIN_SPREAD_PCT:
            fair_signal = -1.0

        fair_strength = min(
            1.0,
            max(
                abs(spread_pct) / max(config.WEEX_MICRO_MIN_SPREAD_PCT, 1e-9),
                robust_z / max(config.WEEX_MIN_FAIR_VALUE_Z, 1e-9),
            ),
        )
        tech_signal = float(tech.get("signal", 0)) * float(tech.get("signal_strength", 0))
        micro_signal = (order_book_obi + obi_proxy) / 2.0
        combined_signal = (
            0.45 * float(combined["signal"])
            + 0.30 * fair_signal * fair_strength
            + 0.15 * tech_signal
            + 0.10 * micro_signal
        )
        combined_confidence = min(
            1.0,
            0.40 * float(combined["consensus"])
            + 0.25 * fair_strength
            + 0.20 * abs(tech_signal)
            + 0.15 * min((abs(order_book_obi) + abs(obi_proxy)) / 2.0, 1.0),
        )
        side = "buy" if combined_signal > 0 else "sell" if combined_signal < 0 else "flat"

        leverage = min(config.WEEX_MICRO_LEVERAGE, config.WEEX_HARD_MAX_LEVERAGE, config.MAX_LEVERAGE)
        position_size_pct = min(config.WEEX_MAX_POSITION_PCT, max(0.0, config.WEEX_MAX_POSITION_PCT * combined_confidence))
        tp_pct = config.WEEX_MICRO_TP_PCT
        sl_pct = config.WEEX_MICRO_SL_PCT

        if side == "buy":
            take_profit = price * (1 + tp_pct)
            stop_loss = price * (1 - sl_pct)
        elif side == "sell":
            take_profit = price * (1 - tp_pct)
            stop_loss = price * (1 + sl_pct)
        else:
            take_profit = price
            stop_loss = price

        risk_reward = abs(take_profit - price) / max(abs(price - stop_loss), 1e-9) if side != "flat" else 0.0
        higher_tf_bias = "buy" if float(committees["5m"]["signal"]) > 0 else "sell" if float(committees["5m"]["signal"]) < 0 else "flat"

        reasons: List[str] = [
            f"committee_signal={combined['signal']:+.2f}",
            f"committee_consensus={combined['consensus']:.2f}",
            f"spread_pct={spread_pct:+.4%}",
            f"robust_z={micro['robust_zscore']:+.2f}",
            f"order_book_obi={order_book_obi:+.2f}",
            f"obi_proxy={obi_proxy:+.2f}",
            f"tech={tech_signal:+.2f}",
        ]
        risk_flags: List[str] = []
        should_trade = (
            side in {"buy", "sell"}
            and fair_signal != 0
            and fair_strength >= 1.0
            and abs(combined_signal) >= config.WEEX_MIN_ABS_SIGNAL
            and combined_confidence >= config.WEEX_LIVE_MIN_CONFIDENCE
            and risk_reward >= config.WEEX_MIN_RISK_REWARD
        )

        trend_conflict = (side == "buy" and trend_bias < 0 and higher_tf_bias == "sell") or (
            side == "sell" and trend_bias > 0 and higher_tf_bias == "buy"
        )
        if fair_signal == 0:
            should_trade = False
            risk_flags.append("fair_value_not_extreme")
        if trend_conflict and fair_strength < 1.5:
            should_trade = False
            risk_flags.append("higher_timeframe_trend_conflict")
        if side == "buy" and micro_signal < -0.15:
            should_trade = False
            risk_flags.append("microstructure_bearish")
        if side == "sell" and micro_signal > 0.15:
            should_trade = False
            risk_flags.append("microstructure_bullish")
        if combined["consensus"] < 0.20:
            should_trade = False
            risk_flags.append("committee_consensus_too_low")
        if combined_confidence < config.WEEX_LIVE_MIN_CONFIDENCE:
            risk_flags.append("confidence_below_live_threshold")
        if risk_reward < config.WEEX_MIN_RISK_REWARD:
            risk_flags.append("risk_reward_too_low")

        return {
            "should_trade": should_trade,
            "side": side,
            "signal": combined_signal,
            "confidence": combined_confidence,
            "risk_reward": risk_reward,
            "entry_price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "leverage": leverage,
            "position_size_pct": position_size_pct,
            "risk_flags": risk_flags,
            "reason": ", ".join(reasons + risk_flags),
        }

    async def apply_final_reasoning_gate(self, market_state: Dict, preliminary: Dict) -> Dict:
        if not config.ENABLE_FINAL_REASONER:
            return preliminary

        ctx: AggregatedContext = market_state["context"]
        system_prompt = (
            "You are the final live trading risk gate for a WEEX-only XAUT system. "
            "Optimize for survival and consistent edge, not excitement. "
            "Reject trades when account state, existing positions, protection status, "
            "microstructure, or committee alignment are weak. "
            "Return only JSON with keys final_action, should_trade, side, confidence, "
            "leverage, position_size_pct, take_profit_pct, stop_loss_pct, reason, risk_flags. "
            "final_action must be one of HOLD, REDUCE, CLOSE, ADD, OBSERVE."
        )
        user_payload = {
            "account": {
                "equity": float(ctx.account.get("equity", 0)),
                "available": float(ctx.account.get("available", 0)),
                "unrealized_pnl": float(ctx.account.get("unrealizePnl", 0)),
            },
            "position": {
                "side": (ctx.position or {}).get("side"),
                "leverage": float((ctx.position or {}).get("leverage", 0) or 0),
                "size": float((ctx.position or {}).get("size", 0) or 0),
                "liquidate_price": float((ctx.position or {}).get("liquidatePrice", 0) or 0),
            },
            "plans": [
                {
                    "type": p.get("type"),
                    "status": p.get("status"),
                    "triggerPrice": p.get("triggerPrice"),
                }
                for p in ctx.plans[:4]
            ],
            "ticker_24h": {
                "last": ctx.ticker_24h["last"],
                "mark_price": ctx.ticker_24h["mark_price"],
                "index_price": ctx.ticker_24h["index_price"],
                "change_24h_pct": ctx.ticker_24h["change_24h_pct"],
                "high_24h": ctx.ticker_24h["high_24h"],
                "low_24h": ctx.ticker_24h["low_24h"],
            },
            "micro_features": ctx.micro_features,
            "committee_1m": market_state["committees"]["1m"],
            "committee_3m": market_state["committees"]["3m"],
            "committee_5m": market_state["committees"]["5m"],
            "committee_combined": market_state["combined_committee"],
            "tech_5m": market_state["tech_analysis"],
            "macro": ctx.macro,
            "news": ctx.news[:3],
            "preliminary": {
                "should_trade": preliminary["should_trade"],
                "side": preliminary["side"],
                "signal": preliminary["signal"],
                "confidence": preliminary["confidence"],
                "risk_reward": preliminary["risk_reward"],
                "leverage": preliminary["leverage"],
                "position_size_pct": preliminary["position_size_pct"],
                "risk_flags": preliminary["risk_flags"],
            },
        }
        result = await asyncio.to_thread(
            run_reasoning_gate,
            system_prompt=system_prompt,
            user_prompt=json.dumps(user_payload, ensure_ascii=False),
            timeout=config.FINAL_REASONER_TIMEOUT_SEC,
        )
        if not result or not any(k in result for k in ("should_trade", "side", "confidence", "final_action")):
            return preliminary

        side = str(result.get("side", preliminary["side"])).lower()
        if side not in {"buy", "sell", "flat"}:
            side = preliminary["side"]
        confidence = max(0.0, min(1.0, float(result.get("confidence", preliminary["confidence"]))))
        leverage = int(result.get("leverage", preliminary["leverage"]))
        leverage = max(config.MIN_LEVERAGE, min(leverage, config.WEEX_HARD_MAX_LEVERAGE, config.MAX_LEVERAGE))
        position_size_pct = float(result.get("position_size_pct", preliminary["position_size_pct"]))
        position_size_pct = max(0.0, min(position_size_pct, config.WEEX_MAX_POSITION_PCT))
        max_tp_pct = max(config.WEEX_MICRO_TP_PCT * 4, 0.005)
        max_sl_pct = max(config.WEEX_MICRO_SL_PCT * 4, 0.005)
        tp_pct = min(max(0.0005, float(result.get("take_profit_pct", config.WEEX_MICRO_TP_PCT))), max_tp_pct)
        sl_pct = min(max(0.0005, float(result.get("stop_loss_pct", config.WEEX_MICRO_SL_PCT))), max_sl_pct)
        price = preliminary["entry_price"]
        if side == "buy":
            take_profit = price * (1 + tp_pct)
            stop_loss = price * (1 - sl_pct)
        elif side == "sell":
            take_profit = price * (1 - tp_pct)
            stop_loss = price * (1 + sl_pct)
        else:
            take_profit = price
            stop_loss = price
        rr = abs(take_profit - price) / max(abs(price - stop_loss), 1e-9) if side != "flat" else 0.0
        gate_meta = result.get("_meta", {}) if isinstance(result, dict) else {}
        gate_provider = gate_meta.get("provider", "unknown")
        risk_flags = preliminary.get("risk_flags", []) + list(result.get("risk_flags", []) or [])

        return {
            **preliminary,
            "final_action": str(result.get("final_action", "OBSERVE")).upper(),
            "should_trade": bool(result.get("should_trade", preliminary["should_trade"])) and side in {"buy", "sell"},
            "side": side if side != "flat" else preliminary["side"],
            "confidence": confidence,
            "leverage": leverage,
            "position_size_pct": position_size_pct,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "risk_reward": rr,
            "risk_flags": risk_flags,
            "gate_meta": gate_meta,
            "reason": f"{preliminary['reason']}, gate[{gate_provider}]={result.get('reason', result.get('thesis', 'no_reason'))}",
        }

    def evaluate_hard_risk_guards(self, market_state: Dict, decision: Dict) -> Dict:
        ctx: AggregatedContext = market_state["context"]
        current_equity = float(ctx.account.get("equity", 0))
        available = float(ctx.account.get("available", 0))
        daily_state = self._update_daily_risk_state(current_equity)
        flags: List[str] = []
        block_reasons: List[str] = []

        if available <= 0:
            flags.append("available_balance_zero")
            block_reasons.append("available_balance_zero")
        elif available < config.WEEX_MIN_AVAILABLE_USDT:
            flags.append("available_below_min_trade_buffer")
            block_reasons.append("available_below_min_trade_buffer")

        if float(daily_state.get("daily_drawdown_from_peak_pct", 0)) >= config.MAX_DAILY_LOSS:
            flags.append("max_daily_loss_hit")
            block_reasons.append("max_daily_loss_hit")

        position = ctx.position or {}
        protective_plans = [
            p for p in ctx.plans
            if p.get("status") == "UNTRIGGERED" and str(p.get("type", "")).startswith("CLOSE_") and p.get("triggerPrice")
        ]
        liquidation_buffer_pct = None
        if position:
            flags.append("existing_position_on_weex")
            if config.WEEX_BLOCK_ON_EXISTING_POSITION:
                block_reasons.append("existing_position_on_weex")

            leverage = float(position.get("leverage", 0) or 0)
            if leverage > config.WEEX_HARD_MAX_LEVERAGE:
                flags.append("existing_position_above_hard_leverage_cap")
                block_reasons.append("existing_position_above_hard_leverage_cap")

            liquidate_price = float(position.get("liquidatePrice", 0) or 0)
            mark_price = float(ctx.ticker_24h["mark_price"])
            if liquidate_price > 0:
                liquidation_buffer_pct = abs(mark_price - liquidate_price) / max(mark_price, 1e-9)
                if liquidation_buffer_pct < config.WEEX_MIN_LIQUIDATION_BUFFER_PCT:
                    flags.append("liquidation_buffer_too_small")
                    block_reasons.append("liquidation_buffer_too_small")

            if not protective_plans:
                flags.append("position_has_no_protective_plan")
                block_reasons.append("position_has_no_protective_plan")
            elif config.WEEX_REQUIRE_TPSL_FOR_EXISTING_POSITION and len(protective_plans) < 2:
                flags.append("position_missing_full_tpsl")
                block_reasons.append("position_missing_full_tpsl")

        if int(decision.get("leverage", 0) or 0) > config.WEEX_HARD_MAX_LEVERAGE:
            flags.append("decision_leverage_above_hard_cap")
            block_reasons.append("decision_leverage_above_hard_cap")

        return {
            "blocked": bool(block_reasons),
            "flags": sorted(set(flags)),
            "block_reasons": list(dict.fromkeys(block_reasons)),
            "protective_plan_count": len(protective_plans),
            "liquidation_buffer_pct": liquidation_buffer_pct,
            "daily_state": daily_state,
        }

    async def maybe_execute(self, market_state: Dict, decision: Dict, risk_checks: Dict) -> Dict:
        ctx: AggregatedContext = market_state["context"]
        if risk_checks["blocked"]:
            return {
                "status": "blocked",
                "reason": ", ".join(risk_checks["block_reasons"]),
                "risk_checks": risk_checks,
                "position": ctx.position,
                "plans": ctx.plans,
            }

        if not config.WEEX_AUTOTRADE_ENABLED:
            return {"status": "dry_run", "reason": "WEEX_AUTOTRADE_ENABLED=0", "risk_checks": risk_checks, "decision": decision}
        if not decision["should_trade"]:
            return {"status": "no_trade", "reason": "signal gate not passed", "risk_checks": risk_checks, "decision": decision}

        account = {
            "available": float(ctx.account.get("available", 0)),
            "total_equity": float(ctx.account.get("equity", 0)),
        }
        position_info = self.risk_manager.calculate_scalping_position_size(
            account=account,
            price=decision["entry_price"],
            leverage=decision["leverage"],
            stop_loss_price=decision["stop_loss"],
            take_profit_price=decision["take_profit"],
            position_size_pct=decision["position_size_pct"],
            confidence=decision["confidence"],
        )
        if not position_info:
            return {"status": "blocked", "reason": "position sizing failed", "risk_checks": risk_checks, "decision": decision}

        if config.WEEX_FIXED_ORDER_QTY > 0:
            position_info["oz_size"] = config.WEEX_FIXED_ORDER_QTY

        order = await self.context.exec_client.place_order(
            symbol=config.EXECUTION_SYMBOL,
            side="BUY" if decision["side"] == "buy" else "SELL",
            position_side="LONG" if decision["side"] == "buy" else "SHORT",
            quantity=position_info["oz_size"],
            leverage=decision["leverage"],
            take_profit_price=decision["take_profit"],
            stop_loss_price=decision["stop_loss"],
        )
        if not order:
            return {"status": "failed", "reason": "WEEX place_order failed", "risk_checks": risk_checks, "decision": decision}

        position_side = "long" if decision["side"] == "buy" else "short"
        tpsl = await self.context.exec_client.place_position_tpsl(
            symbol=config.EXECUTION_SYMBOL,
            position_side=position_side,
            size=position_info["size"],
            take_profit_price=decision["take_profit"],
            stop_loss_price=decision["stop_loss"],
        )
        plans_after = await self.context.exec_client.get_current_plan_orders(config.EXECUTION_SYMBOL)
        protective_after = [
            p for p in (plans_after if isinstance(plans_after, list) else [])
            if p.get("status") == "UNTRIGGERED" and str(p.get("type", "")).startswith("CLOSE_") and p.get("triggerPrice")
        ]
        required_plan_count = 2 if config.WEEX_REQUIRE_TPSL_FOR_EXISTING_POSITION else 1
        if len(protective_after) < required_plan_count:
            emergency_close = await self.context.exec_client.close_positions(config.EXECUTION_SYMBOL)
            return {
                "status": "failed",
                "reason": "protective_plan_verification_failed",
                "decision": decision,
                "risk_checks": risk_checks,
                "order": order,
                "tpsl": tpsl,
                "plans_after": plans_after,
                "emergency_close": emergency_close,
            }

        return {
            "status": "submitted",
            "order": order,
            "tpsl": tpsl,
            "plans_after": plans_after,
            "risk_checks": risk_checks,
            "decision": decision,
            "position_info": position_info,
        }

    async def run_once(self) -> Dict:
        market_state = await self.gather_market_state()
        preliminary = self.build_trade_decision(market_state)
        decision = await self.apply_final_reasoning_gate(market_state, preliminary)
        risk_checks = self.evaluate_hard_risk_guards(market_state, decision)
        execution = await self.maybe_execute(market_state, decision, risk_checks)

        ctx: AggregatedContext = market_state["context"]
        summary = {
            "service": {
                "data_source": "WEEX_ONLY",
                "execution_exchange": "WEEX",
                "final_reasoner": config.FINAL_REASONER_PROVIDER,
            },
            "account": {
                "available": float(ctx.account.get("available", 0)),
                "equity": float(ctx.account.get("equity", 0)),
                "frozen": float(ctx.account.get("frozen", 0)),
                "unrealized_pnl": float(ctx.account.get("unrealizePnl", 0)),
                "total_equity": float(ctx.account.get("equity", 0)),
            },
            "position": ctx.position,
            "plans": ctx.plans,
            "market_state": {
                "timestamp": ctx.timestamp,
                "last": ctx.ticker_24h["last"],
                "mark_price": ctx.ticker_24h["mark_price"],
                "index_price": ctx.ticker_24h["index_price"],
                "change_24h_pct": ctx.ticker_24h["change_24h_pct"],
                "high_24h": ctx.ticker_24h["high_24h"],
                "low_24h": ctx.ticker_24h["low_24h"],
                "micro_features": ctx.micro_features,
                "order_book_obi": ctx.order_book["obi"],
                "top_news": ctx.news[:3],
            },
            "timeframes": {
                tf: {
                    "latest_close": float(df["close"].iloc[-1]),
                    "latest_high": float(df["high"].iloc[-1]),
                    "latest_low": float(df["low"].iloc[-1]),
                    "bars": len(df),
                }
                for tf, df in ctx.timeframes.items()
            },
            "committees": market_state["committees"],
            "combined_committee": market_state["combined_committee"],
            "tech_analysis": market_state["tech_analysis"],
            "preliminary_decision": preliminary,
            "decision": decision,
            "risk_checks": risk_checks,
            "execution": execution,
        }
        self.write_latest_state(summary)
        return summary

    @staticmethod
    def write_latest_state(summary: Dict) -> None:
        output_path = Path(__file__).resolve().parent / "_tmp" / "latest_state.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, ensure_ascii=False, default=str, indent=2), encoding="utf-8")


async def main():
    parser = argparse.ArgumentParser(description="WEEX-only XAUT live service with hard risk guards.")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop-seconds", type=int, default=300)
    args = parser.parse_args()

    service = OKXWeexXautService()
    await service.initialize()
    try:
        if args.once:
            summary = await service.run_once()
            print(json.dumps(summary, ensure_ascii=False, default=str, indent=2))
            status = summary["execution"]["status"]
            if status in {"submitted", "dry_run", "no_trade", "blocked", "failed"}:
                send_feishu(
                    json.dumps(summary, ensure_ascii=False, default=str, indent=2),
                    level="info" if status != "submitted" else "success",
                    title="AURUM WEEX 扫描",
                )
            return

        while True:
            summary = await service.run_once()
            print(json.dumps(summary, ensure_ascii=False, default=str))
            await asyncio.sleep(args.loop_seconds)
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
