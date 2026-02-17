"""
AURUM主程序 - 完整Multi-Agent黄金交易系统
整合：宏观 + 技术 + 机器学习 + XAUT策略
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config
from enhanced_macro_analyst import EnhancedMacroAnalyst
from technical_agent import TechnicalAnalyst
from executor_agent import ExecutorAgent
from risk_manager import RiskManager
from okx_client import OKXClient
from feishu_notifier import send_feishu, send_heartbeat
from complete_multi_agent import CompleteMultiAgentSystem
from multi_timeframe_monitor import MultiTimeframeMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AURUMSystem:
    """AURUM交易系统"""
    
    def __init__(self):
        # 初始化各个Agent
        self.macro_sentinel = EnhancedMacroAnalyst()
        self.technical_analyst = TechnicalAnalyst()
        self.okx_client = OKXClient()
        self.risk_manager = RiskManager()
        self.executor = ExecutorAgent(self.okx_client, self.risk_manager)
        self.multi_agent = CompleteMultiAgentSystem()  # 完整Multi-Agent系统
        self.mtf_monitor = MultiTimeframeMonitor()  # 多周期监控器
        
        # 系统状态
        self.daily_start_equity = 0
        self.last_heartbeat_time = None
        self.test_trade_executed = False
        self.stoploss_alert_state = {'last_time': None, 'fired_levels': set()}
        self.breakout_alert_state = {'last_time': None, 'fired_levels': set()}
        self.fakeout_alert_state = {'last_time': None, 'fired_levels': set()}
        self.exhaust_alert_state = {'last_time': None, 'fired_levels': set()}
        self.liq_alert_state = {'last_time': None, 'fired_levels': set()}
        self.last_gemini_time = None
    
    async def initialize(self) -> bool:
        """初始化系统"""
        logger.info("\n" + "="*80)
        logger.info("🔥 AURUM系统启动")
        logger.info("="*80)
        
        # 初始化OKX客户端
        await self.okx_client.initialize()
        
        # 查询合约信息
        logger.info("\n🔍 查询合约信息...")
        inst_info = await self.okx_client.get_instrument_info(config.INST_ID)
        if not inst_info:
            logger.error("❌ 无法获取合约信息，请检查合约代码")
            return False
        
        # 获取初始账户信息
        account = await self.okx_client.get_account_balance()
        if not account:
            logger.error("❌ 无法获取账户信息")
            return False
        
        self.daily_start_equity = account['total_equity']
        logger.info(f"\n💰 初始权益: ${self.daily_start_equity:.2f}")
        
        # 显示所有持仓
        logger.info("\n🔍 检查现有持仓...")
        all_positions = await self.okx_client.get_all_positions()
        
        position_summary = []
        
        # SWAP永续合约持仓
        if all_positions['swap_positions']:
            logger.info("\n📊 SWAP永续合约持仓:")
            for pos in all_positions['swap_positions']:
                inst_id = pos['instId']
                size = float(pos['pos'])
                avg_px = float(pos['avgPx'])
                upl = float(pos['upl'])
                upl_ratio = float(pos['uplRatio'])
                lever = pos['lever']
                
                direction = "做多" if size > 0 else "做空"
                logger.info(f"   {inst_id}: {direction} {abs(size)} @ ${avg_px:.2f}, {lever}x杠杆, 盈亏${upl:.2f} ({upl_ratio*100:.2f}%)")
                
                position_summary.append(
                    f"• **{inst_id}**: {direction} {abs(size)} @ ${avg_px:.2f}\n"
                    f"  杠杆{lever}x, 盈亏${upl:.2f} ({upl_ratio*100:.2f}%)"
                )
        else:
            logger.info("   ⚪ 无SWAP永续合约持仓")
        
        # 现货杠杆余额
        if all_positions['margin_balances']:
            logger.info("\n📊 现货杠杆余额:")
            for ccy, balance in all_positions['margin_balances'].items():
                if balance['equity'] > 0.01:
                    logger.info(f"   {ccy}: 权益{balance['equity']:.4f}, 可用{balance['available']:.4f}")
                    if balance['borrowed'] > 0:
                        logger.info(f"        借币{balance['borrowed']:.4f}, 利息{balance['interest']:.4f}")
                        position_summary.append(
                            f"• **{ccy}杠杆**: 权益{balance['equity']:.4f}, 借币{balance['borrowed']:.4f}"
                        )
        else:
            logger.info("   ⚪ 无现货杠杆余额")
        
        # 发送启动通知
        position_text = "\n".join(position_summary) if position_summary else "无持仓"
        
        send_feishu(
            f"**🚀 AURUM系统已启动**\n\n"
            f"**💰 初始权益：** ${self.daily_start_equity:.2f}（¥{self.daily_start_equity*config.CNY_RATE:.2f}）\n"
            f"**📊 合约：** {config.INST_ID}\n"
            f"**⏰ 时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"**📊 当前持仓：**\n{position_text}\n\n"
            f"**模式说明：**\n"
            f"• 白天（UTC 0-12）：推送信号，手动执行\n"
            f"• 夜晚（UTC 13-21）：自动交易\n"
            f"• 杠杆：{config.MIN_LEVERAGE}-{config.MAX_LEVERAGE}x动态调整\n"
            f"• 浮盈加仓：{'开启' if config.PYRAMIDING_ENABLED else '关闭'}",
            level="success",
            title="🚀 系统启动"
        )
        
        return True
    
    async def run(self):
        """主循环"""
        if not await self.initialize():
            return
        
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                
                logger.info("\n" + "="*80)
                logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {scan_count} 次扫描")
                logger.info("="*80)
                
                # 1. 获取账户信息
                account = await self.okx_client.get_account_balance()
                if not account:
                    logger.error("❌ 无法获取账户信息，60秒后重试")
                    await asyncio.sleep(60)
                    continue
                
                # 2. 获取当前价格
                price = await self.okx_client.get_ticker(config.INST_ID)
                if not price:
                    logger.error("❌ 无法获取价格，60秒后重试")
                    await asyncio.sleep(60)
                    continue
                
                logger.info(f"💰 当前价格: ${price:.2f}")
                logger.info(f"💰 可用资金: ${account['available']:.2f}")
                
                # 3. 风险检查
                risk_check = self.risk_manager.check_risk_limits(account, self.daily_start_equity)
                if not risk_check['can_trade']:
                    logger.warning(f"⚠️ 风控触发: {risk_check['reason']}")
                    send_feishu(
                        f"**⚠️ 风控触发**\n\n{risk_check['reason']}\n\n系统已停止交易",
                        level="warning"
                    )
                    await asyncio.sleep(300)
                    continue
                
                # 4. 监控持仓（止盈止损 + 浮盈加仓）
                positions = await self.okx_client.get_positions(config.INST_ID)
                if positions:
                    # 止损/强平距离提醒（只推送）
                    self._check_stop_loss_alert(price, positions)
                    self._check_liq_alert(price, positions)

                    # 获取技术数据用于加仓判断
                    klines = await self.okx_client.get_klines(config.INST_ID, config.EXIT_TIMEFRAME, 100)
                    if klines:
                        df = self._parse_klines(klines)
                        tech_result = self.technical_analyst.analyze(df, price)
                        await self.executor.monitor_positions(price, tech_result)
                
                # 5. 宏观分析
                if config.ENABLE_MACRO_ANALYSIS:
                    macro_result = self.macro_sentinel.calculate_enhanced_macro_score()
                    macro_score = macro_result['score']
                else:
                    logger.info("⚪ 宏观分析已禁用，使用默认评分")
                    macro_result = {'score': 0, 'dxy': None, 'us10y': None, 'vix': None}
                    macro_score = 0
                
                # 6. 多周期监控（15m/5m/1m）
                logger.info("\n🔍 多周期监控...")
                
                # 获取三个周期的K线
                klines_15m = await self.okx_client.get_klines(config.INST_ID, config.EXIT_TIMEFRAME, 300)
                klines_5m = await self.okx_client.get_klines(config.INST_ID, config.ENTRY_TIMEFRAME, config.ENTRY_LIMIT)
                klines_1m = await self.okx_client.get_klines(config.INST_ID, '1m', 60)
                klines_1h = await self.okx_client.get_klines(config.INST_ID, config.EXIT_ALT_TIMEFRAME, config.EXIT_LIMIT)
                klines_4h = await self.okx_client.get_klines(config.INST_ID, '4H', 120)
                
                if not klines_15m or not klines_5m or not klines_1m:
                    logger.error("❌ 无法获取K线数据")
                    await asyncio.sleep(60)
                    continue
                
                df_15m = self._parse_klines(klines_15m)
                df_5m = self._parse_klines(klines_5m)
                df_1m = self._parse_klines(klines_1m)
                df_1h = self._parse_klines(klines_1h) if klines_1h else None
                df_4h = self._parse_klines(klines_4h) if klines_4h else None

                # 突破/假突破/动能衰竭提醒（只推送）
                self._check_breakout_alert(price, df_5m)
                self._check_fakeout_alert(price, df_5m)
                self._check_exhaustion_alert(price, df_5m)
                
                # 多周期分析
                mtf_result = self.mtf_monitor.analyze_all_timeframes(
                    df_15m, df_5m, df_1m, price
                )
                
                # 🔥 紧急信号处理
                if mtf_result['crash_detected']:
                    logger.warning(f"\n🔴🔴🔴 暴跌检测！{mtf_result['reason']}")
                    logger.warning(f"   严重程度: {mtf_result['details']['crash']['severity']}/100")
                    
                    # 发送飞书警报
                    send_feishu(
                        f"**🔴 暴跌警报！**\n\n"
                        f"**原因：** {mtf_result['reason']}\n"
                        f"**严重程度：** {mtf_result['details']['crash']['severity']}/100\n"
                        f"**当前价格：** ${price:.2f}\n\n"
                        f"**建议：** 考虑做空或平多单",
                        level="danger",
                        title="🔴 暴跌警报"
                    )
                    
                    # 如果有多单，考虑平仓
                    if positions and positions[0]['side'] == 'long':
                        logger.warning("⚠️ 检测到暴跌，建议平仓多单！")
                        # 这里可以添加自动平仓逻辑
                
                elif mtf_result['reversal_detected']:
                    logger.info(f"\n🟢🟢🟢 反转检测！{mtf_result['reason']}")
                    logger.info(f"   置信度: {mtf_result['details']['reversal']['confidence']}/100")
                    
                    # 发送飞书通知
                    send_feishu(
                        f"**🟢 反转信号！**\n\n"
                        f"**原因：** {mtf_result['reason']}\n"
                        f"**置信度：** {mtf_result['details']['reversal']['confidence']}/100\n"
                        f"**当前价格：** ${price:.2f}\n\n"
                        f"**建议：** 考虑做多",
                        level="success",
                        title="🟢 反转信号"
                    )
                
                # 显示多周期状态
                logger.info(f"\n📊 多周期状态:")
                for tf in ['15m', '5m', '1m']:
                    if tf in mtf_result['details']:
                        data = mtf_result['details'][tf]
                        if 'error' not in data:
                            logger.info(
                                f"   {tf}: 涨跌{data['change_pct']:+.2f}%, "
                                f"RSI={data['rsi']:.1f}, ADX={data['adx']:.1f}"
                            )
                
                # 7. 技术分析（入场使用 3m 数据）
                df = df_5m
                tech_result = self.technical_analyst.analyze(df, price)
                
                # 8. 训练ML模型（每次扫描都训练，使用最新数据）
                if scan_count % 5 == 1:  # 每5次扫描训练一次，避免过于频繁
                    logger.info("🤖 训练机器学习模型...")
                    self.multi_agent.train_ml_model(df)
                
                # 9. 完整Multi-Agent决策（宏观+技术+ML+XAUT）
                decision = self.multi_agent.make_decision(macro_result, tech_result, df, price)

                # 9.1 出场提醒（15m / 1H）
                if positions:
                    exit_signals = self._check_exit_signals(positions, df_15m, df_1h, price)
                    if exit_signals:
                        send_feishu(
                            exit_signals,
                            level="warning",
                            title="Exit Signal"
                        )

                # 9.2 Gemini analysis (OKX indicators + account snapshot)
                await self._maybe_send_gemini_analysis(
                    price=price,
                    account=account,
                    positions=positions,
                    df_3m=df_5m,
                    df_15m=df_15m,
                    df_1h=df_1h,
                    df_4h=df_4h,
                    decision=decision
                )
                
                # 10. 检查是否应该交易
                if not decision['should_trade']:
                    logger.info(f"⚪ {decision['reason']}")
                    await asyncio.sleep(60)
                    continue
                
                # 11. 检查信号方向
                # 🔥 如果检测到暴跌，允许做空
                if mtf_result['crash_detected']:
                    logger.warning(f"\n🔥 暴跌模式：允许做空")
                    if decision['signal'] < -0.15:  # 做空信号
                        logger.info(f"\n🔴🔴🔴 发现高确定性做空机会！🔴🔴🔴")
                        logger.info(f"   最终信号: {decision['signal']:+.2f}")
                        logger.info(f"   置信度: {decision['confidence']:.1%}")
                        logger.info(f"   暴跌严重度: {mtf_result['details']['crash']['severity']}/100")
                        
                        # 这里可以添加做空逻辑
                        # TODO: 实现做空功能
                        logger.warning("⚠️ 做空功能待实现")
                    
                    await asyncio.sleep(60)
                    continue
                
                # 🟢 如果检测到反转，强化做多信号
                if mtf_result['reversal_detected']:
                    logger.info(f"\n🟢 反转模式：强化做多信号")
                    decision['signal'] += 0.2  # 增加信号强度
                    decision['confidence'] = min(1.0, decision['confidence'] + 0.1)
                
                # 常规Buy the Dip策略：只做多
                if decision['signal'] < 0.2:  # 信号太弱或做空
                    logger.info(f"⚪ 信号不足（信号={decision['signal']:+.2f}，Buy the Dip策略只做多）")
                    await asyncio.sleep(60)
                    continue
                
                # 12. 发现高确定性做多机会！
                logger.info(f"\n🔥🔥🔥 发现高确定性做多机会！🔥🔥🔥")
                logger.info(f"   最终信号: {decision['signal']:+.2f}")
                logger.info(f"   置信度: {decision['confidence']:.1%}")
                logger.info(f"   共识度: {decision['consensus']:.1%}")
                logger.info(f"   建议杠杆: {decision['leverage']}x")
                logger.info(f"\n🤖 各Agent投票:")
                for agent, signal in decision['agent_signals'].items():
                    logger.info(f"   {agent}: {signal:+.2f}")
                
                # 合并所有数据
                signal_data = {
                    **tech_result, 
                    **macro_result, 
                    'leverage': decision['leverage'], 
                    'confidence': decision['confidence'],
                    'ml_confidence': decision['ml_details']['confidence'],
                    'xaut_cascade': decision['xaut_details']['cascade_detected']
                }
                
                # 13. 执行交易（如果有信号且无持仓）
                if not positions:
                    # 测试模式：只执行一次
                    if config.TEST_MODE and self.test_trade_executed:
                        logger.info("🧪 测试模式：已执行过交易，跳过")
                    else:
                        success = await self.executor.execute_signal(
                            signal_data, account, macro_score
                        )
                        if success and config.TEST_MODE:
                            self.test_trade_executed = True
                            logger.warning("🧪 测试交易已执行")
                
                # 14. 定期心跳（每5分钟）
                if self._should_send_heartbeat():
                    positions = await self.okx_client.get_positions()
                    send_heartbeat(
                        {
                            'equity': account['total_equity'],
                            'available': account['available'],
                            'margin_used': account['margin_used'],
                            'price': price
                        },
                        positions
                    )
                    self.last_heartbeat_time = datetime.now()
                
                # 15. 等待下次扫描（1分钟）
                logger.info(f"\n⏰ 等待60秒后进行下次扫描...")
                await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("\n收到中断信号，正在关闭系统...")
        except Exception as e:
            logger.error(f"❌ 系统异常: {e}", exc_info=True)
            send_feishu(f"**❌ 系统异常**\n\n{str(e)}", level="danger")
        finally:
            await self.okx_client.close()
            logger.info("✅ 系统已关闭")
    
    def _parse_klines(self, klines: list) -> pd.DataFrame:
        """解析K线数据"""
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 
            'volume', 'volCcy', 'volCcyQuote', 'confirm'
        ])
        
        # 转换数据类型
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # OKX返回的是从新到旧，需要反转
        df = df.iloc[::-1].reset_index(drop=True)
        
        return df
    
    def _should_send_heartbeat(self) -> bool:
        """判断是否应该发送心跳"""
        if self.last_heartbeat_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_heartbeat_time).total_seconds()
        return elapsed >= 300  # 5分钟

    def _parse_levels(self, text: str) -> list:
        try:
            levels = []
            for part in str(text).split(','):
                part = part.strip()
                if not part:
                    continue
                levels.append(float(part))
            return sorted([lv for lv in levels if lv > 0])
        except Exception:
            return []

    def _check_stop_loss_alert(self, price: float, positions: list):
        """距离止损接近提醒（只推送）"""
        stop_price = getattr(config, 'STOP_LOSS_ALERT_PRICE', 0)
        if not stop_price or stop_price <= 0:
            return

        pos = next((p for p in positions if p.get('instId') == config.INST_ID), None)
        if not pos:
            return

        size = float(pos.get('pos', 0))
        if size == 0:
            return

        if size > 0:
            if price <= stop_price:
                if "HIT" not in self.stoploss_alert_state['fired_levels']:
                    send_feishu(
                        f"**⛔ 止损价已触达**\n\n"
                        f"**当前价：** ${price:.2f}\n"
                        f"**止损价：** ${stop_price:.2f}\n\n"
                        f"仅提醒，不自动交易。",
                        level="danger",
                        title="⛔ 止损触发提醒"
                    )
                    self.stoploss_alert_state['fired_levels'].add("HIT")
                return
            dist_pct = (price - stop_price) / price
        else:
            if price >= stop_price:
                if "HIT" not in self.stoploss_alert_state['fired_levels']:
                    send_feishu(
                        f"**⛔ 止损价已触达**\n\n"
                        f"**当前价：** ${price:.2f}\n"
                        f"**止损价：** ${stop_price:.2f}\n\n"
                        f"仅提醒，不自动交易。",
                        level="danger",
                        title="⛔ 止损触发提醒"
                    )
                    self.stoploss_alert_state['fired_levels'].add("HIT")
                return
            dist_pct = (stop_price - price) / price

        levels = self._parse_levels(getattr(config, 'STOP_LOSS_ALERT_LEVELS', ''))
        if not levels:
            return

        # 冷却
        last_time = self.stoploss_alert_state['last_time']
        if last_time is not None:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < config.STOP_LOSS_ALERT_COOLDOWN_MINUTES * 60:
                return

        for lv in levels:
            if dist_pct <= lv and lv not in self.stoploss_alert_state['fired_levels']:
                send_feishu(
                    f"**⚠️ 接近止损提醒**\n\n"
                    f"**当前价：** ${price:.2f}\n"
                    f"**止损价：** ${stop_price:.2f}\n"
                    f"**距离止损：** {dist_pct*100:.2f}%\n\n"
                    f"仅提醒，不自动交易。",
                    level="warning",
                    title="⚠️ 止损接近"
                )
                self.stoploss_alert_state['fired_levels'].add(lv)
                self.stoploss_alert_state['last_time'] = datetime.now()
                break

    def _check_liq_alert(self, price: float, positions: list):
        """强平距离提醒（只推送）"""
        levels = self._parse_levels(getattr(config, 'LIQ_ALERT_LEVELS', ''))
        if not levels:
            return

        pos = next((p for p in positions if p.get('instId') == config.INST_ID), None)
        if not pos:
            return

        liq_px = float(pos.get('liqPx') or 0)
        size = float(pos.get('pos', 0))
        if liq_px <= 0 or size == 0:
            return

        if size > 0:
            dist_pct = (price - liq_px) / price
        else:
            dist_pct = (liq_px - price) / price

        # 冷却
        last_time = self.liq_alert_state['last_time']
        if last_time is not None:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < config.LIQ_ALERT_COOLDOWN_MINUTES * 60:
                return

        for lv in levels:
            if dist_pct <= lv and lv not in self.liq_alert_state['fired_levels']:
                send_feishu(
                    f"**⛔ 强平距离预警**\n\n"
                    f"**当前价：** ${price:.2f}\n"
                    f"**强平价：** ${liq_px:.2f}\n"
                    f"**距离强平：** {dist_pct*100:.2f}%\n\n"
                    f"仅提醒，不自动交易。",
                    level="danger",
                    title="⛔ 强平距离预警"
                )
                self.liq_alert_state['fired_levels'].add(lv)
                self.liq_alert_state['last_time'] = datetime.now()
                break

    def _check_breakout_alert(self, price: float, df_5m: pd.DataFrame):
        """突破确认提醒（只推送）"""
        if df_5m is None or df_5m.empty:
            return
        levels = self._parse_levels(getattr(config, 'BREAKOUT_ALERT_LEVELS', ''))
        if not levels or len(df_5m) < 25:
            return

        confirm = max(1, int(getattr(config, 'BREAKOUT_CONFIRM_CANDLES', 2)))
        last = df_5m.iloc[-confirm:]

        # RSI/ADX
        delta = df_5m['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_now = float(rsi.iloc[-1])

        adx = df_5m['close'].rolling(14).std() / df_5m['close'].rolling(14).mean() * 100
        adx_now = float(adx.iloc[-1])

        vol_now = df_5m['volume'].iloc[-1]
        vol_ma = df_5m['volume'].rolling(20).mean().iloc[-1]
        vol_ok = vol_now > vol_ma * config.BREAKOUT_VOL_MULTIPLIER if vol_ma > 0 else False

        last_time = self.breakout_alert_state['last_time']
        if last_time is not None:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < config.BREAKOUT_ALERT_COOLDOWN_MINUTES * 60:
                return

        for lv in levels:
            if price < lv:
                continue
            if all(last['close'] >= lv) and rsi_now >= config.BREAKOUT_RSI_MIN and adx_now >= config.BREAKOUT_ADX_MIN and vol_ok:
                if lv in self.breakout_alert_state['fired_levels']:
                    continue
                send_feishu(
                    f"**🟢 突破确认**\n\n"
                    f"**价格：** ${price:.2f}\n"
                    f"**确认价位：** ${lv:.2f}\n"
                    f"**条件：** {confirm}根5m收盘站上 + 量能放大 + RSI/ADX确认\n"
                    f"RSI={rsi_now:.1f}, ADX={adx_now:.1f}\n\n"
                    f"仅提醒，不自动交易。",
                    level="success",
                    title="🟢 突破确认"
                )
                self.breakout_alert_state['fired_levels'].add(lv)
                self.breakout_alert_state['last_time'] = datetime.now()
                break

    def _check_fakeout_alert(self, price: float, df_5m: pd.DataFrame):
        """假突破提醒（只推送）"""
        if df_5m is None or df_5m.empty:
            return
        levels = self._parse_levels(getattr(config, 'BREAKOUT_ALERT_LEVELS', ''))
        if not levels or len(df_5m) < 10:
            return

        lookback = max(1, int(getattr(config, 'FAKEOUT_LOOKBACK_BARS', 3)))
        reclaim = max(1, int(getattr(config, 'FAKEOUT_RECLAIM_BARS', 2)))

        last_time = self.fakeout_alert_state['last_time']
        if last_time is not None:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < config.EXHAUST_COOLDOWN_MINUTES * 60:
                return

        last = df_5m.iloc[-1]
        body = abs(last['close'] - last['open'])
        wick = (last['high'] - last['low']) - body
        wick_ratio = (wick / body) if body > 0 else 0

        for lv in levels:
            if lv in self.fakeout_alert_state['fired_levels']:
                continue
            recent_high = df_5m['high'].iloc[-lookback:].max()
            if recent_high >= lv and all(df_5m['close'].iloc[-reclaim:] < lv) and wick_ratio >= config.FAKEOUT_WICK_RATIO:
                send_feishu(
                    f"**🟠 假突破警报**\n\n"
                    f"**关键位：** ${lv:.2f}\n"
                    f"**当前价：** ${price:.2f}\n"
                    f"**表现：** 刺破后回落 + 长影线\n\n"
                    f"仅提醒，不自动交易。",
                    level="warning",
                    title="🟠 假突破警报"
                )
                self.fakeout_alert_state['fired_levels'].add(lv)
                self.fakeout_alert_state['last_time'] = datetime.now()
                break

    def _check_exhaustion_alert(self, price: float, df_5m: pd.DataFrame):
        """动能衰竭提醒（只推送）"""
        if df_5m is None or df_5m.empty or len(df_5m) < 30:
            return

        last_time = self.exhaust_alert_state['last_time']
        if last_time is not None:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < config.EXHAUST_COOLDOWN_MINUTES * 60:
                return

        delta = df_5m['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_now = float(rsi.iloc[-1])
        rsi_prev = float(rsi.iloc[-2])

        vol_now = df_5m['volume'].iloc[-1]
        vol_ma = df_5m['volume'].rolling(20).mean().iloc[-1]
        vol_ratio = (vol_now / vol_ma) if vol_ma > 0 else 1.0

        if (rsi_prev - rsi_now) >= config.EXHAUST_RSI_DROP and vol_ratio <= config.EXHAUST_VOL_RATIO:
            send_feishu(
                f"**🟡 动能衰竭提醒**\n\n"
                f"**当前价：** ${price:.2f}\n"
                f"**RSI变化：** {rsi_prev:.1f} → {rsi_now:.1f}\n"
                f"**量能比：** {vol_ratio:.2f}\n\n"
                f"仅提醒，不自动交易。",
                level="warning",
                title="🟡 动能衰竭"
            )
            self.exhaust_alert_state['last_time'] = datetime.now()

    def _check_exit_signals(self, positions: list, df_15m: pd.DataFrame, df_1h: pd.DataFrame, price: float) -> str:
        """出场提醒（15m / 1H）"""
        if not positions:
            return ""

        pos = positions[0]
        size = float(pos.get('pos', 0))
        if size == 0:
            return ""

        side = "LONG" if size > 0 else "SHORT"

        def _analyze(df: pd.DataFrame, label: str) -> str:
            if df is None or df.empty:
                return ""
            tech = self.technical_analyst.analyze(df, price)
            signal = tech.get('signal', 0)
            strength = tech.get('signal_strength', 0)
            adx = tech.get('adx', 0)
            # exit if opposite direction and strong enough
            if size > 0 and signal < 0 and strength >= 0.6 and adx >= 25:
                return f"{label}: Opposite signal (strength {strength:.0%}, ADX {adx:.1f})"
            if size < 0 and signal > 0 and strength >= 0.6 and adx >= 25:
                return f"{label}: Opposite signal (strength {strength:.0%}, ADX {adx:.1f})"
            return ""

        notes = []
        note_15m = _analyze(df_15m, "15m")
        if note_15m:
            notes.append(note_15m)
        note_1h = _analyze(df_1h, "1H")
        if note_1h:
            notes.append(note_1h)

        if not notes:
            return ""

        return (
            f"Exit Signal\n\n"
            f"Side: {side}\n"
            f"Price: ${price:.2f}\n"
            + "\n".join(notes)
        )

    async def _maybe_send_gemini_analysis(self, price, account, positions, df_3m, df_15m, df_1h, df_4h, decision):
        """Call Gemini and push only final analysis to Feishu."""
        # interval control
        interval = self._parse_interval_seconds(config.PUSH_INTERVAL)
        if interval > 0 and self.last_gemini_time is not None:
            elapsed = (datetime.now() - self.last_gemini_time).total_seconds()
            if elapsed < interval:
                return

        # on-signal-only control
        if config.PUSH_ON_SIGNAL_ONLY and not decision.get('should_trade', False):
            return

        prompt = self._build_gemini_prompt(price, account, positions, df_3m, df_15m, df_1h, df_4h, decision)
        analysis = None
        if prompt and config.GEMINI_API_KEY and config.GEMINI_BASE_URL and config.GEMINI_MODEL:
            try:
                from gemini_client import gemini_generate
                analysis = await asyncio.to_thread(gemini_generate, prompt)
            except Exception:
                analysis = None

        if not analysis:
            analysis = self._build_local_reference(price, df_3m, df_15m, df_1h, df_4h)

        send_feishu(analysis, level="info", title="AURUM 参考")
        self.last_gemini_time = datetime.now()

    def _parse_interval_seconds(self, value: str) -> int:
        if not value:
            return 0
        v = value.strip().lower()
        if v.endswith('s'):
            return int(v[:-1])
        if v.endswith('m'):
            return int(v[:-1]) * 60
        if v.endswith('h'):
            return int(v[:-1]) * 3600
        return int(v)

    def _build_gemini_prompt(self, price, account, positions, df_3m, df_15m, df_1h, df_4h, decision) -> str:
        def summarize_df(df, label):
            if df is None or df.empty:
                return f"{label}: n/a"
            close = df['close']
            rsi = self._calc_rsi(close).iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            trend = "up" if close.iloc[-1] >= ma20 else "down"
            return f"{label}: rsi {rsi:.1f}, trend {trend}, ma20 {ma20:.2f}, ma50 {ma50:.2f}"

        pos_line = "Position: None"
        if positions:
            p = positions[0]
            pos = float(p.get('pos', 0))
            side = "LONG" if pos > 0 else "SHORT"
            avg = float(p.get('avgPx', 0))
            last = float(p.get('last', avg))
            lever = p.get('lever')
            upl = float(p.get('upl', 0))
            liq = float(p.get('liqPx') or 0)
            pos_line = f"Position: {side} {abs(pos):.0f} @ {avg:.2f}, last {last:.2f}, lev {lever}x, pnl {upl:.2f}, liq {liq:.2f}"

        decision_line = f"Signal {decision.get('signal', 0):.2f}, conf {decision.get('confidence', 0):.2f}"

        account_line = ""
        if account:
            account_line = f"Equity {account['total_equity']:.2f}, Avail {account['available']:.2f}, Margin {account['margin_used']:.2f}, UPnL {account['unrealized_pnl']:.2f}"

        prompt = (
            "你是交易辅助。只输出4行中文，格式固定：\n"
            "1) 市场状态：强/弱/震荡  | 2) 短线动能：上/下/弱  | 3) 风险：高/中/低  | 4) 关键位：支撑xx-xx，阻力xx-xx。\n"
            "不要给买卖指令，不要给仓位/杠杆/止损止盈，不要重复原始指标。\n\n"
            f"价格 {price:.2f}\n"
            f"{account_line}\n"
            f"{pos_line}\n"
            f"{decision_line}\n"
            f"{summarize_df(df_3m, '3m')} | {summarize_df(df_15m, '15m')}\n"
            f"{summarize_df(df_1h, '1H')} | {summarize_df(df_4h, '4H')}\n"
        )
        return prompt

    def _build_local_reference(self, price, df_3m, df_15m, df_1h, df_4h) -> str:
        def _safe_last(series):
            return float(series.iloc[-1]) if series is not None and len(series) else float('nan')

        def _trend(df):
            if df is None or df.empty:
                return 0.0
            close = df['close']
            ma20 = close.rolling(20).mean()
            return _safe_last(close - ma20)

        def _rsi(df):
            if df is None or df.empty:
                return float('nan')
            return float(self._calc_rsi(df['close']).iloc[-1])

        def _atr(df):
            if df is None or df.empty:
                return float('nan')
            high = df['high']
            low = df['low']
            tr = (high - low).abs()
            atr = tr.rolling(14).mean()
            return _safe_last(atr)

        def _levels(df):
            if df is None or df.empty:
                return (price, price)
            low = float(df['low'].tail(20).min())
            high = float(df['high'].tail(20).max())
            return (low, high)

        t_short = _trend(df_3m) + _trend(df_15m)
        t_long = _trend(df_1h) + _trend(df_4h)
        rsi_1h = _rsi(df_1h)
        rsi_4h = _rsi(df_4h)
        atr_15m = _atr(df_15m)

        if t_long > 0 and t_short > 0:
            market = "强"
        elif t_long < 0 and t_short < 0:
            market = "弱"
        else:
            market = "震荡"

        if t_short > 0:
            momentum = "上"
        elif t_short < 0:
            momentum = "下"
        else:
            momentum = "弱"

        risk = "中"
        if (rsi_1h and rsi_1h > 75) or (rsi_4h and rsi_4h > 75):
            risk = "高"
        if atr_15m and atr_15m > 20:
            risk = "高"

        sup, res = _levels(df_15m if df_15m is not None else df_3m)
        if atr_15m and atr_15m > 0:
            sup = sup - atr_15m
            res = res + atr_15m

        sup2 = sup + (atr_15m if atr_15m else 0)
        res2 = res - (atr_15m if atr_15m else 0)

        line1 = f"市场状态：{market}"
        line2 = f"短线动能：{momentum}"
        line3 = f"风险：{risk}"
        line4 = f"关键位：支撑{sup:.1f}-{sup2:.1f}，阻力{res2:.1f}-{res:.1f}"
        return "\n".join([line1, line2, line3, line4])

    @staticmethod
    def _calc_rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))


async def main():
    """主入口"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🔥 AURUM - 黄金Multi-Agent交易系统                  ║
    ║                                                              ║
    ║  核心特点：                                                   ║
    ║    • 宏观基本面监测（美元、美债、VIX）                        ║
    ║    • 技术分析（1H K线 + 铁矿石特征工程）                      ║
    ║    • Multi-Agent协同决策                                     ║
    ║    • 白天推送 + 夜晚自动交易                                  ║
    ║    • 右侧浮盈加仓（正金字塔）                                 ║
    ║    • 动态杠杆 {}-{}x                                         ║
    ║                                                              ║
    ║  🚀 Buy the Dip, 顺势而为！                                  ║
    ║  💰 飞书实时推送！                                            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止系统
    """.format(config.MIN_LEVERAGE, config.MAX_LEVERAGE))
    
    system = AURUMSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())
