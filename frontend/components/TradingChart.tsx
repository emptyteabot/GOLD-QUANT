"use client";
import { useEffect, useRef, useState } from "react";

interface KlineBar {
  time: string; open: number; high: number; low: number; close: number; volume: number;
}

export default function TradingChart({ code = "518880" }: { code?: string }) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<KlineBar[]>([]);
  const [period, setPeriod] = useState("5");

  useEffect(() => {
    fetch(`/api/klines?code=${code}&period=${period}&days=5`)
      .then(r => r.json()).then(setData).catch(() => {});
  }, [code, period]);

  useEffect(() => {
    if (!chartRef.current || !data.length) return;
    let chart: any = null;

    import("lightweight-charts").then(({ createChart }) => {
      if (!chartRef.current) return;
      chartRef.current.innerHTML = "";

      chart = createChart(chartRef.current, {
        width: chartRef.current.clientWidth,
        height: 480,
        layout: { background: { color: "#0b0e11" }, textColor: "#848e9c", fontSize: 11, fontFamily: "Inter" },
        grid: { vertLines: { color: "#1e2329" }, horzLines: { color: "#1e2329" } },
        crosshair: { mode: 0, vertLine: { color: "#474d57", width: 1, style: 2 }, horzLine: { color: "#474d57", width: 1, style: 2 } },
        rightPriceScale: { borderColor: "#1e2329", scaleMargins: { top: 0.1, bottom: 0.2 } },
        timeScale: { borderColor: "#1e2329", timeVisible: true, secondsVisible: false },
      });

      const candleSeries = chart.addCandlestickSeries({
        upColor: "#0ecb81", downColor: "#f6465d",
        borderUpColor: "#0ecb81", borderDownColor: "#f6465d",
        wickUpColor: "#0ecb81", wickDownColor: "#f6465d",
      });

      const volumeSeries = chart.addHistogramSeries({
        priceFormat: { type: "volume" },
        priceScaleId: "vol",
      });
      chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });

      const formatted = data.map(d => ({
        time: Math.floor(new Date(d.time).getTime() / 1000) as any,
        open: d.open, high: d.high, low: d.low, close: d.close,
      }));

      const volFormatted = data.map(d => ({
        time: Math.floor(new Date(d.time).getTime() / 1000) as any,
        value: d.volume,
        color: d.close >= d.open ? "rgba(14,203,129,0.3)" : "rgba(246,70,93,0.3)",
      }));

      candleSeries.setData(formatted);
      volumeSeries.setData(volFormatted);
      chart.timeScale().fitContent();

      const handleResize = () => {
        if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth });
      };
      window.addEventListener("resize", handleResize);
      return () => window.removeEventListener("resize", handleResize);
    });

    return () => { if (chart) chart.remove(); };
  }, [data]);

  const periods = [
    { value: "5", label: "5m" }, { value: "15", label: "15m" },
    { value: "30", label: "30m" }, { value: "60", label: "1H" },
    { value: "daily", label: "1D" },
  ];

  return (
    <div className="okx-card overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-1 px-4 py-2.5 border-b border-okx-border">
        {periods.map(p => (
          <button key={p.value} onClick={() => setPeriod(p.value)}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors
              ${period === p.value
                ? "bg-okx-gold/10 text-okx-gold border border-okx-gold/20"
                : "text-okx-muted hover:text-okx-text hover:bg-white/[0.03]"
              }`}>
            {p.label}
          </button>
        ))}
      </div>
      {/* Chart */}
      <div ref={chartRef} className="w-full" style={{ minHeight: 480 }}>
        {!data.length && (
          <div className="flex items-center justify-center h-[480px] text-okx-dim text-sm">
            加载K线数据...
          </div>
        )}
      </div>
    </div>
  );
}



