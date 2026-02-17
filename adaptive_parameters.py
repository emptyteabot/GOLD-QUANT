"""
参数自适应系统
根据市场状态动态调整参数
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)


class AdaptiveParameters:
    """自适应参数管理器"""
    
    def __init__(self):
        # 默认参数
        self.base_params = {
            'confidence_threshold': 0.50,
            'signal_threshold': 0.20,
            'leverage': 10,
            'stop_loss_pct': 0.015,
            'position_size': 0.30
        }
        logger.info("✅ 参数自适应系统初始化")
    
    def adjust_for_market(self, market_state: dict) -> dict:
        """根据市场状态调整参数"""
        regime = market_state.get('regime', 'unknown')
        adx = market_state.get('adx', 20)
        volatility = market_state.get('volatility', 0.02)
        
        params = self.base_params.copy()
        
        # 趋势市
        if regime == 'trending' or adx > 25:
            params['confidence_threshold'] = 0.45  # 降低阈值
            params['signal_threshold'] = 0.15
            params['leverage'] = 15  # 提高杠杆
            params['stop_loss_pct'] = 0.020  # 放宽止损
            logger.info("📈 趋势市模式: 激进参数")
        
        # 震荡市
        elif regime == 'ranging' or adx < 20:
            params['confidence_threshold'] = 0.60  # 提高阈值
            params['signal_threshold'] = 0.25
            params['leverage'] = 8  # 降低杠杆
            params['stop_loss_pct'] = 0.012  # 收紧止损
            logger.info("📊 震荡市模式: 保守参数")
        
        # 高波动市
        elif volatility > 0.03:
            params['confidence_threshold'] = 0.55
            params['signal_threshold'] = 0.20
            params['leverage'] = 12
            params['stop_loss_pct'] = 0.025  # 放宽止损
            params['position_size'] = 0.20  # 减小仓位
            logger.info("💥 高波动市: 谨慎参数")
        
        # 低波动市
        elif volatility < 0.01:
            params['confidence_threshold'] = 0.48
            params['signal_threshold'] = 0.18
            params['leverage'] = 12
            params['stop_loss_pct'] = 0.010
            logger.info("😴 低波动市: 积极参数")
        
        else:
            logger.info("⚖️ 正常市场: 默认参数")
        
        return params
