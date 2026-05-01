"""
AURUM 24小时后台交易系统
持续监控 + 飞书实时通知
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path
import json
import aiohttp

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入系统模块
try:
    from okx_client import OKXClient
    from risk_manager import RiskManager
    from agent_16_scalping_system import Agent16ScalpingSystem
    from scalping_engine import ScalpingEngine
    import config
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# 配置日志
# ═══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aurum_24h.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 飞书通知
# ═══════════════════════════════════════════════════════════════
class FeishuNotifier:
    """飞书通知器"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_signal(self, signal_data: dict):
        """发送交易信号通知"""
        try:
            message = self._build_signal_message(signal_data)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        logger.info("✅ 飞书通知已发送")
                        return True
                    else:
                        logger.error(f"❌ 飞书通知失败: {resp.status}")
                        return False

        except Exception as e:
            logger.error(f"❌ 发送飞书通知异常: {e}")
            return False

    def _build_signal_message(self, signal_data: dict) -> dict:
        """构建飞书消息"""

        action = signal_data['action']
        current_price = signal_data['current_price']
        entry_price = signal_data['entry_price']
        stop_loss = signal_data['stop_loss']
        take_profit = signal_data['take_profit']
        confidence = signal_data['confidence']
        long_count = signal_data['long_count']
        short_count = signal_data['short_count']
        signal_value = signal_data['signal']
        leverage = signal_data.get('leverage', 0)
        position_pct = signal_data.get('position_size_pct', 0)
        risk_reward = signal_data.get('risk_reward', 0)
        hold_minutes = signal_data.get('expected_hold_minutes', 0)
        summary = signal_data.get('reason_summary', '-')

        # 确定颜色和emoji
        if action == '做多':
            color = 'green'
            emoji = '🟢'
            action_text = '做多信号'
        elif action == '做空':
            color = 'red'
            emoji = '🔴'
            action_text = '做空信号'
        else:
            color = 'grey'
            emoji = '⚪'
            action_text = '观望'

        # 构建消息
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": f"{emoji} **AURUM 交易信号**\n**{action_text}**",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**当前价格**\n${current_price:.2f}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**信心度**\n{confidence:.1%}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**开仓点位**\n${entry_price:.2f}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**止损点位**\n${stop_loss:.2f}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**止盈点位**\n${take_profit:.2f}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**杠杆倍数**\n{leverage}x",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**建议仓位**\n{position_pct:.0%}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**风险收益比**\n1:{risk_reward:.2f}",
                                    "tag": "lark_md"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**Agent讨论结果**\n做多: {long_count}/16 | 做空: {short_count}/16\n综合信号: {signal_value:.2f}",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**执行摘要**\n{summary}\n预计持仓: {hold_minutes} 分钟",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            "tag": "lark_md"
                        }
                    }
                ]
            }
        }

        return message

    async def send_status(self, status_text: str):
        """发送状态通知"""
        try:
            message = {
                "msg_type": "text",
                "content": {
                    "text": f"[{datetime.now().strftime('%H:%M:%S')}] {status_text}"
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    return resp.status == 200

        except Exception as e:
            logger.error(f"❌ 发送状态通知异常: {e}")
            return False

# ═══════════════════════════════════════════════════════════════
# 24小时交易系统
# ═══════════════════════════════════════════════════════════════
class AURUM24HSystem:
    """24小时后台交易系统"""

    def __init__(self, webhook_url: str):
        self.okx_client = OKXClient()
        self.risk_manager = RiskManager()
        self.scalping_engine = ScalpingEngine(self.okx_client, self.risk_manager)
        self.agent_system = Agent16ScalpingSystem()
        self.notifier = FeishuNotifier(webhook_url)

        # 状态跟踪
        self.running = False
        self.last_signal_time = None
        self.last_signal_action = None
        self.cycle_count = 0
        self.signal_count = 0

    async def initialize(self) -> bool:
        """初始化系统"""
        try:
            logger.info("\n" + "="*80)
            logger.info("🚀 AURUM 24小时后台交易系统启动")
            logger.info("="*80)
            logger.info("📊 模式: 16-Agent讨论 + 5分钟K线 + 快进快出")
            logger.info("⏱️  目标: 5-15分钟内平仓")
            logger.info("🔔 通知: 飞书实时推送")

            # 初始化OKX客户端
            await self.okx_client.initialize()

            # 获取账户信息
            account = await self.okx_client.get_account_balance()
            if not account:
                logger.error("❌ 无法获取账户信息")
                return False

            logger.info(f"\n💰 账户信息:")
            logger.info(f"   总权益: ${account['total_equity']:.2f}")
            logger.info(f"   可用资金: ${account['available']:.2f}")

            # 发送启动通知
            await self.notifier.send_status(
                f"✅ AURUM系统已启动\n"
                f"账户权益: ${account['total_equity']:.2f}\n"
                f"可用资金: ${account['available']:.2f}"
            )

            return True

        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}")
            return False

    async def analyze_and_notify(self):
        """分析并发送通知"""
        try:
            # 获取当前价格
            ticker = await self.okx_client.get_ticker(config.INST_ID)
            if not ticker:
                logger.warning("⚠️ 无法获取行情")
                return

            current_price = float(ticker['last'])

            # 获取K线数据
            klines_df = await self.scalping_engine.get_klines(config.INST_ID, limit=100)
            if klines_df is None or len(klines_df) < 20:
                logger.warning("⚠️ K线数据不足")
                return

            # 16-Agent分析
            analysis = self.agent_system.analyze(klines_df, current_price)

            logger.info(f"\n{'='*80}")
            logger.info(f"📍 交易周期 #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*80}")
            logger.info(f"💹 当前价格: ${current_price:.2f}")
            logger.info(f"📊 决策: {analysis['action']}")
            logger.info(f"   信心度: {analysis['confidence']:.1%}")
            logger.info(f"   做多Agent: {analysis['long_count']}/16")
            logger.info(f"   做空Agent: {analysis['short_count']}/16")

            # 检查是否有新的交易信号
            if analysis.get('tradeable') and analysis['confidence'] >= 0.6 and analysis['action'] != '观望':
                # 检查是否与上一个信号重复
                if self.last_signal_action == analysis['action'] and \
                   self.last_signal_time and \
                   (datetime.now() - self.last_signal_time).total_seconds() < 300:
                    logger.info("⏭️  信号重复，跳过通知")
                    return

                # 发送交易信号通知
                logger.info(f"\n🔔 发送交易信号通知...")

                signal_data = {
                    'action': analysis['action'],
                    'current_price': current_price,
                    'entry_price': analysis['entry_price'],
                    'stop_loss': analysis['stop_loss'],
                    'take_profit': analysis['take_profit'],
                    'confidence': analysis['confidence'],
                    'long_count': analysis['long_count'],
                    'short_count': analysis['short_count'],
                    'signal': analysis['signal'],
                    'leverage': analysis.get('leverage', 0),
                    'position_size_pct': analysis.get('position_size_pct', 0),
                    'risk_reward': analysis.get('risk_reward', 0),
                    'expected_hold_minutes': analysis.get('expected_hold_minutes', 0),
                    'reason_summary': analysis.get('reason_summary', '-'),
                }

                success = await self.notifier.send_signal(signal_data)

                if success:
                    self.last_signal_time = datetime.now()
                    self.last_signal_action = analysis['action']
                    self.signal_count += 1

                    logger.info(f"✅ 交易信号已发送")
                    logger.info(f"   总信号数: {self.signal_count}")
                else:
                    logger.error("❌ 交易信号发送失败")

        except Exception as e:
            logger.error(f"❌ 分析异常: {e}")

    async def run_24h_loop(self):
        """24小时循环"""
        self.running = True

        while self.running:
            try:
                self.cycle_count += 1

                # 执行分析和通知
                await self.analyze_and_notify()

                # 等待5分钟后进行下一次分析
                logger.info(f"⏳ 等待5分钟后进行下一次分析...")
                await asyncio.sleep(300)  # 5分钟

            except KeyboardInterrupt:
                logger.info("\n⏹️  用户中断，系统停止")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ 循环异常: {e}")
                await asyncio.sleep(60)

    async def run(self):
        """运行系统"""
        if not await self.initialize():
            logger.error("❌ 系统初始化失败")
            return

        try:
            await self.run_24h_loop()
        except Exception as e:
            logger.error(f"❌ 系统运行失败: {e}")
        finally:
            logger.info("\n🛑 系统已停止")
            await self.notifier.send_status("🛑 AURUM系统已停止")

# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════
async def main():
    """主函数"""
    webhook_url = config.FEISHU_WEBHOOK
    if not webhook_url:
        logger.error("❌ 未配置 FEISHU_WEBHOOK_URL")
        return

    system = AURUM24HSystem(webhook_url)
    await system.run()

if __name__ == "__main__":
    asyncio.run(main())
