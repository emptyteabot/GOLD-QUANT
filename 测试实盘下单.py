"""
🧪 实盘下单测试（最小金额）
测试做多加仓功能是否正常工作
"""
import asyncio
import logging
from okx_client import OKXClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_place_order():
    """测试最小金额下单"""
    logger.info("="*80)
    logger.info("🧪 实盘下单测试（最小金额做多）")
    logger.info("="*80)
    
    client = OKXClient()
    await client.initialize()
    
    # 1. 获取当前价格
    logger.info("\n📊 获取当前价格...")
    price = await client.get_ticker("XAU-USDT-SWAP")
    if not price:
        logger.error("❌ 无法获取价格")
        await client.close()
        return
    
    logger.info(f"✅ 当前价格: ${price:.2f}")
    
    # 2. 获取账户余额
    logger.info("\n💰 获取账户余额...")
    account = await client.get_account_balance()
    if account:
        # 提取USDT余额
        details = account.get('details', [])
        for d in details:
            if d.get('ccy') == 'USDT':
                balance = float(d.get('availBal', 0))
                logger.info(f"✅ 可用余额: ${balance:.2f} USDT")
                break
    
    # 3. 跳过杠杆设置（因为有止盈止损单时无法修改）
    logger.info("\n⚙️ 使用现有杠杆设置（10x）...")
    
    # 4. 计算最小下单量
    # OKX的sz参数是张数，不是XAUT数量
    # XAU-USDT-SWAP: 1张 = 0.01 XAUT
    # 最小下单 1张 = 0.01 XAUT ≈ $49
    min_size = 1  # 1张（最小）
    xaut_amount = 0.01  # 1张 = 0.01 XAUT
    
    logger.info(f"\n📝 准备下单:")
    logger.info(f"   合约: XAU-USDT-SWAP")
    logger.info(f"   方向: 做多 (buy) - 加仓")
    logger.info(f"   数量: {min_size}张 = {xaut_amount} XAUT")
    logger.info(f"   价值: ~${xaut_amount * price:.2f}")
    logger.info(f"   杠杆: 10x")
    logger.info(f"   保证金: ~${xaut_amount * price / 10:.2f}")
    
    # 5. 确认下单
    logger.info("\n" + "="*80)
    logger.info("⚠️  即将执行真实交易！")
    logger.info(f"⚠️  将做多（加仓） {xaut_amount} XAUT，价值约 ${xaut_amount * price:.2f}")
    logger.info("="*80)
    
    confirm = input("\n确认下单？(输入 yes 确认): ")
    
    if confirm.lower() != 'yes':
        logger.info("❌ 已取消下单")
        await client.close()
        return
    
    # 6. 执行下单
    logger.info("\n🚀 执行下单...")
    
    try:
        result = await client.place_order(
            inst_id="XAU-USDT-SWAP",
            side="buy",  # 做多（加仓）
            size=min_size,  # 1张
            leverage=10
        )
        
        if result:
            logger.info("\n" + "="*80)
            logger.info("🎉 下单成功！")
            logger.info("="*80)
            logger.info(f"订单ID: {result.get('ordId', 'N/A')}")
            logger.info(f"客户端ID: {result.get('clOrdId', 'N/A')}")
            logger.info(f"\n⚠️ 注意：止盈止损需要在OKX App手动设置")
        else:
            logger.error("❌ 下单失败")
            
    except Exception as e:
        logger.error(f"❌ 下单异常: {e}")
    
    # 7. 查询持仓
    logger.info("\n📊 查询当前持仓...")
    positions = await client.get_positions()
    if positions:
        for pos in positions:
            logger.info(f"   {pos.get('instId')}: {pos.get('pos')} 张 ({pos.get('posSide')})")
    else:
        logger.info("   无持仓")
    
    await client.close()
    logger.info("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_place_order())

