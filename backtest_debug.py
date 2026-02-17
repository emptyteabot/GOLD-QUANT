"""
回测系统 - 调试版（强制显示决策过程）
找出为什么没有交易
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
from okx_client import OKXClient
from complete_multi_agent import CompleteMultiAgentSystem
from enhanced_macro_analyst import EnhancedMacroAnalyst
from technical_agent import TechnicalAnalyst
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BacktestDebug:
    """回测调试版 - 显示每次决策"""
    
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.trades = []
        
        self.multi_agent = CompleteMultiAgentSystem()
        self.technical_analyst = TechnicalAnalyst()
        
    async def run_backtest(self):
        """运行回测"""
        logger.info("="*80)
        logger.info(f"🔍 回测调试版 - 显示决策过程")
        logger.info("="*80)
        
        # 获取数据
        okx_client = OKXClient()
        await okx_client.initialize()
        
        klines = await okx_client.get_klines(config.INST_ID, '5m', 500)
        await okx_client.close()
        
        if not klines:
            logger.error("❌ 无法获取历史数据")
            return
        
        df = self._parse_klines(klines)
        logger.info(f"✅ 获取到 {len(df)} 根K线")
        
        # 训练ML
        logger.info("\n🤖 训练ML模型...")
        self.multi_agent.train_ml_model(df)
        
        # 只分析最近10根K线，详细显示决策
        logger.info("\n📊 分析最近10根K线的决策过程:")
        logger.info("="*80)
        
        for i in range(len(df) - 10, len(df)):
            historical_df = df.iloc[:i].copy()
            current_bar = df.iloc[i]
            current_price = float(current_bar['close'])
            current_time = current_bar['timestamp']
            
            logger.info(f"\n⏰ K线 #{i} | 时间: {current_time} | 价格: ${current_price:.2f}")
            
            # 宏观分析
            macro_result = {'score': 50}
            
            # 技术分析
            tech_result = self.technical_analyst.analyze(historical_df, current_price)
            logger.info(f"   📈 技术分析: 信号={tech_result.get('signal', 0):+.2f}, ADX={tech_result.get('adx', 0):.1f}, RSI={tech_result.get('rsi', 0):.1f}")
            
            # Multi-Agent决策
            decision = self.multi_agent.make_decision(
                macro_result, tech_result, historical_df, current_price
            )
            
            logger.info(f"   🤖 Multi-Agent决策:")
            logger.info(f"      最终信号: {decision['signal']:+.2f}")
            logger.info(f"      置信度: {decision['confidence']:.1%}")
            logger.info(f"      共识度: {decision['consensus']:.1%}")
            logger.info(f"      应该交易: {decision['should_trade']}")
            
            if decision['should_trade']:
                logger.info(f"      ✅ 通过should_trade检查")
                
                # 检查各种阈值
                logger.info(f"\n   🔍 阈值检查:")
                logger.info(f"      信号 {decision['signal']:+.2f} > 0.05? {decision['signal'] > 0.05}")
                logger.info(f"      置信度 {decision['confidence']:.1%} > 30%? {decision['confidence'] > 0.30}")
                
                if decision['signal'] > 0.05 and decision['confidence'] > 0.30:
                    logger.info(f"      ✅✅✅ 满足所有条件！应该开仓！")
                else:
                    logger.info(f"      ❌ 不满足阈值")
            else:
                logger.info(f"      ❌ 未通过should_trade检查")
                logger.info(f"      原因: {decision.get('reason', '未知')}")
        
        logger.info("\n" + "="*80)
        logger.info("📊 调试总结:")
        logger.info(f"   分析了 {len(df)} 根K线")
        logger.info(f"   详细显示了最后 10 根的决策过程")
        logger.info(f"   请查看上面的日志，找出为什么没有交易")
        logger.info("="*80)
    
    def _parse_klines(self, klines: list) -> pd.DataFrame:
        """解析K线数据"""
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 
            'volume', 'volCcy', 'volCcyQuote', 'confirm'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df = df.iloc[::-1].reset_index(drop=True)
        
        return df


async def main():
    """主函数"""
    print("="*80)
    print("🔍 AURUM回测调试版")
    print("="*80)
    
    engine = BacktestDebug(initial_capital=1000.0)
    await engine.run_backtest()
    
    print("\n✅ 调试完成！")


if __name__ == "__main__":
    asyncio.run(main())
