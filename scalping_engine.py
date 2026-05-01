"""
5分钟快进快出交易引擎
目标：5-15分钟内平仓，追求高胜率
"""
import logging
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
from agent_16_scalping_system import Agent16ScalpingSystem
import config

logger = logging.getLogger(__name__)


class ScalpingEngine:
    """短线交易引擎"""

    def __init__(self, okx_client, risk_manager):
        self.okx_client = okx_client
        self.risk_manager = risk_manager
        self.agent_system = Agent16ScalpingSystem()

        # 交易参数
        self.timeframe = getattr(config, 'ENTRY_TIMEFRAME', '5m')
        self.entry_threshold = max(0.58, getattr(config, 'MIN_CONFIDENCE', 0.58))
        self.exit_threshold = 0.3

        # 持仓跟踪
        self.active_positions = {}  # {position_id: position_info}
        self.trade_history = []

        # 性能指标
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0

        logger.info("✅ 短线交易引擎已初始化（5分钟周期）")

    async def get_klines(self, inst_id: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据"""
        try:
            klines = await self.okx_client.get_klines(inst_id, self.timeframe, limit)
            if not klines:
                return None

            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df[['open', 'high', 'low', 'close', 'volume']] = df[
                ['open', 'high', 'low', 'close', 'volume']
            ].astype(float)

            return df

        except Exception as e:
            logger.error(f"❌ 获取K线失败: {e}")
            return None

    async def analyze_and_trade(self, inst_id: str, current_price: float) -> Dict:
        """分析并执行交易"""

        # 获取K线数据
        klines_df = await self.get_klines(inst_id, limit=100)
        if klines_df is None or len(klines_df) < 20:
            logger.warning("⚠️ K线数据不足")
            return {'action': 'skip', 'reason': 'K线数据不足'}

        # 16个Agent讨论
        analysis = self.agent_system.analyze(klines_df, current_price)

        logger.info(f"\n{'='*60}")
        logger.info(f"📊 16-Agent讨论结果 (5分钟周期)")
        logger.info(f"{'='*60}")
        logger.info(f"最终决策: {analysis['action']}")
        logger.info(f"综合信号: {analysis['signal']:.2f}")
        logger.info(f"信心度: {analysis['confidence']:.1%}")
        logger.info(f"做多Agent: {analysis['long_count']}/16")
        logger.info(f"做空Agent: {analysis['short_count']}/16")
        logger.info(f"中性Agent: {analysis['neutral_count']}/16")

        # 显示各Agent意见
        logger.info(f"\n🤖 各Agent意见:")
        for decision in analysis['decisions']:
            action = "做多" if decision.signal > 0 else "做空" if decision.signal < 0 else "中性"
            logger.info(
                f"  • {decision.agent_name}: {action} "
                f"(信号{decision.signal:.2f}, 信心{decision.confidence:.1%}) - {decision.reason}"
            )

        # 执行交易决策
        if self.active_positions:
            await self.check_exit_conditions(inst_id, klines_df, current_price)
            return {'action': 'hold', 'reason': '已有持仓，先管理风险'}

        if analysis.get('tradeable') and analysis['confidence'] >= self.entry_threshold:
            if analysis['action'] == '做多':
                return await self.execute_long(inst_id, analysis)
            elif analysis['action'] == '做空':
                return await self.execute_short(inst_id, analysis)

        # 检查平仓条件
        await self.check_exit_conditions(inst_id, klines_df, current_price)

        return {'action': 'hold', 'reason': analysis.get('reason_summary', '信号不足，继续观察')}

    async def execute_long(self, inst_id: str, analysis: Dict) -> Dict:
        """执行做多"""
        logger.info(f"\n🟢 执行做多信号")

        account = await self.okx_client.get_account_balance()
        if not account:
            return {'action': 'failed', 'reason': '无法获取账户信息'}

        leverage = int(analysis.get('leverage', getattr(config, 'BASE_LEVERAGE', 6)))

        # 计算仓位
        position_info = self.risk_manager.calculate_scalping_position_size(
            account,
            price=analysis['entry_price'],
            leverage=leverage,
            stop_loss_price=analysis['stop_loss'],
            take_profit_price=analysis['take_profit'],
            position_size_pct=analysis.get('position_size_pct', getattr(config, 'POSITION_SIZE_PCT', 0.1)),
            confidence=analysis.get('confidence', 0.0),
        )

        if not position_info:
            return {'action': 'failed', 'reason': '仓位计算失败'}

        if getattr(config, 'SIGNAL_ONLY', True):
            logger.info("📡 SIGNAL_ONLY 已开启，跳过真实下单，仅输出做多信号")
            logger.info(f"   建议入场: ${analysis['entry_price']:.2f}")
            logger.info(f"   建议止损: ${position_info['stop_loss']:.2f}")
            logger.info(f"   建议止盈: ${position_info['take_profit']:.2f}")
            logger.info(f"   建议杠杆: {leverage}x")
            logger.info(f"   建议仓位: {analysis.get('position_size_pct', 0):.0%}")
            return {'action': 'long_signal', 'position_info': position_info, 'simulated': True}

        # 下单
        order = await self.okx_client.place_order(
            inst_id=inst_id,
            side='buy',
            order_type='market',
            size=position_info['size'],
            leverage=leverage
        )

        if order and order.get('order_id'):
            position_id = order['order_id']
            self.active_positions[position_id] = {
                'side': 'long',
                'entry_price': analysis['entry_price'],
                'entry_time': datetime.now(),
                'size': position_info['size'],
                'oz_size': position_info['oz_size'],
                'stop_loss': position_info['stop_loss'],
                'take_profit': position_info['take_profit'],
                'confidence': analysis['confidence'],
                'leverage': leverage,
                'position_usage': position_info['position_usage'],
                'risk_reward': analysis.get('risk_reward'),
            }

            logger.info(f"✅ 做多订单已下达")
            logger.info(f"   订单ID: {position_id}")
            logger.info(f"   数量: {position_info['size']}")
            logger.info(f"   入场价: ${analysis['entry_price']:.2f}")
            logger.info(f"   止损: ${position_info['stop_loss']:.2f}")
            logger.info(f"   止盈: ${position_info['take_profit']:.2f}")
            logger.info(f"   杠杆: {leverage}x")
            logger.info(f"   仓位占用: {position_info['position_usage']:.1%}")

            return {'action': 'long', 'order_id': position_id, 'position_info': position_info}
        else:
            return {'action': 'failed', 'reason': '下单失败'}

    async def execute_short(self, inst_id: str, analysis: Dict) -> Dict:
        """执行做空"""
        logger.info(f"\n🔴 执行做空信号")

        account = await self.okx_client.get_account_balance()
        if not account:
            return {'action': 'failed', 'reason': '无法获取账户信息'}

        leverage = int(analysis.get('leverage', getattr(config, 'BASE_LEVERAGE', 6)))

        # 计算仓位
        position_info = self.risk_manager.calculate_scalping_position_size(
            account,
            price=analysis['entry_price'],
            leverage=leverage,
            stop_loss_price=analysis['stop_loss'],
            take_profit_price=analysis['take_profit'],
            position_size_pct=analysis.get('position_size_pct', getattr(config, 'POSITION_SIZE_PCT', 0.1)),
            confidence=analysis.get('confidence', 0.0),
        )

        if not position_info:
            return {'action': 'failed', 'reason': '仓位计算失败'}

        if getattr(config, 'SIGNAL_ONLY', True):
            logger.info("📡 SIGNAL_ONLY 已开启，跳过真实下单，仅输出做空信号")
            logger.info(f"   建议入场: ${analysis['entry_price']:.2f}")
            logger.info(f"   建议止损: ${position_info['stop_loss']:.2f}")
            logger.info(f"   建议止盈: ${position_info['take_profit']:.2f}")
            logger.info(f"   建议杠杆: {leverage}x")
            logger.info(f"   建议仓位: {analysis.get('position_size_pct', 0):.0%}")
            return {'action': 'short_signal', 'position_info': position_info, 'simulated': True}

        # 下单
        order = await self.okx_client.place_order(
            inst_id=inst_id,
            side='sell',
            order_type='market',
            size=position_info['size'],
            leverage=leverage
        )

        if order and order.get('order_id'):
            position_id = order['order_id']
            self.active_positions[position_id] = {
                'side': 'short',
                'entry_price': analysis['entry_price'],
                'entry_time': datetime.now(),
                'size': position_info['size'],
                'oz_size': position_info['oz_size'],
                'stop_loss': position_info['stop_loss'],
                'take_profit': position_info['take_profit'],
                'confidence': analysis['confidence'],
                'leverage': leverage,
                'position_usage': position_info['position_usage'],
                'risk_reward': analysis.get('risk_reward'),
            }

            logger.info(f"✅ 做空订单已下达")
            logger.info(f"   订单ID: {position_id}")
            logger.info(f"   数量: {position_info['size']}")
            logger.info(f"   入场价: ${analysis['entry_price']:.2f}")
            logger.info(f"   止损: ${position_info['stop_loss']:.2f}")
            logger.info(f"   止盈: ${position_info['take_profit']:.2f}")
            logger.info(f"   杠杆: {leverage}x")
            logger.info(f"   仓位占用: {position_info['position_usage']:.1%}")

            return {'action': 'short', 'order_id': position_id, 'position_info': position_info}
        else:
            return {'action': 'failed', 'reason': '下单失败'}

    async def check_exit_conditions(self, inst_id: str, klines_df: pd.DataFrame, current_price: float):
        """检查平仓条件"""

        for position_id, position in list(self.active_positions.items()):
            # 检查持仓时间（最多15分钟）
            hold_time = (datetime.now() - position['entry_time']).total_seconds() / 60
            if hold_time > 15:
                logger.warning(f"⏰ 持仓超过15分钟，执行强制平仓")
                await self.close_position(inst_id, position_id, position, current_price, "时间止损")
                continue

            # 检查止损
            if position['side'] == 'long' and current_price <= position['stop_loss']:
                logger.warning(f"🛑 触发止损，执行平仓")
                await self.close_position(inst_id, position_id, position, current_price, "止损")
                continue

            if position['side'] == 'short' and current_price >= position['stop_loss']:
                logger.warning(f"🛑 触发止损，执行平仓")
                await self.close_position(inst_id, position_id, position, current_price, "止损")
                continue

            # 检查止盈
            if position['side'] == 'long' and current_price >= position['take_profit']:
                logger.info(f"✅ 触发止盈，执行平仓")
                await self.close_position(inst_id, position_id, position, current_price, "止盈")
                continue

            if position['side'] == 'short' and current_price <= position['take_profit']:
                logger.info(f"✅ 触发止盈，执行平仓")
                await self.close_position(inst_id, position_id, position, current_price, "止盈")
                continue

    async def close_position(self, inst_id: str, position_id: str, position: Dict,
                            current_price: float, reason: str):
        """平仓"""

        side = 'sell' if position['side'] == 'long' else 'buy'

        order = await self.okx_client.place_order(
            inst_id=inst_id,
            side=side,
            order_type='market',
            size=position['size']
        )

        if order:
            notional_size = position.get('oz_size', position['size'])
            pnl = (current_price - position['entry_price']) * notional_size
            if position['side'] == 'short':
                pnl = -pnl

            self.total_trades += 1
            if pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1

            self.total_pnl += pnl

            logger.info(f"✅ 平仓成功 ({reason})")
            logger.info(f"   平仓价: ${current_price:.2f}")
            logger.info(f"   盈亏: ${pnl:.2f}")
            logger.info(f"   持仓时间: {(datetime.now() - position['entry_time']).total_seconds() / 60:.1f}分钟")

            del self.active_positions[position_id]

    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0

        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'avg_pnl_per_trade': self.total_pnl / self.total_trades if self.total_trades > 0 else 0,
        }
