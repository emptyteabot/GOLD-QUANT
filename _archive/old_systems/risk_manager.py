"""
风险管理系统 - 专业版
基于Kelly公式、VaR、动态止损
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime


class RiskManager:
    """
    风险管理器
    
    功能：
    1. Kelly公式计算最优仓位
    2. VaR/CVaR风险度量
    3. 动态止损止盈
    4. 最大回撤控制
    5. 风险预算分配
    """
    
    def __init__(
        self,
        initial_capital: float = 100000,
        max_position_size: float = 0.3,  # 最大仓位30%
        max_single_loss: float = 0.02,  # 单笔最大亏损2%
        max_daily_loss: float = 0.05,  # 日内最大亏损5%
        max_drawdown: float = 0.10,  # 最大回撤10%
        var_confidence: float = 0.95,  # VaR置信度
        atr_stop_multiplier: float = 2.0,  # ATR止损倍数
        use_kelly: bool = True  # 使用Kelly公式
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_size = max_position_size
        self.max_single_loss = max_single_loss
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.var_confidence = var_confidence
        self.atr_stop_multiplier = atr_stop_multiplier
        self.use_kelly = use_kelly
        
        # 状态
        self.positions = {}
        self.daily_pnl = 0
        self.peak_capital = initial_capital
        self.current_drawdown = 0
        
        # 历史
        self.pnl_history = []
        self.capital_history = [initial_capital]
        
    def calculate_kelly_fraction(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Kelly公式计算最优仓位
        
        Kelly% = W - (1-W)/R
        W = 胜率
        R = 盈亏比 (平均盈利/平均亏损)
        
        Args:
            win_rate: 胜率
            avg_win: 平均盈利
            avg_loss: 平均亏损（正数）
        
        Returns:
            Kelly仓位比例 (0-1)
        """
        if avg_loss == 0:
            return 0
        
        R = avg_win / avg_loss
        kelly = win_rate - (1 - win_rate) / R
        
        # Kelly公式可能给出负值或过大值，需要限制
        kelly = max(0, min(kelly, self.max_position_size))
        
        # 使用半Kelly或1/4 Kelly更保守
        kelly = kelly * 0.5  # 半Kelly
        
        return kelly
    
    def calculate_position_size(
        self,
        signal_strength: float,
        price: float,
        atr: float,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ) -> Dict:
        """
        计算仓位大小
        
        Args:
            signal_strength: 信号强度 (0-1)
            price: 当前价格
            atr: ATR值
            win_rate: 历史胜率
            avg_win: 平均盈利
            avg_loss: 平均亏损
        
        Returns:
            {
                'position_size': float,  # 仓位大小（资金）
                'shares': int,  # 股数
                'position_pct': float,  # 仓位比例
                'stop_loss': float,  # 止损价
                'take_profit': float  # 止盈价
            }
        """
        # 1. 基础仓位（基于信号强度）
        base_position = signal_strength * self.max_position_size
        
        # 2. Kelly调整
        if self.use_kelly and win_rate and avg_win and avg_loss:
            kelly_fraction = self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)
            base_position = min(base_position, kelly_fraction)
        
        # 3. 波动率调整
        # 波动率高 → 减小仓位
        volatility = atr / price
        vol_adjusted_position = base_position * (0.02 / volatility)  # 目标波动率2%
        vol_adjusted_position = min(vol_adjusted_position, self.max_position_size)
        
        # 4. 风险预算调整
        # 确保单笔亏损不超过max_single_loss
        risk_per_trade = self.current_capital * self.max_single_loss
        stop_distance = atr * self.atr_stop_multiplier
        max_position_by_risk = risk_per_trade / stop_distance
        
        # 5. 最终仓位
        position_size = min(
            vol_adjusted_position * self.current_capital,
            max_position_by_risk
        )
        
        shares = int(position_size / price)
        actual_position_size = shares * price
        position_pct = actual_position_size / self.current_capital
        
        # 6. 止损止盈
        stop_loss = price - stop_distance
        take_profit = price + stop_distance * 2  # 盈亏比2:1
        
        return {
            'position_size': actual_position_size,
            'shares': shares,
            'position_pct': position_pct,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_amount': stop_distance * shares
        }
    
    def calculate_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95,
        method: str = 'historical'
    ) -> float:
        """
        计算VaR (Value at Risk)
        
        Args:
            returns: 收益率序列
            confidence: 置信度
            method: 'historical' or 'parametric'
        
        Returns:
            VaR值（正数表示潜在亏损）
        """
        if len(returns) == 0:
            return 0
        
        if method == 'historical':
            # 历史模拟法
            var = -np.percentile(returns, (1 - confidence) * 100)
        else:
            # 参数法（假设正态分布）
            mean = returns.mean()
            std = returns.std()
            from scipy import stats
            z_score = stats.norm.ppf(confidence)
            var = -(mean - z_score * std)
        
        return var
    
    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        计算CVaR (Conditional VaR / Expected Shortfall)
        
        超过VaR的平均损失
        
        Args:
            returns: 收益率序列
            confidence: 置信度
        
        Returns:
            CVaR值
        """
        if len(returns) == 0:
            return 0
        
        var = self.calculate_var(returns, confidence)
        # CVaR = 超过VaR的损失的平均值
        cvar = -returns[returns < -var].mean()
        
        return cvar if not np.isnan(cvar) else var
    
    def check_risk_limits(self) -> Dict:
        """
        检查风险限制
        
        Returns:
            {
                'can_trade': bool,
                'daily_loss_ok': bool,
                'drawdown_ok': bool,
                'position_limit_ok': bool,
                'warnings': List[str]
            }
        """
        warnings = []
        
        # 1. 检查日内亏损
        daily_loss_pct = abs(self.daily_pnl) / self.current_capital
        daily_loss_ok = daily_loss_pct < self.max_daily_loss
        
        if not daily_loss_ok:
            warnings.append(f'日内亏损超限: {daily_loss_pct:.2%} > {self.max_daily_loss:.2%}')
        
        # 2. 检查回撤
        self.current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        drawdown_ok = self.current_drawdown < self.max_drawdown
        
        if not drawdown_ok:
            warnings.append(f'回撤超限: {self.current_drawdown:.2%} > {self.max_drawdown:.2%}')
        
        # 3. 检查仓位
        total_position = sum([pos['size'] for pos in self.positions.values()])
        position_pct = total_position / self.current_capital
        position_limit_ok = position_pct < self.max_position_size
        
        if not position_limit_ok:
            warnings.append(f'仓位超限: {position_pct:.2%} > {self.max_position_size:.2%}')
        
        can_trade = daily_loss_ok and drawdown_ok and position_limit_ok
        
        return {
            'can_trade': can_trade,
            'daily_loss_ok': daily_loss_ok,
            'drawdown_ok': drawdown_ok,
            'position_limit_ok': position_limit_ok,
            'warnings': warnings,
            'daily_loss_pct': daily_loss_pct,
            'current_drawdown': self.current_drawdown,
            'position_pct': position_pct
        }
    
    def update_capital(self, pnl: float):
        """更新资金"""
        self.current_capital += pnl
        self.daily_pnl += pnl
        
        # 更新峰值
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        # 记录历史
        self.pnl_history.append(pnl)
        self.capital_history.append(self.current_capital)
    
    def reset_daily_pnl(self):
        """重置日内盈亏"""
        self.daily_pnl = 0
    
    def get_risk_metrics(self) -> Dict:
        """
        获取风险指标
        
        Returns:
            完整的风险指标
        """
        if len(self.pnl_history) == 0:
            return {}
        
        pnl_series = pd.Series(self.pnl_history)
        capital_series = pd.Series(self.capital_history)
        
        # 收益率
        returns = capital_series.pct_change().dropna()
        
        # 基础指标
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital
        
        # 风险指标
        var_95 = self.calculate_var(returns, 0.95)
        cvar_95 = self.calculate_cvar(returns, 0.95)
        
        # 夏普比率
        if returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252)  # 年化
        else:
            sharpe = 0
        
        # 最大回撤
        cummax = capital_series.cummax()
        drawdown = (capital_series - cummax) / cummax
        max_dd = drawdown.min()
        
        # Calmar比率
        calmar = total_return / abs(max_dd) if max_dd != 0 else 0
        
        return {
            'current_capital': self.current_capital,
            'total_return': total_return,
            'total_pnl': self.current_capital - self.initial_capital,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'current_drawdown': self.current_drawdown,
            'calmar_ratio': calmar,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'win_rate': len([p for p in self.pnl_history if p > 0]) / len(self.pnl_history) if self.pnl_history else 0,
            'profit_factor': sum([p for p in self.pnl_history if p > 0]) / abs(sum([p for p in self.pnl_history if p < 0])) if sum([p for p in self.pnl_history if p < 0]) != 0 else 0
        }


# ==================== 测试 ====================

def test_risk_manager():
    """测试风险管理器"""
    print("\n" + "=" * 70)
    print("🧪 测试风险管理系统")
    print("=" * 70)
    
    rm = RiskManager(
        initial_capital=100000,
        max_position_size=0.3,
        max_single_loss=0.02,
        use_kelly=True
    )
    
    print("\n1️⃣ 测试Kelly公式...")
    kelly = rm.calculate_kelly_fraction(win_rate=0.6, avg_win=100, avg_loss=50)
    print(f"   Kelly仓位: {kelly:.2%}")
    
    print("\n2️⃣ 测试仓位计算...")
    position = rm.calculate_position_size(
        signal_strength=0.8,
        price=2650,
        atr=20,
        win_rate=0.6,
        avg_win=100,
        avg_loss=50
    )
    print(f"   仓位大小: ${position['position_size']:,.0f}")
    print(f"   股数: {position['shares']}")
    print(f"   仓位比例: {position['position_pct']:.2%}")
    print(f"   止损价: ${position['stop_loss']:.2f}")
    print(f"   止盈价: ${position['take_profit']:.2f}")
    
    print("\n3️⃣ 测试VaR计算...")
    returns = pd.Series(np.random.randn(100) * 0.02)
    var = rm.calculate_var(returns, 0.95)
    cvar = rm.calculate_cvar(returns, 0.95)
    print(f"   VaR(95%): {var:.2%}")
    print(f"   CVaR(95%): {cvar:.2%}")
    
    print("\n4️⃣ 测试风险限制...")
    # 模拟一些交易
    rm.update_capital(1000)
    rm.update_capital(-500)
    rm.update_capital(2000)
    
    risk_check = rm.check_risk_limits()
    print(f"   可以交易: {risk_check['can_trade']}")
    print(f"   日内亏损: {risk_check['daily_loss_pct']:.2%}")
    print(f"   当前回撤: {risk_check['current_drawdown']:.2%}")
    
    print("\n5️⃣ 测试风险指标...")
    metrics = rm.get_risk_metrics()
    print(f"   当前资金: ${metrics['current_capital']:,.0f}")
    print(f"   总收益率: {metrics['total_return']:.2%}")
    print(f"   夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"   最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"   胜率: {metrics['win_rate']:.2%}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_risk_manager()



