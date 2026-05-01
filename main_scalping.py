"""
AURUM 短线交易系统主程序
16-Agent + 5分钟K线 + 快进快出
"""
import asyncio
import logging
from datetime import datetime
import config
from okx_client import OKXClient
from risk_manager import RiskManager
from scalping_engine import ScalpingEngine
from feishu_notifier import send_feishu

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AURUMScalpingSystem:
    """AURUM短线交易系统"""

    def __init__(self):
        self.okx_client = OKXClient()
        self.risk_manager = RiskManager()
        self.scalping_engine = ScalpingEngine(self.okx_client, self.risk_manager)
        self.running = False

    async def initialize(self) -> bool:
        """初始化系统"""
        logger.info("\n" + "="*80)
        logger.info("🚀 AURUM 短线交易系统启动")
        logger.info("="*80)
        logger.info("📊 模式: 16-Agent讨论 + 5分钟K线 + 快进快出")
        logger.info("⏱️  目标: 5-15分钟内平仓")
        logger.info("🎯 策略: 精准短线交易")

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

        return True

    async def run_trading_loop(self):
        """交易循环"""
        self.running = True
        cycle = 0

        while self.running:
            try:
                cycle += 1
                logger.info(f"\n{'='*80}")
                logger.info(f"📍 交易周期 #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}")

                # 获取当前价格
                ticker = await self.okx_client.get_ticker(config.INST_ID)
                if not ticker:
                    logger.warning("⚠️ 无法获取行情")
                    await asyncio.sleep(60)
                    continue

                current_price = float(ticker['last'])
                logger.info(f"💹 当前价格: ${current_price:.2f}")

                # 执行交易分析和下单
                result = await self.scalping_engine.analyze_and_trade(config.INST_ID, current_price)
                logger.info(f"📋 交易结果: {result}")

                # 显示性能统计
                stats = self.scalping_engine.get_performance_stats()
                if stats['total_trades'] > 0:
                    logger.info(f"\n📈 性能统计:")
                    logger.info(f"   总交易数: {stats['total_trades']}")
                    logger.info(f"   胜率: {stats['win_rate']:.1%}")
                    logger.info(f"   总盈亏: ${stats['total_pnl']:.2f}")
                    logger.info(f"   平均盈亏: ${stats['avg_pnl_per_trade']:.2f}")

                # 等待5分钟后再次分析
                logger.info(f"⏳ 等待5分钟后进行下一次分析...")
                await asyncio.sleep(300)  # 5分钟

            except KeyboardInterrupt:
                logger.info("\n⏹️  用户中断，系统停止")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ 交易循环出错: {e}")
                await asyncio.sleep(60)

    async def run(self):
        """运行系统"""
        if not await self.initialize():
            logger.error("❌ 系统初始化失败")
            return

        try:
            await self.run_trading_loop()
        except Exception as e:
            logger.error(f"❌ 系统运行失败: {e}")
        finally:
            logger.info("\n🛑 系统已停止")


async def main():
    """主函数"""
    system = AURUMScalpingSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())
