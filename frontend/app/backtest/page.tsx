"use client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Download, TrendingUp, TrendingDown, Activity } from 'lucide-react';

// 模拟数据
const mockEquityCurve = Array.from({ length: 90 }, (_, i) => ({
  date: `2025-${String(Math.floor(i / 30) + 1).padStart(2, '0')}-${String((i % 30) + 1).padStart(2, '0')}`,
  equity: 10000 + Math.random() * 2000 + i * 30,
  benchmark: 10000 + i * 20,
}));

const mockTrades = [
  { id: '1', date: '2025-01-15', side: 'long', entry: 4750, exit: 4820, pnl: 70, reason: '止盈' },
  { id: '2', date: '2025-01-18', side: 'short', entry: 4830, exit: 4780, pnl: 50, reason: '止盈' },
  { id: '3', date: '2025-01-20', side: 'long', entry: 4760, exit: 4740, pnl: -20, reason: '止损' },
  { id: '4', date: '2025-01-25', side: 'long', entry: 4700, exit: 4780, pnl: 80, reason: '止盈' },
  { id: '5', date: '2025-02-01', side: 'short', entry: 4800, exit: 4750, pnl: 50, reason: '止盈' },
];

export default function BacktestPage() {
  const handleExport = () => {
    console.log('导出回测报告');
    // TODO: 实现导出功能
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-okx-text">回测结果</h1>
          <p className="text-okx-muted mt-1">AURUM v3.0 · 2025-01-01 至 2025-03-31</p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-okx-gold text-okx-bg rounded-lg hover:bg-okx-gold/90 font-medium"
        >
          <Download className="w-4 h-4" />
          导出报告
        </button>
      </div>

      {/* 核心指标 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="总收益率"
          value="+23.5%"
          icon={<TrendingUp className="w-5 h-5" />}
          positive
        />
        <MetricCard
          title="最大回撤"
          value="-8.2%"
          icon={<TrendingDown className="w-5 h-5" />}
          positive
        />
        <MetricCard
          title="夏普比率"
          value="1.85"
          icon={<Activity className="w-5 h-5" />}
          positive
        />
      </div>

      {/* 收益曲线 */}
      <div className="okx-card p-6">
        <h2 className="text-lg font-semibold text-okx-text mb-4">收益曲线</h2>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={mockEquityCurve}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2329" />
            <XAxis
              dataKey="date"
              stroke="#848e9c"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => value.slice(5)}
            />
            <YAxis
              stroke="#848e9c"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#12161c',
                border: '1px solid #1e2329',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#848e9c' }}
            />
            <Line
              type="monotone"
              dataKey="equity"
              stroke="#0ecb81"
              strokeWidth={2}
              dot={false}
              name="策略权益"
            />
            <Line
              type="monotone"
              dataKey="benchmark"
              stroke="#848e9c"
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
              name="基准"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 交易统计 + 月度收益 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 交易统计 */}
        <div className="okx-card p-6">
          <h2 className="text-lg font-semibold text-okx-text mb-4">交易统计</h2>
          <div className="space-y-3">
            <StatRow label="总交易次数" value="45" />
            <StatRow label="胜率" value="62.2%" />
            <StatRow label="盈亏比" value="2.3" />
            <StatRow label="平均持仓" value="2.5天" />
            <StatRow label="最大连胜" value="8次" />
            <StatRow label="最大连亏" value="3次" />
          </div>
        </div>

        {/* 月度收益 */}
        <div className="okx-card p-6">
          <h2 className="text-lg font-semibold text-okx-text mb-4">月度收益</h2>
          <div className="space-y-3">
            <MonthRow month="2025-01" return={5.2} />
            <MonthRow month="2025-02" return={8.1} />
            <MonthRow month="2025-03" return={10.2} />
          </div>
        </div>
      </div>

      {/* 交易明细 */}
      <div className="okx-card p-6">
        <h2 className="text-lg font-semibold text-okx-text mb-4">交易明细</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-okx-border">
                <th className="text-left py-3 px-4 text-sm text-okx-muted font-medium">日期</th>
                <th className="text-left py-3 px-4 text-sm text-okx-muted font-medium">方向</th>
                <th className="text-right py-3 px-4 text-sm text-okx-muted font-medium">入场价</th>
                <th className="text-right py-3 px-4 text-sm text-okx-muted font-medium">出场价</th>
                <th className="text-right py-3 px-4 text-sm text-okx-muted font-medium">盈亏</th>
                <th className="text-left py-3 px-4 text-sm text-okx-muted font-medium">原因</th>
              </tr>
            </thead>
            <tbody>
              {mockTrades.map((trade) => (
                <tr key={trade.id} className="border-b border-okx-border/50 hover:bg-okx-hover">
                  <td className="py-3 px-4 text-sm text-okx-text">{trade.date}</td>
                  <td className="py-3 px-4">
                    <span className={`text-sm font-medium ${
                      trade.side === 'long' ? 'text-okx-green' : 'text-okx-red'
                    }`}>
                      {trade.side === 'long' ? '做多' : '做空'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-okx-text text-right">${trade.entry}</td>
                  <td className="py-3 px-4 text-sm text-okx-text text-right">${trade.exit}</td>
                  <td className="py-3 px-4 text-right">
                    <span className={`text-sm font-semibold ${
                      trade.pnl >= 0 ? 'text-okx-green' : 'text-okx-red'
                    }`}>
                      {trade.pnl >= 0 ? '+' : ''}${trade.pnl}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-okx-muted">{trade.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// 指标卡片
function MetricCard({ title, value, icon, positive }: {
  title: string;
  value: string;
  icon: React.ReactNode;
  positive: boolean;
}) {
  return (
    <div className="okx-card p-6">
      <div className="flex items-center justify-between mb-3">
        <span className="text-okx-muted text-sm">{title}</span>
        <div className={positive ? 'text-okx-green' : 'text-okx-red'}>{icon}</div>
      </div>
      <div className={`text-3xl font-bold ${positive ? 'text-okx-green' : 'text-okx-red'}`}>
        {value}
      </div>
    </div>
  );
}

// 统计行
function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-2">
      <span className="text-okx-muted text-sm">{label}</span>
      <span className="text-okx-text font-medium">{value}</span>
    </div>
  );
}

// 月度收益行
function MonthRow({ month, return: ret }: { month: string; return: number }) {
  return (
    <div className="flex justify-between items-center py-2">
      <span className="text-okx-muted text-sm">{month}</span>
      <span className={`font-semibold ${ret >= 0 ? 'text-okx-green' : 'text-okx-red'}`}>
        {ret >= 0 ? '+' : ''}{ret}%
      </span>
    </div>
  );
}
