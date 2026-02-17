"""
快速测试交易信号生成
验证Multi-Agent系统是否能产生有效信号
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from okx_client import OKXClient
from complete_multi_agent import CompleteMultiAgentSystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_signal_generation():
    """测试信号生成"""
    logger.info("="*80)
    logger.info("🧪 测试交易信号生成")
    logger.info("="*80)
    
    # 初始化系统
    agent_system = CompleteMultiAgentSystem()
    client = OKXClient()
    await client.initialize()
    
    # 获取实时K线
    logger.info("\n📊 获取实时K线数据...")
    klines = await client.get_klines('XAU-USDT-SWAP', '5m', limit=300)
    
    if not klines:
        logger.error("❌ 无法获取K线数据")
        await client.close()
        return
    
    # 转换为DataFrame
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
    df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df = df.iloc[::-1].reset_index(drop=True)
    
    logger.info(f"✅ 获取到 {len(df)} 根K线")
    
    # 训练ML模型
    logger.info("\n🤖 训练机器学习模型...")
    agent_system.train_ml_model(df)
    
    # 计算技术指标
    logger.info("\n📈 计算技术指标...")
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    # ADX（简化版）
    adx = df['close'].rolling(14).std().iloc[-1] / df['close'].rolling(14).mean().iloc[-1] * 100
    
    # 趋势信号
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    signal = 1 if df['close'].iloc[-1] > ma20 else -1
    
    tech_data = {
        'signal': signal,
        'signal_strength': 0.5,
        'rsi': current_rsi,
        'adx': adx
    }
    
    logger.info(f"   RSI: {current_rsi:.1f}")
    logger.info(f"   ADX: {adx:.1f}")
    logger.info(f"   趋势: {'看多' if signal > 0 else '看空'}")
    
    # 宏观数据（简化）
    macro_data = {'score': 50}
    
    # 当前价格
    current_price = df['close'].iloc[-1]
    logger.info(f"\n💰 当前价格: ${current_price:.2f}")
    
    # 生成决策
    logger.info("\n🤖 Multi-Agent决策...")
    decision = agent_system.make_decision(
        macro_data=macro_data,
        tech_data=tech_data,
        klines_df=df,
        price=current_price
    )
    
    # 输出结果
    logger.info("\n" + "="*80)
    logger.info("📊 决策结果")
    logger.info("="*80)
    logger.info(f"是否交易: {'✅ 是' if decision['should_trade'] else '❌ 否'}")
    logger.info(f"信号方向: {decision['signal']:+.2f} ({'做多' if decision['signal'] > 0 else '做空'})")
    logger.info(f"置信度: {decision['confidence']:.1%}")
    logger.info(f"共识度: {decision['consensus']:.1%}")
    logger.info(f"建议杠杆: {decision['leverage']}x")
    logger.info(f"原因: {decision['reason']}")
    
    logger.info(f"\n🤖 5个专家信号:")
    for agent, sig in decision['agent_signals'].items():
        logger.info(f"   {agent}: {sig:+.2f}")
    
    # 测试杠杆计算
    logger.info(f"\n🔧 杠杆计算测试:")
    test_cases = [
        (0.95, 0.85, "极强信号"),
        (0.90, 0.80, "强信号"),
        (0.75, 0.70, "标准信号"),
        (0.65, 0.60, "中等信号"),
        (0.50, 0.50, "弱信号"),
        (0.45, 0.45, "最低阈值"),
        (0.40, 0.40, "低于阈值"),
    ]
    
    for strength, consensus, desc in test_cases:
        # 模拟杠杆计算逻辑
        if strength >= 0.95 and consensus >= 0.85:
            leverage = 20
        elif strength >= 0.90 and consensus >= 0.80:
            leverage = 18
        elif strength >= 0.85 and consensus >= 0.75:
            leverage = 16
        elif strength >= 0.75 and consensus >= 0.70:
            leverage = 15
        elif strength >= 0.65 and consensus >= 0.60:
            leverage = 12
        elif strength >= 0.50 and consensus >= 0.50:
            leverage = 10
        else:
            leverage = 0
        
        logger.info(f"   {desc}: 强度{strength:.0%}, 共识{consensus:.0%} → {leverage}x杠杆")
    
    await client.close()
    
    logger.info("\n" + "="*80)
    logger.info("✅ 测试完成")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(test_signal_generation())
