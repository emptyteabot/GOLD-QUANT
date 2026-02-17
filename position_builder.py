"""
分批建仓系统
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class PositionBuilder:
    """分批建仓管理器"""
    
    def __init__(self):
        self.tranches = []  # 分批记录
        logger.info("✅ 分批建仓系统初始化")
    
    def calculate_tranches(self, signal_strength: float, total_size: float) -> List[Dict]:
        """计算分批方案"""
        tranches = []
        
        if signal_strength >= 0.95:
            # 极强信号: 3批
            tranches = [
                {'size': total_size * 0.5, 'threshold': 0.80},
                {'size': total_size * 0.3, 'threshold': 0.90},
                {'size': total_size * 0.2, 'threshold': 0.95}
            ]
            logger.info("🔥 极强信号: 3批建仓")
        
        elif signal_strength >= 0.85:
            # 强信号: 2批
            tranches = [
                {'size': total_size * 0.6, 'threshold': 0.75},
                {'size': total_size * 0.4, 'threshold': 0.85}
            ]
            logger.info("💪 强信号: 2批建仓")
        
        else:
            # 中等信号: 1批
            tranches = [
                {'size': total_size, 'threshold': signal_strength}
            ]
            logger.info("👌 中等信号: 1批建仓")
        
        return tranches
    
    def calculate_exit_tranches(self, profit_pct: float) -> Dict:
        """计算分批止盈"""
        if profit_pct >= 0.06:
            return {'action': 'close_all', 'ratio': 1.0}
        elif profit_pct >= 0.04:
            return {'action': 'close_partial', 'ratio': 0.5}
        elif profit_pct >= 0.02:
            return {'action': 'close_partial', 'ratio': 0.3}
        else:
            return {'action': 'hold', 'ratio': 0}
    
    def should_add_position(self, current_signal: float, entry_signal: float, profit_pct: float) -> bool:
        """是否应该加仓"""
        # 信号增强 + 有浮盈
        if current_signal > entry_signal + 0.1 and profit_pct > 0.01:
            logger.info("➕ 信号增强,建议加仓")
            return True
        return False
