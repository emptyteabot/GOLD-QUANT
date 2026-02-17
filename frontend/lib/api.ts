const API = process.env.NEXT_PUBLIC_API_URL || "";

export async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface Quote {
  code: string; name: string; price: number; change_pct: number;
  change_amt: number; volume: number; amount: number;
  open: number; high: number; low: number; prev_close: number;
  turnover_rate: number; amplitude: number; t0: boolean; type: string;
}

export interface Signal {
  code: string; name: string; direction: "BUY" | "SELL" | "HOLD";
  score: number; confidence: number;
  entry_price: number; stop_loss: number; take_profit: number;
  risk_reward: number; reason: string; urgency: string;
  regime: string; regime_desc: string; is_t0: boolean;
  macro_bias: number; patterns: any[]; strategies: Record<string, any>;
}

export interface KlineBar {
  time: string; open: number; high: number; low: number;
  close: number; volume: number;
}

export interface MarketStatus {
  status: string; icon: string; is_trading: boolean; time: string;
}

export interface MacroData {
  bias: number; confidence: number; summary: string; factors: Record<string, any>;
}



