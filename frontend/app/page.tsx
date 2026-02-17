"use client";
import { useState } from "react";
import Header from "@/components/Header";
import PriceTicker from "@/components/PriceTicker";
import SignalPanel from "@/components/SignalPanel";
import TradingChart from "@/components/TradingChart";
import MacroPanel from "@/components/MacroPanel";

type Tab = "market" | "signals" | "chart" | "macro";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("market");

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: "market", label: "行情", icon: "📊" },
    { key: "signals", label: "信号", icon: "🎯" },
    { key: "chart", label: "图表", icon: "📈" },
    { key: "macro", label: "宏观", icon: "🌍" },
  ];

  return (
    <div className="min-h-screen bg-okx-bg">
      <Header />

      <main className="max-w-[1600px] mx-auto px-4 py-4">
        {/* Tab Bar */}
        <div className="flex items-center gap-1 mb-5 p-1 bg-okx-card border border-okx-border rounded-xl w-fit">
          {tabs.map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold transition-all
                ${activeTab === tab.key
                  ? "bg-okx-gold/10 text-okx-gold border border-okx-gold/20 shadow-[0_0_12px_rgba(252,213,53,0.08)]"
                  : "text-okx-muted hover:text-okx-text hover:bg-white/[0.03]"
                }`}>
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* ────── Market Tab ────── */}
        {activeTab === "market" && (
          <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-4">
            <div className="space-y-4">
              {/* Price Table */}
              <div className="okx-card overflow-hidden">
                <div className="px-5 py-3 border-b border-okx-border flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-okx-text tracking-wide uppercase">黄金板块行情</h2>
                  <span className="text-[10px] text-okx-dim">实时刷新 15s</span>
                </div>
                <PriceTicker />
              </div>
              {/* Quick Chart */}
              <TradingChart code="518880" />
            </div>

            {/* Right Sidebar */}
            <div className="space-y-4">
              <MacroPanel />
              {/* Quick Signals */}
              <div className="okx-card p-5">
                <h3 className="text-sm font-semibold text-okx-text tracking-wide uppercase mb-3">信号快报</h3>
                <SignalPanel />
              </div>
            </div>
          </div>
        )}

        {/* ────── Signals Tab ────── */}
        {activeTab === "signals" && (
          <div className="max-w-4xl">
            <div className="mb-4">
              <h2 className="text-lg font-bold text-okx-text">交易信号</h2>
              <p className="text-sm text-okx-dim mt-1">七维策略引擎 · 行情自适应 · K线形态识别</p>
            </div>
            <SignalPanel />
          </div>
        )}

        {/* ────── Chart Tab ────── */}
        {activeTab === "chart" && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-bold text-okx-text">技术图表</h2>
              <p className="text-sm text-okx-dim mt-1">TradingView 级别 K线图 · 多周期切换</p>
            </div>
            <TradingChart code="518880" />
          </div>
        )}

        {/* ────── Macro Tab ────── */}
        {activeTab === "macro" && (
          <div className="max-w-2xl">
            <div className="mb-4">
              <h2 className="text-lg font-bold text-okx-text">宏观面分析</h2>
              <p className="text-sm text-okx-dim mt-1">国际金价 · 上海金价 · 板块资金流向</p>
            </div>
            <MacroPanel />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-okx-border mt-8 py-4 text-center text-[11px] text-okx-dim">
        © 2026 Gold Advisor Pro™ · 仅供参考，不构成投资建议
      </footer>
    </div>
  );
}



