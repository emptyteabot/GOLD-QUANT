"use client";
import { useEffect, useState } from "react";
import type { MacroData } from "@/lib/api";

export default function MacroPanel() {
  const [data, setData] = useState<MacroData | null>(null);

  useEffect(() => {
    fetch("/api/macro").then(r => r.json()).then(setData).catch(() => {});
  }, []);

  if (!data) return <div className="okx-card p-4 text-okx-dim text-sm text-center">加载宏观数据...</div>;

  const biasColor = data.bias > 0.1 ? "text-okx-green" : data.bias < -0.1 ? "text-okx-red" : "text-okx-muted";
  const biasLabel = data.bias > 0.1 ? "利多黄金" : data.bias < -0.1 ? "利空黄金" : "中性";

  return (
    <div className="okx-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-okx-text tracking-wide uppercase">宏观面分析</h3>
        <span className={`text-xs font-semibold ${biasColor}`}>{biasLabel}</span>
      </div>

      {/* Bias Meter */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <div className="h-2 bg-okx-border rounded-full overflow-hidden">
            <div className={`h-full rounded-full transition-all ${data.bias > 0 ? "bg-okx-green" : "bg-okx-red"}`}
              style={{ width: `${Math.min(100, Math.abs(data.bias) * 100 + 50)}%`, marginLeft: data.bias < 0 ? "auto" : 0 }} />
          </div>
          <div className="flex justify-between mt-1 text-[10px] text-okx-dim">
            <span>利空</span><span>中性</span><span>利多</span>
          </div>
        </div>
        <div className={`font-mono text-2xl font-bold ${biasColor}`}>
          {data.bias > 0 ? "+" : ""}{data.bias.toFixed(3)}
        </div>
      </div>

      {/* Factors */}
      <div className="space-y-2">
        {data.factors.gold_signal && (
          <div className="flex items-center justify-between py-2 border-t border-okx-border/50">
            <span className="text-xs text-okx-dim">🥇 国际金价</span>
            <span className="text-xs text-okx-muted">{data.factors.gold_signal}</span>
          </div>
        )}
        {data.factors.flow_signal && (
          <div className="flex items-center justify-between py-2 border-t border-okx-border/50">
            <span className="text-xs text-okx-dim">💰 板块资金</span>
            <span className="text-xs text-okx-muted">{data.factors.flow_signal}</span>
          </div>
        )}
        <div className="flex items-center justify-between py-2 border-t border-okx-border/50">
          <span className="text-xs text-okx-dim">📊 置信度</span>
          <span className="text-xs font-mono text-okx-text">{(data.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}



