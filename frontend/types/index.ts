// AURUM Dashboard 类型定义

export interface AccountInfo {
  equity: number;
  balance: number;
  todayPnl: number;
  totalReturn: number;
  availableMargin: number;
  usedMargin: number;
}

export interface Position {
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  leverage: number;
  liquidationPrice: number;
}

export interface Signal {
  timestamp: number;
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  strength: number;
  confidence: number;
  reason: string;
  agents: {
    macro: number;
    technical: number;
    ml: number;
    xaut: number;
  };
}

export interface MarketData {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  timestamp: number;
}

export interface Strategy {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  leverage: number;
  stopLoss: number;
  maxPosition: number;
  agentWeights: {
    macro: number;
    technical: number;
    ml: number;
    xaut: number;
  };
  status: 'active' | 'paused' | 'stopped';
}

export interface BacktestResult {
  strategyId: string;
  startDate: string;
  endDate: string;
  totalReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  avgHoldingPeriod: number;
  equityCurve: { date: string; equity: number }[];
  trades: Trade[];
  monthlyReturns: { month: string; return: number }[];
}

export interface Trade {
  id: string;
  timestamp: number;
  symbol: string;
  side: 'long' | 'short';
  entryPrice: number;
  exitPrice: number;
  size: number;
  pnl: number;
  reason: string;
}

export interface WebSocketMessage {
  type: 'price' | 'signal' | 'position' | 'account';
  data: any;
  timestamp: number;
}
