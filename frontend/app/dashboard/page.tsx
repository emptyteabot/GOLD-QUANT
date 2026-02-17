"use client";
import { useRealtimeData } from '@/hooks/useRealtimeData';
import { useAppStore } from '@/stores/useAppStore';
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';

export default function DashboardPage() {
  useRealtimeData();
  const { account, positions, signals } = useAppStore();

  const latestSignal = signals[0];

  return (
    <div className="space-y-6">
      {/* 账户概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="账户权益"
          value={`$${account?.equity.toFixed(2) || '0.00'}`}
          change={account?.todayPnl || 0}
          icon={<DollarSign className="w-5 h-5" />}
        />
        <StatCard
          title="今日盈亏"
          value={`$${account?.todayPnl.toFixed(2) || '0.00'}`}
          change={account?.todayPnl || 0}
          icon={<Activity className="w-5 h-5" />}
        />
        <StatCard
          title="总收益率"
          value={`${account?.totalReturn.toFixed(2) || '0.00'}%`}
          change={account?.totalReturn || 0}
          icon={<TrendingUp className="w-5 h-5" />}
        />
      </div>

      {/* 实时行情 + 持仓 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 实时行情图表 */}
        <div className="okx-card p-6">
          <h2 className="text-lg font-semibold text-okx-text mb-4">实时行情 - XAU/USDT</h2>
          <div className="h-[400px] bg-okx-bg rounded-lg flex items-center justify-center">
            <p className="text-okx-muted">TradingView 图表加载中...</p>
          </div>
        </div>

        {/* 当前持仓 + 最新信号 */}
        <div className="space-y-4">
          {/* 当前持仓 */}
          <div className="okx-card p-6">
            <h3 className="text-lg font-semibold text-okx-text mb-4">当前持仓</h3>
            {positions.length > 0 ? (
              <div className="space-y-3">
                {positions.map((pos, idx) => (
                  <div key={idx} className="p-4 bg-okx-bg rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-okx-text font-medium">{pos.symbol}</span>
                      <span className={`text-sm font-semibold ${pos.side === 'long' ? 'text-okx-green' : 'text-okx-red'}`}>
                        {pos.side === 'long' ? '做多' : '做空'} {pos.size}张
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-okx-muted">开仓价:</span>
                        <span className="text-okx-text ml-2">${pos.entryPrice.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-okx-muted">浮盈:</span>
                        <span className={`ml-2 font-semibold ${pos.unrealizedPnl >= 0 ? 'text-okx-green' : 'text-okx-red'}`}>
                          ${pos.unrealizedPnl.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2 mt-3">
                      <button className="flex-1 px-3 py-1.5 bg-okx-red/10 text-okx-red rounded text-sm font-medium hover:bg-okx-red/20">
                        平仓
                      </button>
                      <button className="flex-1 px-3 py-1.5 bg-okx-green/10 text-okx-green rounded text-sm font-medium hover:bg-okx-green/20">
                        加仓
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-okx-muted text-center py-8">暂无持仓</p>
            )}
          </div>

          {/* 最新信号 */}
          <div className="okx-card p-6">
            <h3 className="text-lg font-semibold text-okx-text mb-4">最新信号</h3>
            {latestSignal ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`text-2xl font-bold ${
                    latestSignal.action === 'buy' ? 'text-okx-green' :
                    latestSignal.action === 'sell' ? 'text-okx-red' : 'text-okx-gold'
                  }`}>
                    {latestSignal.action === 'buy' ? '🟢 做多' :
                     latestSignal.action === 'sell' ? '🔴 做空' : '🟡 观望'}
                  </span>
                  <span className="text-okx-muted text-sm">
                    {new Date(latestSignal.timestamp).toLocaleTimeString('zh-CN')}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-okx-muted">信号强度:</span>
                    <span className="text-okx-text ml-2 font-medium">{latestSignal.strength.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-okx-muted">置信度:</span>
                    <span className="text-okx-text ml-2 font-medium">{(latestSignal.confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="p-3 bg-okx-bg rounded text-sm">
                  <span className="text-okx-muted">原因: </span>
                  <span className="text-okx-text">{latestSignal.reason}</span>
                </div>
              </div>
            ) : (
              <p className="text-okx-muted text-center py-8">等待信号...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// 统计卡片组件
function StatCard({ title, value, change, icon }: {
  title: string;
  value: string;
  change: number;
  icon: React.ReactNode;
}) {
  const isPositive = change >= 0;

  return (
    <div className="okx-card p-6">
      <div className="flex items-center justify-between mb-3">
        <span className="text-okx-muted text-sm">{title}</span>
        <div className="text-okx-gold">{icon}</div>
      </div>
      <div className="text-3xl font-bold text-okx-text mb-2">{value}</div>
      <div className="flex items-center gap-1">
        {isPositive ? (
          <TrendingUp className="w-4 h-4 text-okx-green" />
        ) : (
          <TrendingDown className="w-4 h-4 text-okx-red" />
        )}
        <span className={`text-sm font-medium ${isPositive ? 'text-okx-green' : 'text-okx-red'}`}>
          {isPositive ? '+' : ''}{change.toFixed(2)}%
        </span>
      </div>
    </div>
  );
}
