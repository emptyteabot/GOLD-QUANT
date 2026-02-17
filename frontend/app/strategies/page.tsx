"use client";
import { useState } from 'react';
import { Save, Play } from 'lucide-react';

export default function StrategiesPage() {
  const [config, setConfig] = useState({
    name: 'AURUM Multi-Agent v3.0',
    symbol: 'XAU-USDT-SWAP',
    timeframe: '15m',
    leverage: 10,
    stopLoss: 2,
    maxPosition: 80,
    weights: {
      macro: 30,
      technical: 30,
      ml: 25,
      xaut: 15,
    }
  });

  const handleSave = () => {
    console.log('保存策略配置:', config);
    // TODO: 调用API保存配置
  };

  const handleRun = () => {
    console.log('运行策略:', config);
    // TODO: 调用API启动策略
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-okx-text">策略配置</h1>
          <p className="text-okx-muted mt-1">配置多代理量化策略参数</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-4 py-2 bg-okx-card border border-okx-border text-okx-text rounded-lg hover:bg-okx-hover"
          >
            <Save className="w-4 h-4" />
            保存
          </button>
          <button
            onClick={handleRun}
            className="flex items-center gap-2 px-4 py-2 bg-okx-green text-white rounded-lg hover:bg-okx-green/90"
          >
            <Play className="w-4 h-4" />
            运行
          </button>
        </div>
      </div>

      {/* 基础设置 */}
      <div className="okx-card p-6">
        <h2 className="text-lg font-semibold text-okx-text mb-4">基础设置</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-okx-muted mb-2">策略名称</label>
            <input
              type="text"
              value={config.name}
              onChange={(e) => setConfig({ ...config, name: e.target.value })}
              className="w-full px-4 py-2 bg-okx-bg border border-okx-border rounded-lg text-okx-text focus:border-okx-gold focus:outline-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-okx-muted mb-2">交易品种</label>
              <select
                value={config.symbol}
                onChange={(e) => setConfig({ ...config, symbol: e.target.value })}
                className="w-full px-4 py-2 bg-okx-bg border border-okx-border rounded-lg text-okx-text focus:border-okx-gold focus:outline-none"
              >
                <option value="XAU-USDT-SWAP">XAU-USDT-SWAP</option>
                <option value="BTC-USDT-SWAP">BTC-USDT-SWAP</option>
                <option value="ETH-USDT-SWAP">ETH-USDT-SWAP</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-okx-muted mb-2">时间框架</label>
              <select
                value={config.timeframe}
                onChange={(e) => setConfig({ ...config, timeframe: e.target.value })}
                className="w-full px-4 py-2 bg-okx-bg border border-okx-border rounded-lg text-okx-text focus:border-okx-gold focus:outline-none"
              >
                <option value="5m">5分钟</option>
                <option value="15m">15分钟</option>
                <option value="1h">1小时</option>
                <option value="4h">4小时</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* 风险控制 */}
      <div className="okx-card p-6">
        <h2 className="text-lg font-semibold text-okx-text mb-4">风险控制</h2>
        <div className="space-y-6">
          <SliderControl
            label="最大杠杆"
            value={config.leverage}
            onChange={(v) => setConfig({ ...config, leverage: v })}
            min={1}
            max={20}
            unit="x"
          />
          <SliderControl
            label="单笔止损"
            value={config.stopLoss}
            onChange={(v) => setConfig({ ...config, stopLoss: v })}
            min={0.5}
            max={5}
            step={0.1}
            unit="%"
          />
          <SliderControl
            label="最大仓位"
            value={config.maxPosition}
            onChange={(v) => setConfig({ ...config, maxPosition: v })}
            min={10}
            max={100}
            unit="%"
          />
        </div>
      </div>

      {/* AI代理权重 */}
      <div className="okx-card p-6">
        <h2 className="text-lg font-semibold text-okx-text mb-4">AI代理权重</h2>
        <div className="space-y-6">
          <SliderControl
            label="宏观分析"
            value={config.weights.macro}
            onChange={(v) => setConfig({ ...config, weights: { ...config.weights, macro: v } })}
            min={0}
            max={100}
            unit="%"
          />
          <SliderControl
            label="技术分析"
            value={config.weights.technical}
            onChange={(v) => setConfig({ ...config, weights: { ...config.weights, technical: v } })}
            min={0}
            max={100}
            unit="%"
          />
          <SliderControl
            label="机器学习"
            value={config.weights.ml}
            onChange={(v) => setConfig({ ...config, weights: { ...config.weights, ml: v } })}
            min={0}
            max={100}
            unit="%"
          />
          <SliderControl
            label="XAUT策略"
            value={config.weights.xaut}
            onChange={(v) => setConfig({ ...config, weights: { ...config.weights, xaut: v } })}
            min={0}
            max={100}
            unit="%"
          />
        </div>
        <div className="mt-4 p-3 bg-okx-bg rounded-lg">
          <span className="text-okx-muted text-sm">权重总和: </span>
          <span className={`text-sm font-semibold ${
            Object.values(config.weights).reduce((a, b) => a + b, 0) === 100
              ? 'text-okx-green'
              : 'text-okx-red'
          }`}>
            {Object.values(config.weights).reduce((a, b) => a + b, 0)}%
          </span>
        </div>
      </div>
    </div>
  );
}

// 滑块控制组件
function SliderControl({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  unit = ''
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  unit?: string;
}) {
  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <label className="text-sm text-okx-muted">{label}</label>
        <span className="text-sm font-semibold text-okx-text">
          {value}{unit}
        </span>
      </div>
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        min={min}
        max={max}
        step={step}
        className="w-full h-2 bg-okx-bg rounded-lg appearance-none cursor-pointer slider"
      />
      <div className="flex justify-between text-xs text-okx-dim mt-1">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}
