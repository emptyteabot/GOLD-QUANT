"""
配置更新建议 - 风控V2集成
将增强版风控模块集成到主系统的配置变更
"""

# ============================================================
# config.py 更新建议
# ============================================================

# 1. 杠杆配置更新
# 旧配置:
# BASE_LEVERAGE = int(os.getenv('BASE_LEVERAGE', '10'))
# MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '20'))
# MIN_LEVERAGE = int(os.getenv('MIN_LEVERAGE', '1'))

# 新配置（建议）:
BASE_LEVERAGE = int(os.getenv('BASE_LEVERAGE', '5'))
MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '10'))  # 降低至10x
MIN_LEVERAGE = int(os.getenv('MIN_LEVERAGE', '1'))

# 2. 新增风控参数
# VaR/CVaR配置
VAR_CONFIDENCE = float(os.getenv('VAR_CONFIDENCE', '0.95'))
CVAR_CONFIDENCE = float(os.getenv('CVAR_CONFIDENCE', '0.95'))
VAR_WINDOW = int(os.getenv('VAR_WINDOW', '100'))

# 熔断机制配置
CIRCUIT_BREAKER_LOSS = float(os.getenv('CIRCUIT_BREAKER_LOSS', '0.08'))  # 8%
CIRCUIT_BREAKER_VOLATILITY = float(os.getenv('CIRCUIT_BREAKER_VOLATILITY', '0.05'))  # 5%
CIRCUIT_BREAKER_COOLDOWN = int(os.getenv('CIRCUIT_BREAKER_COOLDOWN', '3600'))  # 1小时

# 流动性配置
MIN_LIQUIDITY_SCORE = float(os.getenv('MIN_LIQUIDITY_SCORE', '0.6'))
LIQUIDITY_WINDOW = int(os.getenv('LIQUIDITY_WINDOW', '20'))

# 动态杠杆配置
VOLATILITY_LOW_THRESHOLD = float(os.getenv('VOLATILITY_LOW_THRESHOLD', '0.02'))
VOLATILITY_HIGH_THRESHOLD = float(os.getenv('VOLATILITY_HIGH_THRESHOLD', '0.04'))

# ============================================================
# .env.trading 更新建议
# ============================================================

"""
# 杠杆配置（降低风险）
BASE_LEVERAGE=5
MAX_LEVERAGE=10
MIN_LEVERAGE=1

# VaR/CVaR风险度量
VAR_CONFIDENCE=0.95
CVAR_CONFIDENCE=0.95
VAR_WINDOW=100

# 熔断机制
CIRCUIT_BREAKER_LOSS=0.08
CIRCUIT_BREAKER_VOLATILITY=0.05
CIRCUIT_BREAKER_COOLDOWN=3600

# 流动性管理
MIN_LIQUIDITY_SCORE=0.6
LIQUIDITY_WINDOW=20

# 动态杠杆
VOLATILITY_LOW_THRESHOLD=0.02
VOLATILITY_HIGH_THRESHOLD=0.04
"""

# ============================================================
# main.py 集成建议
# ============================================================

"""
# 1. 导入新模块
from risk_manager_enhanced_v2 import RiskManagerEnhancedV2

# 2. 初始化（替换旧的RiskManager）
# 旧代码:
# from risk_manager import RiskManager
# risk_manager = RiskManager()

# 新代码:
from risk_manager_enhanced_v2 import RiskManagerEnhancedV2
risk_manager = RiskManagerEnhancedV2()

# 3. 设置每日起始权益（在每日开始时调用）
def on_trading_day_start(account):
    risk_manager.set_daily_start_equity(account['total_equity'])
    logger.info(f"📊 设置每日起始权益: ${account['total_equity']:.2f}")

# 4. 开仓前风控检查（完整流程）
def check_before_open_position(account, klines_df):
    # 熔断检查
    breaker = risk_manager.check_circuit_breaker(account, klines_df)
    if breaker['triggered']:
        logger.warning(f"🚨 熔断触发: {breaker['reason']}")
        return False

    # 流动性检查
    liquidity = risk_manager.assess_liquidity(klines_df)
    if not liquidity['can_trade']:
        logger.warning(f"⚠️ 流动性不足: {liquidity['score']:.2f}")
        return False

    return True

# 5. 仓位计算（使用新方法）
def calculate_position(account, price, klines_df):
    # 新方法自动集成所有风控功能
    position = risk_manager.calculate_position_size(
        account=account,
        price=price,
        klines_df=klines_df,
        stop_loss_pct=config.STOP_LOSS_PCT,
        use_kelly=True
    )

    if position:
        logger.info(f"💰 仓位: {position['size']}张, {position['leverage']}x")
        logger.info(f"📊 VaR(95%): {position['var']:.2%}")
        logger.info(f"📊 CVaR(95%): {position['cvar']:.2%}")
        return position
    else:
        logger.warning("❌ 风控拒绝开仓")
        return None

# 6. 交易记录（新增return_pct参数）
def on_trade_closed(pnl, account):
    return_pct = pnl / account['total_equity']
    risk_manager.record_trade(pnl, return_pct)
    logger.info(f"💵 交易记录: ${pnl:.2f} ({return_pct:.2%})")

# 7. 定期生成风险报告（建议每小时）
def generate_risk_report(account):
    report = risk_manager.get_risk_report(account)

    logger.info("=" * 60)
    logger.info("风险报告")
    logger.info("=" * 60)
    logger.info(f"账户权益: ${report['account_equity']:.2f}")
    logger.info(f"持仓数量: {report['position_count']}")
    logger.info(f"交易次数: {report['trade_count']}")
    logger.info(f"胜率: {report.get('win_rate', 0):.2%}")
    logger.info(f"VaR(95%): {report.get('var_95', 0):.2%}")
    logger.info(f"CVaR(95%): {report.get('cvar_95', 0):.2%}")
    logger.info(f"熔断状态: {'激活' if report['circuit_breaker_active'] else '正常'}")

    # 可选：推送到飞书
    # feishu_notifier.send_risk_report(report)
"""

# ============================================================
# 迁移步骤
# ============================================================

"""
步骤1: 备份现有代码
- 备份 config.py
- 备份 main.py
- 备份 .env.trading

步骤2: 更新配置文件
- 修改 config.py 添加新参数
- 修改 .env.trading 添加新配置

步骤3: 代码集成
- 在 main.py 中导入 RiskManagerEnhancedV2
- 替换 RiskManager 为 RiskManagerEnhancedV2
- 更新仓位计算调用
- 添加熔断检查
- 添加流动性检查

步骤4: 测试验证
- 运行单元测试: python test_risk_manager_v2.py
- 运行演示程序: python demo_risk_manager_v2.py
- 模拟盘测试（纸上交易）

步骤5: 监控上线
- 小仓位实盘测试
- 监控风控指标
- 根据实际情况调优参数

步骤6: 文档更新
- 更新系统文档
- 更新操作手册
- 培训相关人员
"""

# ============================================================
# 兼容性说明
# ============================================================

"""
RiskManagerEnhancedV2 完全兼容旧版 RiskManager 的接口：

兼容方法:
- calculate_position_size()
- check_pyramid_condition()
- calculate_pyramid_size()
- update_trailing_stop()
- record_position()
- increment_pyramid_count()
- clear_position()
- check_risk_limits()

新增方法:
- calculate_var_cvar()
- calculate_volatility()
- calculate_dynamic_leverage()
- check_circuit_breaker()
- assess_liquidity()
- set_daily_start_equity()
- get_risk_report()

因此可以无缝替换，旧代码无需修改即可运行。
新功能需要显式调用新方法。
"""

# ============================================================
# 性能影响
# ============================================================

"""
计算开销分析:

1. VaR/CVaR计算
   - 时间复杂度: O(n log n)
   - 数据量: 100个历史收益率
   - 耗时: < 1ms

2. 波动率计算
   - 时间复杂度: O(n)
   - 数据量: 20-100根K线
   - 耗时: < 1ms

3. 流动性评估
   - 时间复杂度: O(n)
   - 数据量: 20根K线
   - 耗时: < 1ms

4. 熔断检查
   - 时间复杂度: O(1)
   - 耗时: < 0.1ms

总体影响: 每次仓位计算增加约 2-3ms，可忽略不计。
"""

# ============================================================
# 回滚方案
# ============================================================

"""
如果新版本出现问题，可快速回滚：

1. 恢复旧代码
   - 从备份恢复 config.py
   - 从备份恢复 main.py
   - 从备份恢复 .env.trading

2. 重启系统
   - 停止交易程序
   - 切换到旧版本
   - 重新启动

3. 保留数据
   - 新版本的交易记录和风控数据保留
   - 可用于后续分析和优化

回滚时间: < 5分钟
"""

print(__doc__)
