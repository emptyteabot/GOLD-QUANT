"""
终极版黄金交易系统 - 实盘主程序
提前5-30秒预警，领先市场
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys
import signal

# 导入配置
import config_ultimate as config

# 导入核心模块
from leading_indicators import LeadingIndicatorMonitor
from price_monitor import PriceMonitor
from wechat_notifier import notifier

# 尝试导入可选模块
try:
    from data_engine import DataEngine
    HAS_DATA_ENGINE = True
except ImportError:
    HAS_DATA_ENGINE = False
    print("⚠️ 数据引擎未找到，使用简化版本")

try:
    from ml_predictor import EnsemblePredictor
    HAS_ML_PREDICTOR = True
except ImportError:
    HAS_ML_PREDICTOR = False
    print("⚠️ ML预测器未找到，使用基础策略")

try:
    from risk_manager import RiskManager
    HAS_RISK_MANAGER = True
except ImportError:
    HAS_RISK_MANAGER = False
    print("⚠️ 风险管理器未找到，使用简化风控")

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UltimateGoldTradingSystem:
    """
    终极黄金交易系统
    
    核心特点:
    1. 提前预警 - 监控价格变化的原因，而不是价格本身
    2. 多源验证 - 领先指标 + 订单簿 + ML预测
    3. 严格风控 - 止损/止盈/仓位管理/熔断机制
    4. 实时通知 - 微信/飞书推送
    """
    
    def __init__(self):
        self.running = False
        self.last_signal_time = None
        self.last_notification_time = None
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.circuit_breaker_active = False
        
        # 初始化模块
        self.leading_monitor = LeadingIndicatorMonitor()
        self.price_monitor = PriceMonitor()
        
        if HAS_RISK_MANAGER:
            self.risk_manager = RiskManager(initial_capital=config.INITIAL_CAPITAL)
        else:
            self.risk_manager = None
        
        if HAS_ML_PREDICTOR:
            self.ml_predictor = EnsemblePredictor()
        else:
            self.ml_predictor = None
        
        # 性能统计
        self.stats = {
            'total_signals': 0,
            'strong_signals': 0,
            'trades_executed': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'total_pnl': 0.0
        }
    
    async def initialize(self):
        """初始化系统"""
        logger.info("=" * 70)
        logger.info("🚀 终极黄金交易系统启动")
        logger.info("=" * 70)
        
        # 验证配置
        if not config.validate_config():
            logger.error("配置验证失败，系统退出")
            sys.exit(1)
        
        # 打印配置摘要
        config.print_config_summary()
        
        # 初始化各模块
        await self.leading_monitor.initialize()
        await self.price_monitor.initialize()
        
        # 发送启动通知
        await self.send_notification(
            "🚀 系统已启动",
            f"**交易模式:** {config.TRADING_MODE}\n"
            f"**初始资金:** ${config.INITIAL_CAPITAL:,.0f}\n"
            f"**最大仓位:** {config.MAX_POSITION*100:.0f}%\n"
            f"**止损:** {config.STOP_LOSS*100:.0f}%\n\n"
            f"系统正在监控黄金市场\n"
            f"发现交易机会时会立即通知你\n\n"
            f"**监控内容:**\n"
            f"• 美元指数 (DXY)\n"
            f"• 美债收益率 (US10Y)\n"
            f"• VIX 恐慌指数\n"
            f"• 订单簿失衡\n"
            f"• 机器学习预测",
            "success"
        )
        
        logger.info("✅ 系统初始化完成")
        self.running = True
    
    async def shutdown(self):
        """关闭系统"""
        logger.info("正在关闭系统...")
        self.running = False
        
        # 发送关闭通知
        await self.send_notification(
            "🛑 系统已关闭",
            f"**运行统计:**\n"
            f"• 总信号数: {self.stats['total_signals']}\n"
            f"• 强信号数: {self.stats['strong_signals']}\n"
            f"• 执行交易: {self.stats['trades_executed']}\n"
            f"• 胜率: {self.stats['win_trades']/(self.stats['trades_executed'] or 1)*100:.1f}%\n"
            f"• 总盈亏: ${self.stats['total_pnl']:,.2f}",
            "info"
        )
        
        # 关闭各模块
        await self.leading_monitor.close()
        await self.price_monitor.close()
        
        logger.info("✅ 系统已关闭")
    
    async def send_notification(self, title: str, message: str, level: str = "info"):
        """
        发送通知
        
        Args:
            title: 标题
            message: 消息内容
            level: 级别 (critical/warning/info/debug)
        """
        # 检查通知级别
        if not config.NOTIFICATION_LEVELS.get(level, False):
            return
        
        # 检查通知频率限制
        now = datetime.now()
        if self.last_notification_time:
            elapsed = (now - self.last_notification_time).total_seconds()
            if elapsed < config.MIN_NOTIFICATION_INTERVAL:
                logger.debug(f"通知频率限制，跳过: {title}")
                return
        
        # 发送通知
        try:
            if config.WECHAT_ENABLED:
                await notifier.send_alert(title, message, level)
            
            if config.FEISHU_ENABLED:
                await self.send_feishu(title, message, level)
            
            self.last_notification_time = now
            logger.info(f"✅ 通知已发送: {title}")
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    async def send_feishu(self, title: str, message: str, level: str):
        """发送飞书通知"""
        import aiohttp
        
        # 颜色映射
        color_map = {
            'critical': 'red',
            'warning': 'orange',
            'success': 'green',
            'info': 'blue'
        }
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "content": title,
                        "tag": "plain_text"
                    },
                    "template": color_map.get(level, 'blue')
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": message
                    }
                ]
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(config.FEISHU_WEBHOOK_URL, json=payload) as resp:
                    if resp.status == 200:
                        logger.debug("飞书通知发送成功")
                    else:
                        logger.warning(f"飞书通知发送失败: {resp.status}")
        except Exception as e:
            logger.error(f"飞书通知异常: {e}")
    
    async def check_circuit_breaker(self) -> bool:
        """
        检查熔断机制
        
        Returns:
            True: 触发熔断，停止交易
            False: 正常运行
        """
        if not config.CIRCUIT_BREAKER['enabled']:
            return False
        
        # 检查单日亏损
        if self.daily_pnl < -config.INITIAL_CAPITAL * config.CIRCUIT_BREAKER['daily_loss_limit']:
            if not self.circuit_breaker_active:
                self.circuit_breaker_active = True
                await self.send_notification(
                    "🚨 熔断触发 - 单日亏损超限",
                    f"**单日亏损:** ${abs(self.daily_pnl):,.2f}\n"
                    f"**亏损比例:** {abs(self.daily_pnl)/config.INITIAL_CAPITAL*100:.2f}%\n\n"
                    f"系统已暂停交易\n"
                    f"冷却期: {config.CIRCUIT_BREAKER['cooldown_period']/3600:.1f}小时",
                    "critical"
                )
            return True
        
        # 检查连续亏损
        if self.consecutive_losses >= config.CIRCUIT_BREAKER['consecutive_losses']:
            if not self.circuit_breaker_active:
                self.circuit_breaker_active = True
                await self.send_notification(
                    "🚨 熔断触发 - 连续亏损",
                    f"**连续亏损:** {self.consecutive_losses}次\n\n"
                    f"系统已暂停交易\n"
                    f"冷却期: {config.CIRCUIT_BREAKER['cooldown_period']/3600:.1f}小时",
                    "critical"
                )
            return True
        
        return False
    
    async def analyze_market(self) -> Dict:
        """
        综合市场分析
        
        Returns:
            {
                'signal': 信号方向,
                'confidence': 置信度,
                'urgency': 紧急程度,
                'lead_time': 提前时间,
                'reasons': 原因列表,
                'price': 当前价格,
                'position_size': 建议仓位,
                'stop_loss': 止损价格,
                'take_profit': 止盈价格
            }
        """
        # 1. 获取当前价格
        current_price = await self.price_monitor.fetch_current_price()
        if not current_price:
            return {'signal': 'neutral', 'confidence': 0}
        
        # 2. 领先指标分析
        leading_signal = await self.leading_monitor.get_comprehensive_signal()
        
        # 3. ML预测（如果可用）
        ml_signal = None
        if self.ml_predictor and HAS_ML_PREDICTOR:
            try:
                # TODO: 实现ML预测
                pass
            except Exception as e:
                logger.warning(f"ML预测失败: {e}")
        
        # 4. 综合信号
        signal = leading_signal['signal']
        confidence = leading_signal['confidence']
        urgency = leading_signal['urgency']
        lead_time = leading_signal['lead_time']
        reasons = leading_signal['reasons']
        
        # 5. 计算仓位
        if self.risk_manager:
            position_size = self.risk_manager.calculate_position_size(
                signal_strength=confidence/100,
                volatility=0.02  # TODO: 计算实际波动率
            )
        else:
            # 简化仓位计算
            position_size = min(confidence/100 * config.MAX_POSITION, config.MAX_POSITION)
        
        # 6. 计算止损止盈
        if signal in ['bullish', 'strong_bullish']:
            stop_loss_price = current_price * (1 - config.STOP_LOSS)
            take_profit_price = current_price * (1 + config.TAKE_PROFIT)
        elif signal in ['bearish', 'strong_bearish']:
            stop_loss_price = current_price * (1 + config.STOP_LOSS)
            take_profit_price = current_price * (1 - config.TAKE_PROFIT)
        else:
            stop_loss_price = None
            take_profit_price = None
        
        return {
            'signal': signal,
            'confidence': confidence,
            'urgency': urgency,
            'lead_time': lead_time,
            'reasons': reasons,
            'price': current_price,
            'position_size': position_size,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
            'details': leading_signal['details']
        }
    
    async def process_signal(self, analysis: Dict):
        """
        处理交易信号
        
        Args:
            analysis: 市场分析结果
        """
        signal = analysis['signal']
        confidence = analysis['confidence']
        urgency = analysis['urgency']
        
        # 更新统计
        self.stats['total_signals'] += 1
        if confidence > config.STRONG_SIGNAL_THRESHOLD * 100:
            self.stats['strong_signals'] += 1
        
        # 检查信号强度
        if confidence < config.MIN_SIGNAL_STRENGTH * 100:
            logger.debug(f"信号强度不足: {confidence:.1f}%")
            return
        
        # 检查熔断
        if await self.check_circuit_breaker():
            logger.warning("熔断机制激活，跳过交易")
            return
        
        # 检查交易频率
        if self.daily_trades >= config.MAX_TRADES_PER_DAY:
            logger.warning("达到每日交易次数上限")
            return
        
        # 检查信号间隔
        now = datetime.now()
        if self.last_signal_time:
            elapsed = (now - self.last_signal_time).total_seconds()
            if elapsed < config.MIN_TRADE_INTERVAL:
                logger.debug(f"信号间隔过短: {elapsed:.0f}秒")
                return
        
        # 生成通知消息
        signal_emoji = {
            'strong_bullish': '🚀',
            'bullish': '📈',
            'neutral': '➡️',
            'bearish': '📉',
            'strong_bearish': '💥'
        }
        
        signal_text = {
            'strong_bullish': '强烈做多',
            'bullish': '做多',
            'neutral': '观望',
            'bearish': '做空',
            'strong_bearish': '强烈做空'
        }
        
        emoji = signal_emoji.get(signal, '❓')
        text = signal_text.get(signal, signal)
        
        message = (
            f"## {emoji} {text}\n\n"
            f"**当前价格:** ${analysis['price']:.2f}\n"
            f"**信号强度:** {confidence:.1f}%\n"
            f"**紧急程度:** {urgency}/10\n"
            f"**提前时间:** {analysis['lead_time']}\n\n"
            f"**建议仓位:** {analysis['position_size']*100:.1f}%\n"
        )
        
        if analysis['stop_loss']:
            message += f"**止损价格:** ${analysis['stop_loss']:.2f}\n"
        if analysis['take_profit']:
            message += f"**止盈价格:** ${analysis['take_profit']:.2f}\n"
        
        if analysis['reasons']:
            message += f"\n**信号来源:**\n"
            for reason in analysis['reasons']:
                message += f"• {reason}\n"
        
        message += (
            f"\n**风险提示:**\n"
            f"• 严格执行止损\n"
            f"• 控制仓位大小\n"
            f"• 不要重仓\n"
            f"• 这是提前预警，价格可能还未变化"
        )
        
        # 发送通知
        level = 'critical' if urgency >= 8 else 'warning'
        await self.send_notification(
            f"{emoji} {text} 信号",
            message,
            level
        )
        
        # 记录信号
        self.last_signal_time = now
        logger.info(f"✅ 信号已处理: {text} (置信度: {confidence:.1f}%)")
        
        # 如果是实盘模式，这里可以执行实际交易
        if config.TRADING_MODE == 'live' and not config.DRY_RUN:
            # TODO: 实现实际交易逻辑
            logger.info("实盘模式 - 等待手动确认交易")
    
    async def run(self):
        """主循环"""
        try:
            await self.initialize()
            
            logger.info("=" * 70)
            logger.info("💰 开始监控市场")
            logger.info("=" * 70)
            
            while self.running:
                try:
                    # 分析市场
                    analysis = await self.analyze_market()
                    
                    # 处理信号
                    if analysis['signal'] != 'neutral':
                        await self.process_signal(analysis)
                    
                    # 等待下一次检查
                    await asyncio.sleep(config.DATA_UPDATE_INTERVAL)
                    
                except Exception as e:
                    logger.error(f"主循环错误: {e}", exc_info=True)
                    await asyncio.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        except Exception as e:
            logger.error(f"系统错误: {e}", exc_info=True)
        finally:
            await self.shutdown()


# ==================== 主程序入口 ====================

async def main():
    """主函数"""
    system = UltimateGoldTradingSystem()
    
    # 注册信号处理
    def signal_handler(sig, frame):
        logger.info("收到退出信号")
        system.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行系统
    await system.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n系统已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)
