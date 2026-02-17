"""
风险管理模块 - 增强版 V2
新增功能：
1. VaR/CVaR风险度量
2. 动态杠杆调整（基于波动率）
3. 极端行情熔断机制
4. 流动性风险评估
5. 最大杠杆降至10x
"""
import logging
from typing import Dict, Optional, List, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import deque
import config

logger = logging.getLogger(__name__)


class RiskManagerEnhancedV2:
    """增强版风险管理器 V2"""

    # 风控参数
    MAX_LEVERAGE = 10  # 降低最大杠杆：20x → 10x
    MIN_LEVERAGE = 1
    BASE_LEVERAGE = 5

    # VaR参数
    VAR_CONFIDENCE = 0.95  # 95%置信度
    CVAR_CONFIDENCE = 0.95  # 95%置信度
    VAR_WINDOW = 100  # 历史窗口

    # 熔断参数
    CIRCUIT_BREAKER_LOSS = 0.08  # 单日亏损8%触发熔断
    CIRCUIT_BREAKER_VOLATILITY = 0.05  # 波动率超5%触发熔断
    CIRCUIT_BREAKER_COOLDOWN = 3600  # 熔断冷却1小时

    # 流动性参数
    MIN_LIQUIDITY_SCORE = 0.6  # 最低流动性评分

    def __init__(self):
        self.positions = {}
        self.pyramid_count = {}
        self.trade_history = deque(maxlen=200)  # 保留最近200笔交易
        self.returns_history = deque(maxlen=self.VAR_WINDOW)  # 收益率历史
        self.circuit_breaker_triggered = False
        self.circuit_breaker_time = None
        self.daily_start_equity = None
        self.volatility_cache = {}

    def calculate_var_cvar(self, returns: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """
        计算VaR和CVaR

        Args:
            returns: 收益率序列
            confidence: 置信度

        Returns:
            (VaR, CVaR)
        """
        if len(returns) < 30:
            return 0.0, 0.0

        returns_array = np.array(returns)

        # VaR: 历史模拟法
        var = np.percentile(returns_array, (1 - confidence) * 100)

        # CVaR: 超过VaR的平均损失
        cvar_losses = returns_array[returns_array <= var]
        cvar = np.mean(cvar_losses) if len(cvar_losses) > 0 else var

        return var, cvar

    def calculate_volatility(self, klines_df: pd.DataFrame, window: int = 20) -> float:
        """
        计算历史波动率（年化）

        Args:
            klines_df: K线数据
            window: 计算窗口

        Returns:
            年化波动率
        """
        try:
            if len(klines_df) < window:
                return 0.02  # 默认2%

            # 计算对数收益率
            returns = np.log(klines_df['close'] / klines_df['close'].shift(1))

            # 计算标准差（年化）
            volatility = returns.tail(window).std() * np.sqrt(365 * 24)  # 小时K线

            return volatility

        except Exception as e:
            logger.error(f"❌ 波动率计算失败: {e}")
            return 0.02

    def calculate_dynamic_leverage(self, klines_df: pd.DataFrame, base_leverage: int = None) -> int:
        """
        动态杠杆调整（基于波动率）

        规则：
        - 低波动率（<2%）：使用最大杠杆
        - 中波动率（2-4%）：使用基础杠杆
        - 高波动率（>4%）：降低杠杆

        Args:
            klines_df: K线数据
            base_leverage: 基础杠杆

        Returns:
            调整后的杠杆倍数
        """
        if base_leverage is None:
            base_leverage = self.BASE_LEVERAGE

        volatility = self.calculate_volatility(klines_df)

        if volatility < 0.02:
            # 低波动：使用最大杠杆
            leverage = self.MAX_LEVERAGE
            logger.info(f"📊 低波动率 {volatility:.2%} → 杠杆 {leverage}x")
        elif volatility < 0.04:
            # 中波动：使用基础杠杆
            leverage = base_leverage
            logger.info(f"📊 中波动率 {volatility:.2%} → 杠杆 {leverage}x")
        else:
            # 高波动：降低杠杆
            leverage = max(self.MIN_LEVERAGE, base_leverage // 2)
            logger.info(f"⚠️ 高波动率 {volatility:.2%} → 降低杠杆至 {leverage}x")

        return min(leverage, self.MAX_LEVERAGE)

    def check_circuit_breaker(self, account: Dict, klines_df: pd.DataFrame = None) -> Dict:
        """
        熔断机制检查

        触发条件：
        1. 单日亏损超过8%
        2. 市场波动率超过5%
        3. 连续3笔交易亏损

        Args:
            account: 账户信息
            klines_df: K线数据

        Returns:
            {'triggered': bool, 'reason': str, 'cooldown_remaining': int}
        """
        # 检查冷却期
        if self.circuit_breaker_triggered:
            if self.circuit_breaker_time:
                elapsed = (datetime.now() - self.circuit_breaker_time).total_seconds()
                if elapsed < self.CIRCUIT_BREAKER_COOLDOWN:
                    remaining = int(self.CIRCUIT_BREAKER_COOLDOWN - elapsed)
                    return {
                        'triggered': True,
                        'reason': '熔断冷却中',
                        'cooldown_remaining': remaining
                    }
                else:
                    # 冷却结束，解除熔断
                    self.circuit_breaker_triggered = False
                    self.circuit_breaker_time = None
                    logger.info("✅ 熔断冷却结束，恢复交易")

        # 1. 检查单日亏损
        if self.daily_start_equity:
            daily_loss = (account['total_equity'] - self.daily_start_equity) / self.daily_start_equity
            if daily_loss < -self.CIRCUIT_BREAKER_LOSS:
                self._trigger_circuit_breaker(f"单日亏损 {daily_loss:.2%} 超过阈值 {self.CIRCUIT_BREAKER_LOSS:.2%}")
                return {
                    'triggered': True,
                    'reason': f'单日亏损 {daily_loss:.2%}',
                    'cooldown_remaining': self.CIRCUIT_BREAKER_COOLDOWN
                }

        # 2. 检查市场波动率
        if klines_df is not None and len(klines_df) > 20:
            volatility = self.calculate_volatility(klines_df)
            if volatility > self.CIRCUIT_BREAKER_VOLATILITY:
                self._trigger_circuit_breaker(f"市场波动率 {volatility:.2%} 超过阈值 {self.CIRCUIT_BREAKER_VOLATILITY:.2%}")
                return {
                    'triggered': True,
                    'reason': f'极端波动 {volatility:.2%}',
                    'cooldown_remaining': self.CIRCUIT_BREAKER_COOLDOWN
                }

        # 3. 检查连续亏损
        if len(self.trade_history) >= 3:
            recent_trades = list(self.trade_history)[-3:]
            if all(t['pnl'] < 0 for t in recent_trades):
                total_loss = sum(t['pnl'] for t in recent_trades)
                self._trigger_circuit_breaker(f"连续3笔亏损，累计 ${total_loss:.2f}")
                return {
                    'triggered': True,
                    'reason': '连续亏损',
                    'cooldown_remaining': self.CIRCUIT_BREAKER_COOLDOWN
                }

        return {'triggered': False, 'reason': '', 'cooldown_remaining': 0}

    def _trigger_circuit_breaker(self, reason: str):
        """触发熔断"""
        self.circuit_breaker_triggered = True
        self.circuit_breaker_time = datetime.now()
        logger.warning(f"🚨 触发熔断机制: {reason}")
        logger.warning(f"⏰ 冷却时间: {self.CIRCUIT_BREAKER_COOLDOWN}秒")

    def assess_liquidity(self, klines_df: pd.DataFrame, window: int = 20) -> Dict:
        """
        流动性风险评估

        指标：
        1. 成交量稳定性
        2. 买卖价差（模拟）
        3. 市场深度（模拟）

        Args:
            klines_df: K线数据
            window: 评估窗口

        Returns:
            {'score': float, 'risk_level': str, 'can_trade': bool}
        """
        try:
            if len(klines_df) < window:
                return {'score': 0.5, 'risk_level': '未知', 'can_trade': True}

            recent_data = klines_df.tail(window)

            # 1. 成交量稳定性（变异系数）
            volume_cv = recent_data['volume'].std() / recent_data['volume'].mean()
            volume_score = max(0, 1 - volume_cv)  # CV越小越好

            # 2. 价格波动性（作为流动性代理指标）
            price_volatility = recent_data['close'].pct_change().std()
            volatility_score = max(0, 1 - price_volatility * 10)  # 波动越小越好

            # 3. 综合评分
            liquidity_score = (volume_score * 0.6 + volatility_score * 0.4)

            # 风险等级
            if liquidity_score >= 0.8:
                risk_level = '低'
            elif liquidity_score >= 0.6:
                risk_level = '中'
            else:
                risk_level = '高'

            can_trade = liquidity_score >= self.MIN_LIQUIDITY_SCORE

            logger.info(f"💧 流动性评估: 评分={liquidity_score:.2f}, 风险={risk_level}, 可交易={can_trade}")

            return {
                'score': liquidity_score,
                'risk_level': risk_level,
                'can_trade': can_trade,
                'volume_score': volume_score,
                'volatility_score': volatility_score
            }

        except Exception as e:
            logger.error(f"❌ 流动性评估失败: {e}")
            return {'score': 0.5, 'risk_level': '未知', 'can_trade': True}

    def calculate_kelly_fraction(self, win_rate: float = None, avg_win: float = None,
                                 avg_loss: float = None) -> float:
        """Kelly公式计算最优仓位"""
        try:
            if win_rate is None:
                if len(self.trade_history) < 10:
                    return 0.20  # 默认20%

                trades = list(self.trade_history)
                wins = [t['pnl'] for t in trades if t['pnl'] > 0]
                losses = [abs(t['pnl']) for t in trades if t['pnl'] < 0]

                if not wins or not losses:
                    return 0.20

                win_rate = len(wins) / len(trades)
                avg_win = np.mean(wins)
                avg_loss = np.mean(losses)

            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1
            kelly = win_rate - (1 - win_rate) / win_loss_ratio

            # Kelly折半（保守）
            kelly = max(0, min(kelly * 0.5, 0.4))

            logger.info(f"📊 Kelly: 胜率={win_rate:.1%}, 盈亏比={win_loss_ratio:.2f}, Kelly={kelly:.1%}")
            return kelly

        except Exception as e:
            logger.error(f"❌ Kelly计算失败: {e}")
            return 0.20

    def calculate_atr(self, klines_df: pd.DataFrame, period: int = 14) -> float:
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

    def calculate_position_size(self, account: Dict, price: float, klines_df: pd.DataFrame = None,
                               stop_loss_pct: float = 0.10, use_kelly: bool = True) -> Optional[Dict]:
        """
        计算仓位 - 集成所有风控功能

        Args:
            account: 账户信息
            price: 当前价格
            klines_df: K线数据
            stop_loss_pct: 止损百分比
            use_kelly: 是否使用Kelly公式

        Returns:
            仓位信息或None
        """
        # 1. 熔断检查
        circuit_breaker = self.check_circuit_breaker(account, klines_df)
        if circuit_breaker['triggered']:
            logger.warning(f"🚨 熔断中，无法开仓: {circuit_breaker['reason']}")
            return None

        # 2. 流动性检查
        if klines_df is not None and len(klines_df) > 20:
            liquidity = self.assess_liquidity(klines_df)
            if not liquidity['can_trade']:
                logger.warning(f"⚠️ 流动性不足，无法开仓: 评分={liquidity['score']:.2f}")
                return None

        # 3. 动态杠杆
        if klines_df is not None and len(klines_df) > 20:
            leverage = self.calculate_dynamic_leverage(klines_df)
        else:
            leverage = self.BASE_LEVERAGE

        # 4. Kelly仓位
        if use_kelly:
            kelly_fraction = self.calculate_kelly_fraction()
            position_fraction = kelly_fraction
        else:
            position_fraction = 0.25

        # 5. ATR动态止损
        if klines_df is not None and len(klines_df) > 20:
            atr = self.calculate_atr(klines_df)
            if atr > 0:
                atr_stop_pct = (atr * 2) / price
                stop_loss_pct = min(stop_loss_pct, atr_stop_pct)
                logger.info(f"📊 ATR动态止损: {atr:.2f} → {stop_loss_pct:.1%}")

        # 6. 计算仓位
        available = account['available']
        CONTRACT_SIZE = 0.001

        margin_to_use = min(available * 0.9, account['total_equity'] * position_fraction)
        oz_size = (margin_to_use * leverage) / price
        contracts = int(oz_size / CONTRACT_SIZE)

        if contracts < 1:
            logger.warning(f"⚠️ 计算合约张数 {contracts} 小于最小值 1")
            return None

        oz_size = contracts * CONTRACT_SIZE
        margin_needed = (oz_size * price) / leverage
        stop_loss = price * (1 - stop_loss_pct)
        take_profit = price * (1 + stop_loss_pct * 3)
        actual_risk = oz_size * price * stop_loss_pct / leverage

        # 7. VaR/CVaR计算
        var, cvar = 0.0, 0.0
        if len(self.returns_history) >= 30:
            var, cvar = self.calculate_var_cvar(list(self.returns_history))
            logger.info(f"📊 VaR(95%): {var:.2%}, CVaR(95%): {cvar:.2%}")

        logger.info(f"💰 仓位: {position_fraction:.1%}, {contracts}张, {leverage}x")
        logger.info(f"💰 风险: ${actual_risk:.2f} ({actual_risk/account['total_equity']*100:.1f}%)")

        return {
            'size': contracts,
            'oz_size': oz_size,
            'margin': margin_needed,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_amount': actual_risk,
            'leverage': leverage,
            'atr': self.calculate_atr(klines_df) if klines_df is not None else 0,
            'var': var,
            'cvar': cvar,
            'kelly_fraction': position_fraction
        }

    def update_trailing_stop(self, position: Dict, current_price: float,
                            klines_df: pd.DataFrame = None) -> Optional[float]:
        """ATR移动止损"""
        entry_price = float(position.get('avgPx', 0))
        size = float(position.get('pos', 0))

        atr = None
        if klines_df is not None and len(klines_df) > 20:
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

    def record_trade(self, pnl: float, return_pct: float = None):
        """记录交易"""
        self.trade_history.append({
            'pnl': pnl,
            'timestamp': datetime.now()
        })

        if return_pct is not None:
            self.returns_history.append(return_pct)

    def set_daily_start_equity(self, equity: float):
        """设置每日起始权益"""
        self.daily_start_equity = equity
        logger.info(f"📊 设置每日起始权益: ${equity:.2f}")

    def check_pyramid_condition(self, position: Dict, current_price: float) -> bool:
        """检查加仓条件"""
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
        """记录持仓"""
        self.positions[inst_id] = position_data
        if inst_id not in self.pyramid_count:
            self.pyramid_count[inst_id] = 0

    def increment_pyramid_count(self, inst_id: str):
        """增加加仓次数"""
        self.pyramid_count[inst_id] = self.pyramid_count.get(inst_id, 0) + 1

    def clear_position(self, inst_id: str):
        """清除持仓记录"""
        if inst_id in self.positions:
            del self.positions[inst_id]
        if inst_id in self.pyramid_count:
            del self.pyramid_count[inst_id]

    def check_risk_limits(self, account: Dict, daily_start_equity: float) -> Dict:
        """检查风险限制"""
        daily_pnl_pct = (account['total_equity'] - daily_start_equity) / daily_start_equity

        if daily_pnl_pct < -config.MAX_DAILY_LOSS:
            return {'can_trade': False, 'reason': f"达到单日最大亏损"}

        if account['available'] < account['total_equity'] * 0.1:
            return {'can_trade': False, 'reason': f"可用资金不足"}

        return {'can_trade': True, 'reason': ''}

    def get_risk_report(self, account: Dict) -> Dict:
        """生成风险报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'account_equity': account['total_equity'],
            'circuit_breaker_active': self.circuit_breaker_triggered,
            'trade_count': len(self.trade_history),
            'position_count': len(self.positions)
        }

        # 交易统计
        if len(self.trade_history) > 0:
            trades = list(self.trade_history)
            pnls = [t['pnl'] for t in trades]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p < 0]

            report['win_rate'] = len(wins) / len(trades) if trades else 0
            report['avg_win'] = np.mean(wins) if wins else 0
            report['avg_loss'] = np.mean(losses) if losses else 0
            report['total_pnl'] = sum(pnls)

        # VaR/CVaR
        if len(self.returns_history) >= 30:
            var, cvar = self.calculate_var_cvar(list(self.returns_history))
            report['var_95'] = var
            report['cvar_95'] = cvar

        return report


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    rm = RiskManagerEnhancedV2()

    # 模拟账户
    account = {
        'total_equity': 1000,
        'available': 900,
        'margin_used': 100
    }

    # 模拟K线数据
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')
    klines_df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(100).cumsum() + 2800,
        'high': np.random.randn(100).cumsum() + 2810,
        'low': np.random.randn(100).cumsum() + 2790,
        'close': np.random.randn(100).cumsum() + 2800,
        'volume': np.random.randint(1000, 5000, 100)
    })

    rm.set_daily_start_equity(1000)

    # 测试仓位计算
    result = rm.calculate_position_size(account, 2800, klines_df)
    print(f"\n仓位: {result}")

    # 测试风险报告
    report = rm.get_risk_report(account)
    print(f"\n风险报告: {report}")
