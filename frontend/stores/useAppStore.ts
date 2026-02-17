// Zustand 状态管理
import { create } from 'zustand';
import { AccountInfo, Position, Signal, MarketData } from '@/types';

interface AppState {
  // 账户信息
  account: AccountInfo | null;
  setAccount: (account: AccountInfo) => void;

  // 持仓信息
  positions: Position[];
  setPositions: (positions: Position[]) => void;

  // 交易信号
  signals: Signal[];
  addSignal: (signal: Signal) => void;

  // 市场数据
  marketData: Map<string, MarketData>;
  updateMarketData: (symbol: string, data: MarketData) => void;

  // UI状态
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  account: null,
  setAccount: (account) => set({ account }),

  positions: [],
  setPositions: (positions) => set({ positions }),

  signals: [],
  addSignal: (signal) => set((state) => ({
    signals: [signal, ...state.signals].slice(0, 50) // 保留最近50条
  })),

  marketData: new Map(),
  updateMarketData: (symbol, data) => set((state) => {
    const newMap = new Map(state.marketData);
    newMap.set(symbol, data);
    return { marketData: newMap };
  }),

  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
