"""
超级Multi-Agent V3.0 - 终极版
整合所有升级 + 顶级量化策略
"""
import logging
import numpy as np
from typing import Dict
import pandas as pd

logger = logging.getLogger(__name__)


class SuperAgentV3:
    """超级代理 V3.0"""
    
    def __init__(self):
        # 加载所有模块
        self.modules = {}
        
        try:
            from xgboost_agent import XGBoostAgent
            self.modules['xgboost'] = XGBoostAgent()
        except: pass
        
        try:
            from lstm_agent import LSTMAgent
            agent = LSTMAgent()
            if agent.available:
                self.modules['lstm'] = agent
        except: pass
        
        try:
            from dqn_agent import DQNAgent
            agent = DQNAgent()
            if agent.available:
                self.modules['dqn'] = agent
        except: pass
        
        try:
            from stacking_ensemble import StackingEnsemble
            self.modules['stacking'] = StackingEnsemble()
        except: pass
        
        try:
            from multi_timeframe import MultiTimeframeAnalyzer
            self.modules['mtf'] = MultiTimeframeAnalyzer()
        except: pass
        
        try:
            from elite_quant_strategies import EliteQuantStrategies
            self.modules['elite'] = EliteQuantStrategies()
        except: pass
        
        # 原有模块
        from complete_multi_agent import CompleteMultiAgentSystem
        self.base_system = CompleteMultiAgentSystem()
        
        logger.info(f"✅ SuperAgent V3.0 初始化 ({len(self.modules)}个高级模块)")
    
    def train(self, klines_df: pd.DataFrame):
        """训练所有模型"""
        self.base_system.train_ml_model(klines_df)
        
        for name, module in self.modules.items():
            try:
                if hasattr(module, 'train'):
                    module.train(klines_df)
            except: pass
    
    def decide(self, macro_data: Dict, tech_data: Dict, klines_df: pd.DataFrame, price: float) -> Dict:
        """V3.0 超级决策"""
        logger.info("\n" + "="*80)
        logger.info("🚀 SuperAgent V3.0 决策")
        logger.info("="*80)
        
        # 基础系统决策
        base_decision = self.base_system.make_decision(macro_data, tech_data, klines_df, price)
        signals = base_decision['agent_signals']
        
        # 高级模块信号
        if 'elite' in self.modules:
            elite_result = self.modules['elite'].analyze(klines_df, macro_data)
            signals['elite'] = elite_result['signal']
            logger.info(f"🏆 Elite Quant: {elite_result['signal']:+.2f}")
        
        if 'mtf' in self.modules:
            mtf_result = self.modules['mtf'].analyze(klines_df)
            signals['mtf'] = mtf_result['signal']
            logger.info(f"⏰ MTF: {mtf_result['signal']:+.2f}")
        
        if 'xgboost' in self.modules:
            try:
                features = {
                    'rsi': tech_data.get('rsi', 50),
                    'macd': 0,
                    'macd_signal': 0,
                    'sma_20': klines_df['close'].rolling(20).mean().iloc[-1],
                    'sma_50': klines_df['close'].rolling(50).mean().iloc[-1] if len(klines_df) >= 50 else 0,
                    'volatility': klines_df['close'].pct_change().rolling(20).std().iloc[-1],
                    'volume_ratio': klines_df['volume'].iloc[-1] / klines_df['volume'].rolling(20).mean().iloc[-1],
                    'momentum': klines_df['close'].pct_change(10).iloc[-1],
                    'roc': 0
                }
                xgb_result = self.modules['xgboost'].predict(features)
                signals['xgboost'] = xgb_result['signal']
                logger.info(f"🚀 XGBoost: {xgb_result['signal']:+.2f}")
            except: pass
        
        # 动态权重
        weights = {k: 1.0 / len(signals) for k in signals.keys()}
        
        # 如果有Elite策略,给更高权重
        if 'elite' in signals:
            weights['elite'] = 0.25
            remaining = 0.75 / (len(signals) - 1)
            for k in signals.keys():
                if k != 'elite':
                    weights[k] = remaining
        
        # 加权信号
        final_signal = sum(signals[k] * weights[k] for k in signals.keys())
        
        # 共识度
        consensus = 1 - (np.std(list(signals.values())) / 2)
        confidence = (abs(final_signal) + consensus) / 2
        
        # 杠杆
        if confidence >= 0.85:
            leverage = 15
        elif confidence >= 0.75:
            leverage = 12
        elif confidence >= 0.65:
            leverage = 10
        else:
            leverage = 8
        
        logger.info(f"\n🎯 V3.0决策: 信号={final_signal:+.2f} 置信度={confidence:.1%} 杠杆={leverage}x")
        
        should_trade = confidence >= 0.50 and abs(final_signal) >= 0.20 and consensus >= 0.45
        
        return {
            'should_trade': should_trade,
            'signal': final_signal,
            'confidence': confidence,
            'consensus': consensus,
            'leverage': leverage,
            'agent_signals': signals,
            'reason': '✅ V3.0' if should_trade else '❌ 信号不足'
        }
