"""
风险管理模块 - 增强版
新增: Kelly公式仓位管理 + ATR动态止损
"""
import logging
from typing import Dict, Optional
import numpy as np
import config

logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器 - 增强版"""
    
    def __init__(self):
        self.positions = {}
        self.pyramid_count = {}
        self.trade_history = []
    
    def calculate_kelly_fraction(self, win_rate: float = None, avg_win: float = None, avg_loss: float = None) -> float:
        """Kelly公式计算最优仓位"""
        try:
            if win_rate is None:
                if len(self.trade_history) < 10:
                    return 0.25
                
                wins = [t['pnl'] for t in self.trade_history if t['pnl'] > 0]
                losses = [abs(t['pnl']) for t in self.trade_history if t['pnl'] < 0]
                
                if not wins or not losses:
                    return 0.25
                
                win_rate = len(wins) / len(self.trade_history)
                avg_win = np.mean(wins)
                avg_loss = np.mean(losses)
            
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1
            kelly = win_rate - (1 - win_rate) / win_loss_ratio
            kelly = max(0, min(kelly * 0.5, 0.5))
            
            logger.info(f"📊 Kelly: 胜率={win_rate:.1%}, 盈亏比={win_loss_ratio:.2f}, Kelly={kelly:.1%}")
            return kelly
            
        except Exception as e:
            logger.error(f"❌ Kelly计算失败: {e}")
            return 0.25
    
    def calculate_atr(self, klines_df, period=14) -> float:
        """计算ATR"""
        try:
            df = klines_df.tail(period + 1).copy()
            df['h-l'] = df['high'] - df['low']
            df['h-pc'] = abs(df['high'] - df['close'].shift(1))
            df['l-pc'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
            atr = df['tr'].rolling(period).mean().iloc[-1]
            return atr
        except Exception as e:
            logger.error(f"❌ ATR计算失败: {e}")
            return 0
    
    def calculate_position_size(self, account: Dict, price: float, leverage: int, 
                                stop_loss_pct: float = 0.10, klines_df=None, use_kelly=True) -> Dict:
        """计算仓位 - Kelly + ATR增强"""
        available = account['available']
        
        if use_kelly:
            kelly_fraction = self.calculate_kelly_fraction()
            position_fraction = kelly_fraction
        else:
            position_fraction = 0.30
        
        if klines_df is not None and len(klines_df) > 20:
            atr = self.calculate_atr(klines_df)
            if atr > 0:
                atr_stop_pct = (atr * 2) / price
                stop_loss_pct = min(stop_loss_pct, atr_stop_pct)
                logger.info(f"📊 ATR动态止损: {atr:.2f} → {stop_loss_pct:.1%}")
        
        CONTRACT_SIZE = 0.001
        margin_to_use = min(available * 0.9, account['total_equity'] * position_fraction)
        oz_size = (margin_to_use * leverage) / price
        contracts = int(oz_size / CONTRACT_SIZE)
        
        if contracts < 1:
            return None
        
        oz_size = contracts * CONTRACT_SIZE
        margin_needed = (oz_size * price) / leverage
        stop_loss = price * (1 - stop_loss_pct)
        take_profit = price * (1 + stop_loss_pct * 3)
        actual_risk = oz_size * price * stop_loss_pct / leverage
        
        logger.info(f"💰 仓位 (Kelly): {position_fraction:.1%}, {contracts}张, {leverage}x")
        logger.info(f"💰 仓位 (Kelly): {position_fraction:.1%}, {contracts}张, {leverage}x")
        
        return {
            'size': contracts,
            'oz_size': oz_size,
            'margin': margin_needed,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_amount': actual_risk,
            'atr': self.calculate_atr(klines_df) if klines_df is not None else 0
        }
    
    def update_trailing_stop(self, position: Dict, current_price: float, 
                            atr: float = None, klines_df=None) -> Optional[float]:
        """ATR移动止损"""
        entry_price = float(position.get('avgPx', 0))
        size = float(position.get('pos', 0))
        
        if atr is None and klines_df is not None:
            atr = self.calculate_atr(klines_df)
        
        if atr and atr > 0:
            stop_distance = atr * 2
        else:
            stop_distance = current_price * 0.05
        
        if size > 0:
            new_stop = max(current_price - stop_distance, entry_price)
        else:
            new_stop = min(current_price + stop_distance, entry_price)
        
        logger.info(f"📊 ATR止损: ${new_stop:.2f}")
        return new_stop
    
    def record_trade(self, pnl: float):
        """记录交易"""
        self.trade_history.append({'pnl': pnl})
        if len(self.trade_history) > 50:
            self.trade_history = self.trade_history[-50:]
    
    def check_pyramid_condition(self, position: Dict, current_price: float) -> bool:
        """检查加仓"""
        if not config.PYRAMIDING_ENABLED:
            return False
        inst_id = position.get('instId')
        entry_price = float(position.get('avgPx', 0))
        size = float(position.get('pos', 0))
        pyramid_count = self.pyramid_count.get(inst_id, 0)
        if pyramid_count >= len(config.PYRAMID_LEVELS) - 1:
            return False
        if size > 0:
            pnl = (current_price - entry_price) * size
        else:
            pnl = (entry_price - current_price) * abs(size)
        initial_risk = self.positions.get(inst_id, {}).get('initial_risk', 0)
        if initial_risk == 0:
            return False
        pnl_in_r = pnl / initial_risk
        return pnl_in_r >= config.PYRAMID_MIN_PROFIT_R
    
    def calculate_pyramid_size(self, inst_id: str, base_size: float) -> float:
        """计算加仓大小"""
        pyramid_count = self.pyramid_count.get(inst_id, 0)
        if pyramid_count >= len(config.PYRAMID_LEVELS) - 1:
            return 0
        return base_size * config.PYRAMID_LEVELS[pyramid_count + 1]
    
    def record_position(self, inst_id: str, position_data: Dict):
        self.positions[inst_id] = position_data
        if inst_id not in self.pyramid_count:
            self.pyramid_count[inst_id] = 0
    
    def increment_pyramid_count(self, inst_id: str):
        self.pyramid_count[inst_id] = self.pyramid_count.get(inst_id, 0) + 1
    
    def clear_position(self, inst_id: str):
        if inst_id in self.positions:
            del self.positions[inst_id]
        if inst_id in self.pyramid_count:
            del self.pyramid_count[inst_id]
    
    def check_risk_limits(self, account: Dict, daily_start_equity: float) -> Dict:
        daily_pnl_pct = (account['total_equity'] - daily_start_equity) / daily_start_equity
        if daily_pnl_pct < -config.MAX_DAILY_LOSS:
            return {'can_trade': False, 'reason': f"达到单日最大亏损"}
        if account['available'] < account['total_equity'] * 0.1:
            return {'can_trade': False, 'reason': f"可用资金不足"}
        return {'can_trade': True, 'reason': ''}
