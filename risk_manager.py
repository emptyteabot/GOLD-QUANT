"""
风险管理模块 - 浮盈加仓 + 止损止盈
"""
import logging
from typing import Dict, Optional, List
import config

logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器"""
    
    def __init__(self):
        self.positions = {}  # 记录持仓信息
        self.pyramid_count = {}  # 记录加仓次数
    
    def calculate_position_size(self, account: Dict, price: float, leverage: int, 
                                stop_loss_pct: float = 0.10) -> Dict:
        """
        计算仓位大小（基于1R风险单元）
        
        Args:
            account: 账户信息
            price: 入场价格
            leverage: 杠杆倍数
            stop_loss_pct: 止损百分比（默认10%）
        
        Returns:
            dict: {'size': int, 'margin': float, 'stop_loss': float, 'take_profit': float}
        """
        available = account['available']
        
        # 风险单元：账户权益 × 5%
        risk_amount = account['total_equity'] * config.RISK_PER_TRADE
        
        # 🔧 OKX黄金合约：1张 = 0.001盎司
        CONTRACT_SIZE = 0.001
        
        # 简化计算：直接用可用资金的90%开仓
        margin_to_use = min(available * 0.9, account['total_equity'] * 0.3)  # 最多用30%权益
        
        # 计算能开多少盎司：保证金 × 杠杆 / 价格
        oz_size = (margin_to_use * leverage) / price
        
        # 转换为合约张数
        contracts = oz_size / CONTRACT_SIZE
        
        # 向下取整
        import math
        contracts = math.floor(contracts)
        
        # 重新计算实际使用的保证金和盎司数
        oz_size = contracts * CONTRACT_SIZE
        margin_needed = (oz_size * price) / leverage
        
        
        # 检查最小下单量（1张合约）
        if contracts < 1:
            logger.warning(f"⚠️ 计算合约张数 {contracts:.2f} 小于最小值 1")
            logger.warning(f"   可用资金: ${available:.2f}")
            logger.warning(f"   使用保证金: ${margin_to_use:.2f}")
            logger.warning(f"   杠杆: {leverage}x")
            logger.warning(f"   价格: ${price:.2f}")
            return None
        
        # 计算止损止盈价格
        stop_loss = price * (1 - stop_loss_pct)
        take_profit = price * (1 + stop_loss_pct * 3)  # 盈亏比3:1
        
        # 计算实际风险金额
        actual_risk = oz_size * price * stop_loss_pct / leverage
        
        logger.info(f"\n💰 仓位计算:")
        logger.info(f"   账户权益: ${account['total_equity']:.2f}")
        logger.info(f"   可用资金: ${available:.2f}")
        logger.info(f"   使用保证金: ${margin_needed:.2f}")
        logger.info(f"   合约张数: {contracts} 张")
        logger.info(f"   实际盎司: {oz_size:.3f} XAU")
        logger.info(f"   杠杆: {leverage}x")
        logger.info(f"   实际风险: ${actual_risk:.2f} ({actual_risk/account['total_equity']*100:.1f}%)")
        logger.info(f"   止损: ${stop_loss:.2f} (-{stop_loss_pct:.0%})")
        logger.info(f"   止盈: ${take_profit:.2f} (+{stop_loss_pct*3:.0%})")
        
        return {
            'size': contracts,  # 返回合约张数（整数）
            'oz_size': oz_size,  # 实际盎司数
            'margin': margin_needed,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_amount': actual_risk
        }
    
    def calculate_scalping_position_size(
        self,
        account: Dict,
        price: float,
        leverage: int,
        stop_loss_price: float,
        take_profit_price: float,
        position_size_pct: float,
        confidence: float = 0.0,
    ) -> Dict:
        """Size a short-term trade from stop distance first, then margin cap."""
        available = float(account['available'])
        total_equity = float(account['total_equity'])
        contract_size = 0.001

        if available <= 0 or total_equity <= 0:
            logger.warning("Scalping position blocked: no available capital or invalid equity.")
            return None

        risk_multiplier = 0.5 + max(0.0, min(confidence, 1.0)) * 0.5
        risk_amount = total_equity * config.RISK_PER_TRADE * risk_multiplier

        margin_cap_ratio = max(0.0, min(position_size_pct, config.MAX_TOTAL_POSITION))
        if margin_cap_ratio <= 0:
            logger.warning("Scalping position blocked: non-positive margin cap ratio.")
            return None
        margin_to_use = min(available * margin_cap_ratio, total_equity * config.MAX_TOTAL_POSITION)

        stop_distance = abs(price - stop_loss_price)
        stop_distance = max(stop_distance, price * 0.001)

        risk_based_oz = risk_amount / stop_distance
        margin_based_oz = (margin_to_use * leverage) / price
        oz_size = min(risk_based_oz, margin_based_oz)

        import math
        contracts = math.floor(oz_size / contract_size)
        if contracts < 1:
            logger.warning("Scalping position too small after risk sizing.")
            return None

        oz_size = contracts * contract_size
        margin_needed = (oz_size * price) / leverage
        actual_risk = oz_size * stop_distance
        position_usage = margin_needed / total_equity if total_equity else 0.0

        return {
            'size': contracts,
            'oz_size': oz_size,
            'margin': margin_needed,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
            'risk_amount': actual_risk,
            'leverage': leverage,
            'position_usage': position_usage,
            'stop_distance': stop_distance,
        }

    def check_pyramid_condition(self, position: Dict, current_price: float) -> bool:
        """
        检查是否满足浮盈加仓条件
        
        条件：
        1. 浮盈 >= 1R
        2. ADX > 30（趋势加速）
        3. 未超过最大加仓次数
        
        Args:
            position: 持仓信息
            current_price: 当前价格
        
        Returns:
            bool: 是否可以加仓
        """
        if not config.PYRAMIDING_ENABLED:
            return False
        
        inst_id = position.get('instId')
        entry_price = float(position.get('avgPx', 0))
        size = float(position.get('pos', 0))
        
        # 检查加仓次数
        pyramid_count = self.pyramid_count.get(inst_id, 0)
        if pyramid_count >= len(config.PYRAMID_LEVELS) - 1:
            logger.info(f"⚠️ 已达到最大加仓次数 {pyramid_count}")
            return False
        
        # 计算浮盈（以R为单位）
        if size > 0:  # 多单
            pnl = (current_price - entry_price) * size
        else:  # 空单
            pnl = (entry_price - current_price) * abs(size)
        
        # 获取初始风险单元（从记录中）
        initial_risk = self.positions.get(inst_id, {}).get('initial_risk', 0)
        if initial_risk == 0:
            logger.warning("⚠️ 无法获取初始风险单元")
            return False
        
        pnl_in_r = pnl / initial_risk
        
        logger.info(f"📊 浮盈检查: {pnl_in_r:.2f}R (需要 >= {config.PYRAMID_MIN_PROFIT_R}R)")
        
        if pnl_in_r >= config.PYRAMID_MIN_PROFIT_R:
            logger.info(f"✅ 满足加仓条件！当前浮盈 {pnl_in_r:.2f}R")
            return True
        
        return False
    
    def calculate_pyramid_size(self, inst_id: str, base_size: float) -> float:
        """
        计算加仓大小（正金字塔）
        
        Args:
            inst_id: 合约ID
            base_size: 底仓大小
        
        Returns:
            float: 加仓大小
        """
        pyramid_count = self.pyramid_count.get(inst_id, 0)
        
        if pyramid_count >= len(config.PYRAMID_LEVELS) - 1:
            return 0
        
        # 下一次加仓比例
        next_ratio = config.PYRAMID_LEVELS[pyramid_count + 1]
        pyramid_size = base_size * next_ratio
        
        logger.info(f"📊 加仓计算: 第{pyramid_count + 1}次加仓，比例{next_ratio:.0%}，大小{pyramid_size:.3f} XAU")
        
        return pyramid_size
    
    def update_trailing_stop(self, position: Dict, current_price: float, 
                            atr: float = None) -> Optional[float]:
        """
        更新移动止损
        
        Args:
            position: 持仓信息
            current_price: 当前价格
            atr: ATR值（用于动态止损距离）
        
        Returns:
            float: 新的止损价格
        """
        entry_price = float(position.get('avgPx', 0))
        size = float(position.get('pos', 0))
        
        # 默认止损距离：ATR的2倍，或价格的5%
        if atr:
            stop_distance = atr * 2
        else:
            stop_distance = current_price * 0.05
        
        if size > 0:  # 多单
            # 止损价 = 当前价 - 止损距离
            new_stop = current_price - stop_distance
            
            # 确保止损不低于入场价（保本）
            new_stop = max(new_stop, entry_price)
        else:  # 空单
            # 止损价 = 当前价 + 止损距离
            new_stop = current_price + stop_distance
            
            # 确保止损不高于入场价（保本）
            new_stop = min(new_stop, entry_price)
        
        logger.info(f"📊 移动止损: ${new_stop:.2f}")
        
        return new_stop
    
    def record_position(self, inst_id: str, position_data: Dict):
        """记录持仓信息"""
        self.positions[inst_id] = position_data
        if inst_id not in self.pyramid_count:
            self.pyramid_count[inst_id] = 0
    
    def increment_pyramid_count(self, inst_id: str):
        """增加加仓次数"""
        self.pyramid_count[inst_id] = self.pyramid_count.get(inst_id, 0) + 1
        logger.info(f"📊 加仓次数: {self.pyramid_count[inst_id]}/{len(config.PYRAMID_LEVELS)-1}")
    
    def clear_position(self, inst_id: str):
        """清除持仓记录"""
        if inst_id in self.positions:
            del self.positions[inst_id]
        if inst_id in self.pyramid_count:
            del self.pyramid_count[inst_id]
        logger.info(f"📊 已清除 {inst_id} 的持仓记录")
    
    def check_risk_limits(self, account: Dict, daily_start_equity: float) -> Dict:
        """
        检查风险限制
        
        Returns:
            dict: {'can_trade': bool, 'reason': str}
        """
        # 检查单日最大亏损
        daily_pnl = account['total_equity'] - daily_start_equity
        daily_pnl_pct = daily_pnl / daily_start_equity
        
        if daily_pnl_pct < -config.MAX_DAILY_LOSS:
            return {
                'can_trade': False,
                'reason': f"达到单日最大亏损{config.MAX_DAILY_LOSS:.0%}（当前{daily_pnl_pct:.1%}）"
            }
        
        # 检查可用资金
        if account['available'] < account['total_equity'] * 0.1:
            return {
                'can_trade': False,
                'reason': f"可用资金不足（仅剩{account['available']:.2f}）"
            }
        
        return {'can_trade': True, 'reason': ''}


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    rm = RiskManager()
    
    # 测试仓位计算
    account = {
        'total_equity': 1000,
        'available': 900,
        'margin_used': 100
    }
    
    result = rm.calculate_position_size(account, 4500, 10)
    print(f"\n仓位: {result}")

