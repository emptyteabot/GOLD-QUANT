"""
GOD MODE AGENT - 上帝模式
整合所有最强策略,战胜市场
"""
import logging
import numpy as np
from typing import Dict
import pandas as pd

logger = logging.getLogger(__name__)


class GodModeAgent:
    """上帝模式代理"""
    
    def __init__(self):
        self.agents = {}
        
        # 加载所有模块
        try:
            from super_agent_v3 import SuperAgentV3
            self.agents['super_v3'] = SuperAgentV3()
        except: pass
        
        try:
            from ultimate_market_beater import UltimateMarketBeater
            self.agents['ultimate'] = UltimateMarketBeater()
        except: pass
        
        try:
            from elite_quant_strategies import EliteQuantStrategies
            self.agents['elite'] = EliteQuantStrategies()
        except: pass
        
        # 原始系统
        from complete_multi_agent import CompleteMultiAgentSystem
        self.agents['base'] = CompleteMultiAgentSystem()
        
        logger.info(f"🔥 GOD MODE 初始化 ({len(self.agents)}个系统)")
    
    def train(self, klines_df: pd.DataFrame):
        """训练所有系统"""
        logger.info("\n🔥 GOD MODE 训练中...")
        
        for name, agent in self.agents.items():
            try:
                if hasattr(agent, 'train'):
                    agent.train(klines_df)
                elif hasattr(agent, 'train_ml_model'):
                    agent.train_ml_model(klines_df)
            except Exception as e:
                logger.warning(f"训练{name}失败: {e}")
    
    def decide(self, macro_data: Dict, tech_data: Dict, klines_df: pd.DataFrame, price: float) -> Dict:
        """GOD MODE 决策"""
        logger.info("\n" + "="*80)
        logger.info("🔥🔥🔥 GOD MODE DECISION 🔥🔥🔥")
        logger.info("="*80)
        
        signals = {}
        
        # 1. Base系统
        try:
            base_result = self.agents['base'].make_decision(macro_data, tech_data, klines_df, price)
            signals['base'] = base_result['signal']
            logger.info(f"📊 Base系统: {base_result['signal']:+.2f}")
        except Exception as e:
            logger.error(f"Base失败: {e}")
        
        # 2. SuperV3系统
        if 'super_v3' in self.agents:
            try:
                v3_result = self.agents['super_v3'].decide(macro_data, tech_data, klines_df, price)
                signals['super_v3'] = v3_result['signal']
                logger.info(f"🚀 SuperV3: {v3_result['signal']:+.2f}")
            except Exception as e:
                logger.error(f"V3失败: {e}")
        
        # 3. Ultimate系统
        if 'ultimate' in self.agents:
            try:
                ult_result = self.agents['ultimate'].analyze(klines_df, macro_data)
                signals['ultimate'] = ult_result['signal']
                logger.info(f"⚡ Ultimate: {ult_result['signal']:+.2f}")
            except Exception as e:
                logger.error(f"Ultimate失败: {e}")
        
        # 4. Elite系统
        if 'elite' in self.agents:
            try:
                elite_result = self.agents['elite'].analyze(klines_df, macro_data)
                signals['elite'] = elite_result['signal']
                logger.info(f"🏆 Elite: {elite_result['signal']:+.2f}")
            except Exception as e:
                logger.error(f"Elite失败: {e}")
        
        # GOD MODE权重分配
        weights = {
            'base': 0.15,
            'super_v3': 0.25,
            'ultimate': 0.30,  # 最高权重
            'elite': 0.30      # 最高权重
        }
        
        # 归一化权重
        available_weights = {k: v for k, v in weights.items() if k in signals}
        total_weight = sum(available_weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in available_weights.items()}
        
        # 加权信号
        final_signal = sum(signals[k] * weights.get(k, 0) for k in signals.keys())
        
        # 共识度
        signal_values = list(signals.values())
        consensus = 1 - (np.std(signal_values) / 2) if len(signal_values) > 1 else 0.5
        
        # 置信度
        confidence = (abs(final_signal) + consensus) / 2
        
        # 动态杠杆
        if confidence >= 0.90:
            leverage = 20  # 极高置信度
        elif confidence >= 0.80:
            leverage = 15
        elif confidence >= 0.70:
            leverage = 12
        elif confidence >= 0.60:
            leverage = 10
        else:
            leverage = 8
        
        logger.info(f"\n🔥 GOD MODE 最终决策:")
        logger.info(f"   信号: {final_signal:+.2f}")
        logger.info(f"   置信度: {confidence:.1%}")
        logger.info(f"   共识度: {consensus:.1%}")
        logger.info(f"   杠杆: {leverage}x")
        logger.info(f"   系统数: {len(signals)}")
        
        # 交易条件 (更激进)
        should_trade = (
            confidence >= 0.55 and
            abs(final_signal) >= 0.25 and
            consensus >= 0.50
        )
        
        if should_trade:
            logger.info("   ✅ GOD MODE: 开火!")
        else:
            logger.info("   ⏸️  GOD MODE: 等待更好机会")
        
        return {
            'should_trade': should_trade,
            'signal': final_signal,
            'confidence': confidence,
            'consensus': consensus,
            'leverage': leverage,
            'all_signals': signals,
            'reason': '🔥 GOD MODE' if should_trade else '⏸️ 信号不足'
        }
