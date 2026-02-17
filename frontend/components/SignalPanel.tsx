"use client";
import { useEffect, useState } from "react";
import type { Signal } from "@/lib/api";

function SignalBadge({ direction }: { direction: string }) {
  if (direction === "BUY") return (
    <span className="px-3 py-1 rounded-md text-xs font-bold bg-okx-green/15 text-okx-green border border-okx-green/20">
      BUY · 买入
    </span>
  );
  if (direction === "SELL") return (
    <span className="px-3 py-1 rounded-md text-xs font-bold bg-okx-red/15 text-okx-red border border-okx-red/20">
      SELL · 卖出
    </span>
  );
  return (
    <span className="px-3 py-1 rounded-md text-xs font-bold bg-white/5 text-okx-dim border border-okx-border">
      HOLD · 观望
    </span>
  );
}

function UrgencyDot({ urgency }: { urgency: string }) {
  const cls = urgency === "CRITICAL" ? "bg-okx-red live-pulse"
    : urgency === "HIGH" ? "bg-okx-gold"
    : "bg-okx-dim";
  return <span className={`w-2 h-2 rounded-full ${cls}`} />;
}

function RegimeBadge({ regime }: { regime: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    TREND_UP: { label: "📈 趋势上涨", cls: "text-okx-green bg-okx-green/10" },
    TREND_DOWN: { label: "📉 趋势下跌", cls: "text-okx-red bg-okx-red/10" },
    RANGE: { label: "↔️ 震荡", cls: "text-okx-muted bg-white/5" },
    CRASH: { label: "💥 暴跌", cls: "text-okx-red bg-okx-red/10" },
    REVERSAL: { label: "🚗 倒车接人", cls: "text-okx-green bg-okx-green/10" },
  };
  const m = map[regime] || { label: regime, cls: "text-okx-dim bg-white/5" };
  return <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${m.cls}`}>{m.label}</span>;
}

export default function SignalPanel() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/signals")
      .then(r => r.json())
      .then(d => { setSignals(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="okx-card p-8 text-center text-okx-dim text-sm">
      <div className="animate-spin w-6 h-6 border-2 border-okx-gold/30 border-t-okx-gold rounded-full mx-auto mb-3" />
      分析中...
    </div>
  );

  return (
    <div className="space-y-3">
      {signals.map((sig) => {
        const borderColor = sig.direction === "BUY" ? "border-l-okx-green"
          : sig.direction === "SELL" ? "border-l-okx-red"
          : "border-l-okx-border";
        return (
          <div key={sig.code} className={`okx-card border-l-[3px] ${borderColor} p-5`}>
            {/* Header Row */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <UrgencyDot urgency={sig.urgency} />
                <div>
                  <span className="font-semibold text-okx-text">{sig.name}</span>
                  <span className="ml-2 text-xs text-okx-dim">{sig.code}</span>
                </div>
                <RegimeBadge regime={sig.regime} />
              </div>
              <SignalBadge direction={sig.direction} />
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
              <div>
                <div className="text-[10px] text-okx-dim uppercase tracking-wider">评分</div>
                <div className={`font-mono font-bold text-lg ${sig.score > 0 ? "text-okx-green" : sig.score < 0 ? "text-okx-red" : "text-okx-muted"}`}>
                  {sig.score > 0 ? "+" : ""}{sig.score.toFixed(3)}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-okx-dim uppercase tracking-wider">置信度</div>
                <div className="font-mono font-bold text-lg text-okx-text">{(sig.confidence * 100).toFixed(0)}%</div>
              </div>
              {sig.direction !== "HOLD" && (
                <>
                  <div>
                    <div className="text-[10px] text-okx-dim uppercase tracking-wider">入场价</div>
                    <div className="font-mono font-semibold text-okx-text">¥{sig.entry_price.toFixed(3)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-okx-dim uppercase tracking-wider">盈亏比</div>
                    <div className="font-mono font-bold text-okx-gold">{sig.risk_reward}:1</div>
                  </div>
                </>
              )}
            </div>

            {/* SL / TP */}
            {sig.direction !== "HOLD" && (
              <div className="flex gap-4 mb-3 text-xs">
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-okx-red" />
                  <span className="text-okx-dim">止损</span>
                  <span className="font-mono text-okx-red">¥{sig.stop_loss.toFixed(3)}</span>
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-okx-green" />
                  <span className="text-okx-dim">止盈</span>
                  <span className="font-mono text-okx-green">¥{sig.take_profit.toFixed(3)}</span>
                </span>
                {sig.is_t0 && <span className="text-okx-blue">⚡ T+0 日内</span>}
              </div>
            )}

            {/* Patterns */}
            {sig.patterns && sig.patterns.length > 0 && (
              <div className="flex gap-2 mb-2 flex-wrap">
                {sig.patterns.map((p: any, i: number) => (
                  <span key={i} className={`px-2 py-0.5 rounded text-[10px] font-semibold
                    ${p.type === "bullish" ? "bg-okx-green/10 text-okx-green"
                    : p.type === "bearish" ? "bg-okx-red/10 text-okx-red"
                    : "bg-white/5 text-okx-muted"}`}>
                    🕯️ {p.name}
                  </span>
                ))}
              </div>
            )}

            {/* Reason */}
            <p className="text-xs text-okx-dim leading-relaxed">{sig.reason}</p>
          </div>
        );
      })}
    </div>
  );
}



