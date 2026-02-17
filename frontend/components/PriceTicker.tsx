"use client";
import { useEffect, useState } from "react";
import type { Quote } from "@/lib/api";

export default function PriceTicker() {
  const [quotes, setQuotes] = useState<Quote[]>([]);

  useEffect(() => {
    const load = () => fetch("/api/quotes").then(r => r.json()).then(setQuotes).catch(() => {});
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  if (!quotes.length) return (
    <div className="okx-card p-4 text-center text-okx-dim text-sm">加载行情中...</div>
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-okx-dim text-xs uppercase tracking-wider border-b border-okx-border">
            <th className="text-left py-3 px-4 font-medium">标的</th>
            <th className="text-right py-3 px-2 font-medium">最新价</th>
            <th className="text-right py-3 px-2 font-medium">涨跌幅</th>
            <th className="text-right py-3 px-2 font-medium hidden lg:table-cell">成交额</th>
            <th className="text-right py-3 px-2 font-medium hidden lg:table-cell">振幅</th>
            <th className="text-center py-3 px-2 font-medium">T+0</th>
          </tr>
        </thead>
        <tbody>
          {quotes.map((q) => {
            const isUp = q.change_pct >= 0;
            const color = q.change_pct > 0 ? "text-okx-green" : q.change_pct < 0 ? "text-okx-red" : "text-okx-muted";
            return (
              <tr key={q.code} className="border-b border-okx-border/50 hover:bg-white/[0.02] transition-colors">
                <td className="py-3 px-4">
                  <div className="font-semibold text-okx-text">{q.name}</div>
                  <div className="text-xs text-okx-dim">{q.code} · {q.type}</div>
                </td>
                <td className={`text-right py-3 px-2 font-mono font-semibold ${color}`}>
                  ¥{q.price.toFixed(3)}
                </td>
                <td className="text-right py-3 px-2">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono font-semibold text-xs
                    ${isUp ? "bg-okx-green/10 text-okx-green" : "bg-okx-red/10 text-okx-red"}`}>
                    {q.change_pct > 0 ? "+" : ""}{q.change_pct.toFixed(2)}%
                  </span>
                </td>
                <td className="text-right py-3 px-2 font-mono text-okx-muted hidden lg:table-cell">
                  {(q.amount / 1e8).toFixed(2)}亿
                </td>
                <td className="text-right py-3 px-2 font-mono text-okx-muted hidden lg:table-cell">
                  {q.amplitude.toFixed(2)}%
                </td>
                <td className="text-center py-3 px-2">
                  {q.t0 ? (
                    <span className="text-xs text-okx-green bg-okx-green/10 px-2 py-0.5 rounded">T+0</span>
                  ) : (
                    <span className="text-xs text-okx-dim">T+1</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}



