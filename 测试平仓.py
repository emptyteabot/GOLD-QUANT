"""
🧪 平仓测试（卖出1张）
"""
import asyncio
import logging
from okx_client import OKXClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_close_position():
    """测试平仓1张"""
    logger.info("="*80)
    logger.info("🧪 平仓测试（卖出1张多头）")
    logger.info("="*80)
    
    client = OKXClient()
    await client.initialize()
    
    # 1. 查询当前持仓
    logger.info("\n📊 查询当前持仓...")
    positions = await client.get_positions()
    
    current_pos = 0
    if positions:
        for pos in positions:
            if pos.get('instId') == 'XAU-USDT-SWAP':
                current_pos = int(pos.get('pos', 0))
                logger.info(f"   当前持仓: {current_pos} 张 ({pos.get('posSide')})")
    
    if current_pos <= 0:
        logger.error("❌ 没有多头持仓可平")
        await client.close()
        return
    
    # 2. 获取当前价格
    logger.info("\n📊 获取当前价格...")
    price = await client.get_ticker("XAU-USDT-SWAP")
    logger.info(f"✅ 当前价格: ${price:.2f}")
    
    # 3. 准备平仓
    close_size = 1  # 平仓1张
    
    logger.info(f"\n📝 准备平仓:")
    logger.info(f"   合约: XAU-USDT-SWAP")
    logger.info(f"   方向: 卖出平多 (sell)")
    logger.info(f"   数量: {close_size}张")
    logger.info(f"   持仓变化: {current_pos} → {current_pos - close_size}张")
    
    # 4. 确认平仓
    logger.info("\n" + "="*80)
    logger.info("⚠️  即将执行平仓！")
    logger.info("="*80)
    
    confirm = input("\n确认平仓？(输入 yes 确认): ")
    
    if confirm.lower() != 'yes':
        logger.info("❌ 已取消平仓")
        await client.close()
        return
    
    # 5. 执行平仓
    logger.info("\n🚀 执行平仓...")
    
    try:
        # 平仓：side=sell, posSide=long, reduceOnly=true
        result = await client.place_order(
            inst_id="XAU-USDT-SWAP",
            side="sell",  # 卖出
            size=close_size,
            pos_side="long",  # 平多头
            reduce_only=True  # 只减仓
        )
        
        if result:
            logger.info("\n" + "="*80)
            logger.info("🎉 平仓成功！")
            logger.info("="*80)
            logger.info(f"订单ID: {result.get('ordId', 'N/A')}")
        else:
            logger.error("❌ 平仓失败")
            
    except Exception as e:
        logger.error(f"❌ 平仓异常: {e}")
    
    # 6. 再次查询持仓
    logger.info("\n📊 查询平仓后持仓...")
    positions = await client.get_positions()
    if positions:
        for pos in positions:
            if pos.get('instId') == 'XAU-USDT-SWAP':
                new_pos = int(pos.get('pos', 0))
                logger.info(f"   当前持仓: {new_pos} 张")
                logger.info(f"   变化: {current_pos} → {new_pos} (减少{current_pos - new_pos}张)")
    
    await client.close()
    logger.info("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_close_position())
