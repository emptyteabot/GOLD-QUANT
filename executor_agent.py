"""
执行交易员 - Agent 3
白天推送信号 + 夜晚自动交易
"""
import logging
from datetime import datetime
from typing import Dict, Optional
import config
from feishu_notifier import send_signal_push, send_trade_execution

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """混合执行交易员"""
    
    def __init__(self, okx_client, risk_manager):
        self.okx_client = okx_client
        self.risk_manager = risk_manager
    
    def is_daytime(self) -> bool:
        """判断是否为白天模式（亚洲盘+伦敦早盘）"""
        current_hour = datetime.utcnow().hour
        return config.DAYTIME_START <= current_hour < config.DAYTIME_END
    
    def is_nighttime(self) -> bool:
        """判断是否为夜晚模式（纽约盘）"""
        current_hour = datetime.utcnow().hour
        return config.NIGHTTIME_START <= current_hour < config.NIGHTTIME_END
    
    async def execute_signal(self, signal_data: Dict, account: Dict, 
                            macro_score: float, auto_mode: bool = False) -> bool:
        """
        执行交易信号
        
        Args:
            signal_data: 技术分析信号
            account: 账户信息
            macro_score: 宏观评分
            auto_mode: 是否自动执行（夜晚模式）
        
        Returns:
            bool: 是否执行成功
        """
        # 判断信号方向
        signal = signal_data.get('signal', 0)
        if signal == 0:
            logger.info("⚪ 无交易信号")
            return False
        
        # 计算杠杆（根据宏观评分）
        leverage = self._calculate_leverage(macro_score, signal_data.get('signal_strength', 0))
        
        # 获取当前价格
        price = await self.okx_client.get_ticker(config.INST_ID)
        if not price:
            logger.error("❌ 无法获取价格")
            return False
        
        # 计算仓位
        position_calc = self.risk_manager.calculate_position_size(
            account, price, leverage, stop_loss_pct=0.10
        )
        
        if not position_calc:
            logger.error("❌ 仓位计算失败")
            return False
        
        # 准备信号数据
        signal_push_data = {
            'macro_score': macro_score,
            'dxy': signal_data.get('dxy', 0),
            'us10y': signal_data.get('us10y', 0),
            'vix': signal_data.get('vix', 0),
            'signal': signal,
            'signal_strength': signal_data.get('signal_strength', 0),
            'hurst': signal_data.get('hurst', 0.5),
            'adx': signal_data.get('adx', 0),
            'rsi': signal_data.get('rsi', 50),
            'ml_prob': signal_data.get('ml_prob', 0.5),
            'entry_price': price,
            'stop_loss': position_calc['stop_loss'],
            'take_profit': position_calc['take_profit'],
            'position_size': position_calc['size'],
            'leverage': leverage,
            'max_loss': position_calc['risk_amount'],
            'expected_profit': position_calc['risk_amount'] * 3,
            'risk_reward': 3.0
        }
        
        # 白天模式：推送信号
        if self.is_daytime() and not auto_mode:
            logger.info("🌅 白天模式：推送信号到飞书")
            send_signal_push(signal_push_data)
            return False  # 不自动执行
        
        # 夜晚模式：自动执行
        if self.is_nighttime() or auto_mode:
            logger.info("🌙 夜晚模式：自动执行交易")
            return await self._execute_trade(
                signal, price, position_calc, leverage, account
            )
        
        logger.info("⏸️ 非交易时段")
        return False
    
    async def _execute_trade(self, signal: int, price: float, 
                            position_calc: Dict, leverage: int, 
                            account: Dict) -> bool:
        """执行交易"""
        side = 'buy' if signal > 0 else 'sell'
        size = position_calc['size']  # 合约张数（整数）
        oz_size = position_calc['oz_size']  # 实际盎司数
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔥 执行{'做多' if side == 'buy' else '做空'}: {size} 张合约 ({oz_size:.3f} XAU) @ ${price:.2f}, {leverage}x")
        logger.info(f"{'='*80}")
        
        # 设置杠杆
        await self.okx_client.set_leverage(config.INST_ID, leverage)
        
        # 下单
        order = await self.okx_client.place_order(
            config.INST_ID, side, size, leverage
        )
        
        if order:
            logger.info("✅ 交易执行成功")
            
            # 记录持仓
            self.risk_manager.record_position(config.INST_ID, {
                'entry_price': price,
                'size': size,
                'oz_size': oz_size,
                'side': side,
                'leverage': leverage,
                'initial_risk': position_calc['risk_amount'],
                'stop_loss': position_calc['stop_loss'],
                'take_profit': position_calc['take_profit']
            })
            
            # 发送飞书通知
            send_trade_execution({
                'side': side,
                'size': oz_size,  # 显示盎司数
                'contracts': size,  # 显示合约张数
                'price': price,
                'leverage': leverage,
                'margin': position_calc['margin'],
                'stop_loss': position_calc['stop_loss'],
                'take_profit': position_calc['take_profit'],
                'equity': account['total_equity'],
                'available': account['available'] - position_calc['margin'],
                'position_usage': position_calc['margin'] / account['total_equity']
            })
            
            return True
        else:
            logger.error("❌ 交易执行失败")
            return False
    
    def _calculate_leverage(self, macro_score: float, signal_strength: float) -> int:
        """
        动态计算杠杆
        
        规则：
        - Macro Score > 50: 10-15x（激进）
        - 0 < Macro Score < 50: 5-10x（保守）
        - Macro Score < 0: 3-5x（防守）
        """
        if macro_score > config.MACRO_BULL_THRESHOLD:
            # 激进模式
            base_leverage = 12
            if signal_strength > 0.8:
                leverage = 15
            elif signal_strength > 0.6:
                leverage = 12
            else:
                leverage = 10
        elif macro_score > config.MACRO_NEUTRAL_THRESHOLD:
            # 保守模式
            base_leverage = 7
            if signal_strength > 0.8:
                leverage = 10
            elif signal_strength > 0.6:
                leverage = 7
            else:
                leverage = 5
        else:
            # 防守模式
            leverage = 3
        
        # 限制在配置范围内
        leverage = max(config.MIN_LEVERAGE, min(leverage, config.MAX_LEVERAGE))
        
        logger.info(f"📊 动态杠杆: {leverage}x (宏观评分{macro_score:.0f}, 信号强度{signal_strength:.0%})")
        
        return leverage
    
    async def monitor_positions(self, price: float, technical_data: Dict) -> bool:
        """
        监控持仓（止盈止损 + 浮盈加仓）
        
        Args:
            price: 当前价格
            technical_data: 技术分析数据
        
        Returns:
            bool: 是否有操作
        """
        positions = await self.okx_client.get_positions(config.INST_ID)
        
        if not positions:
            return False
        
        for position in positions:
            inst_id = position['instId']
            size = float(position['pos'])
            entry_price = float(position['avgPx'])
            unrealized_pnl = float(position['upl'])
            
            logger.info(f"\n📊 监控持仓: {'多' if size > 0 else '空'}{abs(size):.3f} XAU @ ${entry_price:.2f}")
            logger.info(f"   当前价格: ${price:.2f}")
            logger.info(f"   浮动盈亏: ${unrealized_pnl:.2f}")
            
            # 获取止损止盈价格
            position_info = self.risk_manager.positions.get(inst_id, {})
            stop_loss = position_info.get('stop_loss', 0)
            take_profit = position_info.get('take_profit', 0)
            
            # 检查止损
            if size > 0 and stop_loss > 0 and price <= stop_loss:
                logger.warning(f"⚠️ 触发止损！${price:.2f} <= ${stop_loss:.2f}")
                await self._close_position(inst_id, size, price, "止损")
                return True
            elif size < 0 and stop_loss > 0 and price >= stop_loss:
                logger.warning(f"⚠️ 触发止损！${price:.2f} >= ${stop_loss:.2f}")
                await self._close_position(inst_id, size, price, "止损")
                return True
            
            # 检查止盈
            if size > 0 and take_profit > 0 and price >= take_profit:
                logger.info(f"✅ 触发止盈！${price:.2f} >= ${take_profit:.2f}")
                await self._close_position(inst_id, size, price, "止盈")
                return True
            elif size < 0 and take_profit > 0 and price <= take_profit:
                logger.info(f"✅ 触发止盈！${price:.2f} <= ${take_profit:.2f}")
                await self._close_position(inst_id, size, price, "止盈")
                return True
            
            # 检查浮盈加仓条件
            if config.PYRAMIDING_ENABLED:
                adx = technical_data.get('adx', 0)
                if adx > 30 and self.risk_manager.check_pyramid_condition(position, price):
                    logger.info("🔥 满足浮盈加仓条件！")
                    # TODO: 执行加仓
                    return True
            
            # 更新移动止损
            atr = technical_data.get('atr', None)
            new_stop = self.risk_manager.update_trailing_stop(position, price, atr)
            # TODO: 更新止损单
        
        return False
    
    async def _close_position(self, inst_id: str, size: float, price: float, reason: str) -> bool:
        """
        平仓
        
        Args:
            inst_id: 合约ID
            size: 持仓数量（正数=多，负数=空）
            price: 当前价格
            reason: 平仓原因
        
        Returns:
            bool: 是否成功
        """
        side = 'sell' if size > 0 else 'buy'  # 平多用sell，平空用buy
        abs_size = int(abs(size))
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔥 执行平仓 ({reason}): {abs_size} 张合约 @ ${price:.2f}")
        logger.info(f"{'='*80}")
        
        # 下平仓单
        order = await self.okx_client.place_order(
            inst_id, side, abs_size, leverage=1, reduce_only=True
        )
        
        if order:
            logger.info(f"✅ 平仓成功 ({reason})")
            
            # 清除持仓记录
            if inst_id in self.risk_manager.positions:
                position_info = self.risk_manager.positions[inst_id]
                entry_price = position_info.get('entry_price', 0)
                pnl = (price - entry_price) * abs_size * 0.001 if size > 0 else (entry_price - price) * abs_size * 0.001
                
                # 发送飞书通知
                from feishu_notifier import send_feishu
                send_feishu(
                    f"**🔔 平仓通知 ({reason})**\n\n"
                    f"合约: {inst_id}\n"
                    f"方向: {'多' if size > 0 else '空'}\n"
                    f"数量: {abs_size} 张\n"
                    f"开仓价: ${entry_price:.2f}\n"
                    f"平仓价: ${price:.2f}\n"
                    f"盈亏: ${pnl:.2f}\n"
                    f"原因: {reason}",
                    level="info"
                )
                
                del self.risk_manager.positions[inst_id]
            
            return True
        else:
            logger.error(f"❌ 平仓失败 ({reason})")
            return False


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    executor = ExecutorAgent(None, None)
    
    print(f"当前时间: {datetime.utcnow().hour} UTC")
    print(f"白天模式: {executor.is_daytime()}")
    print(f"夜晚模式: {executor.is_nighttime()}")

