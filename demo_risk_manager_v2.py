"""
风险管理系统集成示例
演示如何在主交易系统中使用增强版风控模块
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from risk_manager_enhanced_v2 import RiskManagerEnhancedV2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def simulate_trading_day():
    """模拟一个交易日的风控流程"""

    print("=" * 60)
    print("AURUM 风险管理系统 V2 - 集成演示")
    print("=" * 60)

    # 1. 初始化风控模块
    rm = RiskManagerEnhancedV2()
    logger.info("✅ 风控模块初始化完成")

    # 2. 模拟账户
    account = {
        'total_equity': 10000,
        'available': 9000,
        'margin_used': 1000
    }
    rm.set_daily_start_equity(account['total_equity'])
    logger.info(f"💰 账户权益: ${account['total_equity']:.2f}")

    # 3. 生成模拟K线数据
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1h')
    np.random.seed(42)
    base_price = 2800
    klines_df = pd.DataFrame({
        'timestamp': dates,
        'open': base_price + np.random.randn(100).cumsum() * 2,
        'high': base_price + np.random.randn(100).cumsum() * 2 + 5,
        'low': base_price + np.random.randn(100).cumsum() * 2 - 5,
        'close': base_price + np.random.randn(100).cumsum() * 2,
        'volume': np.random.randint(1000, 5000, 100)
    })
    current_price = klines_df['close'].iloc[-1]
    logger.info(f"📊 当前价格: ${current_price:.2f}")

    # 4. 风控检查流程
    print("\n" + "=" * 60)
    print("风控检查流程")
    print("=" * 60)

    # 4.1 熔断检查
    logger.info("\n🔍 步骤1: 熔断机制检查")
    breaker = rm.check_circuit_breaker(account, klines_df)
    if breaker['triggered']:
        logger.warning(f"🚨 熔断触发: {breaker['reason']}")
        logger.warning(f"⏰ 冷却剩余: {breaker['cooldown_remaining']}秒")
        return
    else:
        logger.info("✅ 熔断检查通过")

    # 4.2 流动性检查
    logger.info("\n🔍 步骤2: 流动性评估")
    liquidity = rm.assess_liquidity(klines_df)
    logger.info(f"💧 流动性评分: {liquidity['score']:.2f}")
    logger.info(f"📊 风险等级: {liquidity['risk_level']}")
    if not liquidity['can_trade']:
        logger.warning("⚠️ 流动性不足，禁止交易")
        return
    else:
        logger.info("✅ 流动性检查通过")

    # 4.3 波动率分析
    logger.info("\n🔍 步骤3: 波动率分析")
    volatility = rm.calculate_volatility(klines_df)
    logger.info(f"📈 年化波动率: {volatility:.2%}")

    # 4.4 动态杠杆计算
    logger.info("\n🔍 步骤4: 动态杠杆计算")
    leverage = rm.calculate_dynamic_leverage(klines_df)
    logger.info(f"⚙️ 推荐杠杆: {leverage}x")

    # 5. 仓位计算
    print("\n" + "=" * 60)
    print("仓位计算")
    print("=" * 60)

    position = rm.calculate_position_size(
        account=account,
        price=current_price,
        klines_df=klines_df,
        stop_loss_pct=0.10,
        use_kelly=True
    )

    if position:
        logger.info("\n✅ 仓位计算成功")
        logger.info(f"📊 合约张数: {position['size']}")
        logger.info(f"📊 实际盎司: {position['oz_size']:.3f} XAU")
        logger.info(f"📊 使用杠杆: {position['leverage']}x")
        logger.info(f"📊 保证金: ${position['margin']:.2f}")
        logger.info(f"📊 止损价: ${position['stop_loss']:.2f}")
        logger.info(f"📊 止盈价: ${position['take_profit']:.2f}")
        logger.info(f"📊 风险金额: ${position['risk_amount']:.2f}")
        logger.info(f"📊 Kelly仓位: {position['kelly_fraction']:.2%}")

        # 计算风险收益比
        risk_pct = position['risk_amount'] / account['total_equity'] * 100
        logger.info(f"📊 账户风险: {risk_pct:.2f}%")

    else:
        logger.warning("❌ 风控拒绝开仓")
        return

    # 6. 模拟交易执行
    print("\n" + "=" * 60)
    print("模拟交易执行")
    print("=" * 60)

    logger.info("\n📝 记录持仓信息")
    rm.record_position('XAU-USDT-SWAP', {
        'initial_risk': position['risk_amount'],
        'entry_price': current_price,
        'size': position['size']
    })

    # 7. 模拟价格变动和移动止损
    logger.info("\n📈 模拟价格上涨...")
    new_price = current_price * 1.05  # 上涨5%
    logger.info(f"💰 新价格: ${new_price:.2f}")

    position_data = {
        'instId': 'XAU-USDT-SWAP',
        'avgPx': str(current_price),
        'pos': str(position['size'])
    }

    new_stop = rm.update_trailing_stop(position_data, new_price, klines_df)
    logger.info(f"🔒 更新止损: ${new_stop:.2f}")

    # 8. 模拟交易记录
    logger.info("\n📊 记录交易...")
    pnl = (new_price - current_price) * position['oz_size']
    return_pct = pnl / account['total_equity']
    rm.record_trade(pnl, return_pct)
    logger.info(f"💵 盈亏: ${pnl:.2f} ({return_pct:.2%})")

    # 9. 生成风险报告
    print("\n" + "=" * 60)
    print("风险报告")
    print("=" * 60)

    report = rm.get_risk_report(account)
    logger.info(f"\n📊 账户权益: ${report['account_equity']:.2f}")
    logger.info(f"📊 持仓数量: {report['position_count']}")
    logger.info(f"📊 交易次数: {report['trade_count']}")
    logger.info(f"📊 熔断状态: {'激活' if report['circuit_breaker_active'] else '正常'}")

    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)


def demonstrate_circuit_breaker():
    """演示熔断机制"""

    print("\n\n" + "=" * 60)
    print("熔断机制演示")
    print("=" * 60)

    rm = RiskManagerEnhancedV2()

    # 场景1: 单日大幅亏损
    logger.info("\n📉 场景1: 单日亏损10%")
    rm.set_daily_start_equity(10000)
    account_loss = {
        'total_equity': 9000,  # 亏损10%
        'available': 8500,
        'margin_used': 500
    }

    dates = pd.date_range(end=datetime.now(), periods=100, freq='1h')
    klines_df = pd.DataFrame({
        'timestamp': dates,
        'open': 2800 + np.random.randn(100),
        'high': 2810 + np.random.randn(100),
        'low': 2790 + np.random.randn(100),
        'close': 2800 + np.random.randn(100),
        'volume': np.random.randint(1000, 5000, 100)
    })

    breaker = rm.check_circuit_breaker(account_loss, klines_df)
    logger.info(f"🚨 熔断触发: {breaker['triggered']}")
    logger.info(f"📝 原因: {breaker['reason']}")

    # 场景2: 连续亏损
    logger.info("\n📉 场景2: 连续3笔亏损")
    rm2 = RiskManagerEnhancedV2()
    rm2.set_daily_start_equity(10000)
    rm2.record_trade(-100)
    rm2.record_trade(-80)
    rm2.record_trade(-60)

    account_normal = {
        'total_equity': 9760,
        'available': 9000,
        'margin_used': 760
    }

    breaker2 = rm2.check_circuit_breaker(account_normal, klines_df)
    logger.info(f"🚨 熔断触发: {breaker2['triggered']}")
    logger.info(f"📝 原因: {breaker2['reason']}")


def demonstrate_dynamic_leverage():
    """演示动态杠杆调整"""

    print("\n\n" + "=" * 60)
    print("动态杠杆演示")
    print("=" * 60)

    rm = RiskManagerEnhancedV2()

    # 低波动率场景
    logger.info("\n📊 场景1: 低波动率市场")
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1h')
    low_vol_df = pd.DataFrame({
        'timestamp': dates,
        'open': 2800 + np.random.randn(100) * 0.5,
        'high': 2800 + np.random.randn(100) * 0.5 + 1,
        'low': 2800 + np.random.randn(100) * 0.5 - 1,
        'close': 2800 + np.random.randn(100) * 0.5,
        'volume': np.random.randint(1000, 5000, 100)
    })

    leverage_low = rm.calculate_dynamic_leverage(low_vol_df)
    logger.info(f"⚙️ 推荐杠杆: {leverage_low}x")

    # 高波动率场景
    logger.info("\n📊 场景2: 高波动率市场")
    high_vol_df = pd.DataFrame({
        'timestamp': dates,
        'open': 2800 + np.random.randn(100) * 30,
        'high': 2800 + np.random.randn(100) * 30 + 10,
        'low': 2800 + np.random.randn(100) * 30 - 10,
        'close': 2800 + np.random.randn(100) * 30,
        'volume': np.random.randint(1000, 5000, 100)
    })

    leverage_high = rm.calculate_dynamic_leverage(high_vol_df)
    logger.info(f"⚙️ 推荐杠杆: {leverage_high}x")


if __name__ == "__main__":
    # 运行完整演示
    simulate_trading_day()

    # 演示熔断机制
    demonstrate_circuit_breaker()

    # 演示动态杠杆
    demonstrate_dynamic_leverage()

    print("\n\n" + "=" * 60)
    print("所有演示完成！")
    print("=" * 60)
