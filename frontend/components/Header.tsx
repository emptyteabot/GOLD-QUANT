"use client";
import { useEffect, useState } from "react";
import type { MarketStatus } from "@/lib/api";

export default function Header() {
  const [status, setStatus] = useState<MarketStatus | null>(null);
  const [time, setTime] = useState("");

  useEffect(() => {
    const tick = () => setTime(new Date().toLocaleTimeString("zh-CN", { hour12: false }));
    tick();
    const t = setInterval(tick, 1000);
    fetch("/api/market-status").then(r => r.json()).then(setStatus).catch(() => {});
    const s = setInterval(() => {
      fetch("/api/market-status").then(r => r.json()).then(setStatus).catch(() => {});
    }, 30000);
    return () => { clearInterval(t); clearInterval(s); };
  }, []);

  const dotColor = status?.is_trading ? "bg-okx-green" : "bg-okx-red";

  return (
    <header className="sticky top-0 z-50 border-b border-okx-border bg-okx-bg/80 backdrop-blur-xl">
      <div className="max-w-[1600px] mx-auto px-4 h-14 flex items-center justify-between">
        {/* Left: Logo */}
        <div className="flex items-center gap-3">
          <span className="text-2xl">🥇</span>
          <span className="text-lg font-extrabold tracking-tight bg-gradient-to-r from-okx-gold to-yellow-300 bg-clip-text text-transparent">
            Gold Advisor Pro
          </span>
          <span className="px-2.5 py-0.5 text-[10px] font-semibold tracking-wider text-okx-gold bg-okx-gold/10 border border-okx-gold/20 rounded-full">
            v3.0
          </span>
        </div>

        {/* Center: Nav */}
        <nav className="hidden md:flex items-center gap-1">
          {["行情", "信号", "图表", "宏观", "回测"].map((item) => (
            <button key={item} className="px-4 py-1.5 text-sm font-medium text-okx-muted hover:text-okx-text hover:bg-white/[0.03] rounded-lg transition-colors">
              {item}
            </button>
          ))}
        </nav>

        {/* Right: Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <span className={`w-2 h-2 rounded-full ${dotColor} live-pulse`} />
            <span className="text-okx-muted">{status?.status || "—"}</span>
          </div>
          <span className="font-mono text-sm text-okx-dim">{time}</span>
        </div>
      </div>
    </header>
  );
}



