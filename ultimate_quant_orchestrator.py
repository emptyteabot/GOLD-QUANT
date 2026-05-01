from __future__ import annotations

import argparse
import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Dict, List

import config
from agent_16_scalping_system import Agent16ScalpingSystem
from context_aggregator import AggregatedContext, MarketContextAggregator, fallback_technical
from rag_context import LocalKeywordRAG
from reasoning_gate import run_reasoning_gate

try:
    from complete_multi_agent import CompleteMultiAgentSystem
except Exception:
    CompleteMultiAgentSystem = None  # type: ignore[assignment]


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
                "reason": d.reason,
            }
            for d in ranked[:6]
        ],
    }


@dataclass
class OrchestratorResult:
    context: Dict
    rag_hits: Dict[str, List[Dict]]
    committees: Dict
    final_adjudication: Dict | None


class UltimateQuantOrchestrator:
    def __init__(self):
        self.context = MarketContextAggregator()
        self.rag = LocalKeywordRAG()
        self.scalping_committee = Agent16ScalpingSystem()
        self.secondary_committee = CompleteMultiAgentSystem() if CompleteMultiAgentSystem else None

    async def initialize(self):
        await self.context.initialize()

    async def close(self):
        await self.context.close()

    def _run_llm_committee(self, frames: Dict[str, object], price: float) -> Dict:
        outputs = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            fut_map = {
                executor.submit(self.scalping_committee.analyze, df, price): tf
                for tf, df in frames.items()
            }
            for future in as_completed(fut_map):
                tf = fut_map[future]
                outputs[tf] = summarize_committee(future.result())
        return outputs

    def _run_secondary_committee(self, ctx: AggregatedContext) -> Dict:
        if self.secondary_committee is None:
            return {"available": False, "reason": "complete_multi_agent unavailable in current environment"}
        df_5m = ctx.timeframes["5m"]
        price = ctx.ticker_24h["last"]
        tech = fallback_technical(df_5m, price)
        macro = ctx.macro
        decision = self.secondary_committee.make_decision(macro, tech, df_5m, price)
        return decision

    def _rag_queries(self, ctx: AggregatedContext) -> Dict[str, str]:
        position_side = (ctx.position or {}).get("side", "NONE")
        return {
            "micro": "XAUT micro arbitrage order book imbalance fair value spread zscore",
            "risk": f"XAUT {position_side} leverage liquidation risk stop loss reduce position",
            "ops": "OpenClaw orchestration agent runtime context aggregator dry run execution broker",
        }

    def _run_rag(self, queries: Dict[str, str]) -> Dict[str, List[Dict]]:
        out: Dict[str, List[Dict]] = {}
        for key, query in queries.items():
            out[key] = [asdict(hit) for hit in self.rag.search(query, top_k=6)]
        return out

    async def _final_gate(self, payload: Dict) -> Dict | None:
        if not config.ENABLE_FINAL_REASONER:
            return None
        system_prompt = (
            "You are the ultimate quant orchestrator final gate. "
            "You receive multi-timeframe committee outputs, a secondary committee, "
            "WEEX-only market context, local RAG findings, and live position state. "
            "Return ONLY JSON with keys final_action, urgency, confidence, thesis, "
            "risk_flags, execution_plan, should_trade. "
            "final_action must be one of HOLD, REDUCE, CLOSE, ADD, OBSERVE. "
            "Do not optimize for excitement; optimize for survival and edge quality."
        )
        return await asyncio.to_thread(
            run_reasoning_gate,
            system_prompt=system_prompt,
            user_prompt=json.dumps(payload, ensure_ascii=False),
            timeout=config.FINAL_REASONER_TIMEOUT_SEC,
        )

    async def run_once(self) -> OrchestratorResult:
        ctx = await self.context.collect(config.EXECUTION_SYMBOL)
        payload = ctx.to_payload()
        llm_committees = self._run_llm_committee(ctx.timeframes, ctx.ticker_24h["last"])
        secondary = self._run_secondary_committee(ctx)
        rag_queries = self._rag_queries(ctx)
        rag_hits = self._run_rag(rag_queries)
        final_payload = {
            "market_context": payload,
            "committees": {
                "llm_16_agents": llm_committees,
                "secondary_multi_agent": secondary,
            },
            "rag_hits": rag_hits,
        }
        final = await self._final_gate(final_payload)
        return OrchestratorResult(
            context=payload,
            rag_hits=rag_hits,
            committees=final_payload["committees"],
            final_adjudication=final,
        )


async def main():
    parser = argparse.ArgumentParser(description="Ultimate dry-run quant orchestrator.")
    parser.add_argument("--once", action="store_true", default=True)
    args = parser.parse_args()
    orchestrator = UltimateQuantOrchestrator()
    await orchestrator.initialize()
    try:
        result = await orchestrator.run_once()
        payload = json.dumps(
            {
                "context": result.context,
                "rag_hits": result.rag_hits,
                "committees": result.committees,
                "final_adjudication": result.final_adjudication,
            },
            ensure_ascii=False,
            default=str,
            indent=2,
        )
        sys.stdout.buffer.write((payload + "\n").encode("utf-8"))
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())
