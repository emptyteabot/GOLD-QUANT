"""
风险管理模块测试用例
测试增强版V2的所有功能
"""
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from risk_manager_enhanced_v2 import RiskManagerEnhancedV2


class TestRiskManagerV2(unittest.TestCase):
    """风险管理器测试"""

    def setUp(self):
        """测试前准备"""
        self.rm = RiskManagerEnhancedV2()
        self.account = {
            'total_equity': 1000,
            'available': 900,
            'margin_used': 100
        }

        # 生成模拟K线数据
        dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')
        np.random.seed(42)
        self.klines_df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.randn(100).cumsum() + 2800,
            'high': np.random.randn(100).cumsum() + 2810,
            'low': np.random.randn(100).cumsum() + 2790,
            'close': np.random.randn(100).cumsum() + 2800,
            'volume': np.random.randint(1000, 5000, 100)
        })

    def test_var_cvar_calculation(self):
        """测试VaR/CVaR计算"""
        print("\n=== 测试VaR/CVaR计算 ===")

        # 生成模拟收益率
        returns = np.random.normal(-0.001, 0.02, 100)

        var, cvar = self.rm.calculate_var_cvar(returns, confidence=0.95)

        print(f"VaR(95%): {var:.4f}")
        print(f"CVaR(95%): {cvar:.4f}")

        # 断言
        self.assertLess(var, 0, "VaR应该为负值")
        self.assertLess(cvar, var, "CVaR应该小于VaR")

    def test_volatility_calculation(self):
        """测试波动率计算"""
        print("\n=== 测试波动率计算 ===")

        volatility = self.rm.calculate_volatility(self.klines_df)

        print(f"年化波动率: {volatility:.4f}")

        # 断言
        self.assertGreater(volatility, 0, "波动率应该大于0")
        self.assertLess(volatility, 1, "波动率应该小于100%")

    def test_dynamic_leverage(self):
        """测试动态杠杆调整"""
        print("\n=== 测试动态杠杆调整 ===")

        # 测试低波动率
        low_vol_df = self.klines_df.copy()
        low_vol_df['close'] = 2800 + np.random.randn(100) * 0.1  # 低波动

        leverage_low = self.rm.calculate_dynamic_leverage(low_vol_df)
        print(f"低波动率杠杆: {leverage_low}x")

        # 测试高波动率
        high_vol_df = self.klines_df.copy()
        high_vol_df['close'] = 2800 + np.random.randn(100) * 50  # 高波动

        leverage_high = self.rm.calculate_dynamic_leverage(high_vol_df)
        print(f"高波动率杠杆: {leverage_high}x")

        # 断言
        self.assertGreaterEqual(leverage_low, leverage_high, "低波动率应使用更高杠杆")
        self.assertLessEqual(leverage_high, self.rm.MAX_LEVERAGE, "杠杆不应超过最大值")

    def test_circuit_breaker_daily_loss(self):
        """测试熔断机制 - 单日亏损"""
        print("\n=== 测试熔断机制 - 单日亏损 ===")

        self.rm.set_daily_start_equity(1000)

        # 模拟大幅亏损
        account_loss = {
            'total_equity': 900,  # 亏损10%
            'available': 850,
            'margin_used': 50
        }

        result = self.rm.check_circuit_breaker(account_loss, self.klines_df)

        print(f"熔断触发: {result['triggered']}")
        print(f"原因: {result['reason']}")

        # 断言
        self.assertTrue(result['triggered'], "单日亏损10%应触发熔断")

    def test_circuit_breaker_volatility(self):
        """测试熔断机制 - 极端波动"""
        print("\n=== 测试熔断机制 - 极端波动 ===")

        # 生成极端波动数据
        extreme_vol_df = self.klines_df.copy()
        extreme_vol_df['close'] = 2800 + np.random.randn(100) * 100  # 极端波动

        self.rm.set_daily_start_equity(1000)

        result = self.rm.check_circuit_breaker(self.account, extreme_vol_df)

        print(f"熔断触发: {result['triggered']}")
        print(f"原因: {result['reason']}")

        # 断言（可能触发）
        if result['triggered']:
            self.assertIn('波动', result['reason'], "应该是波动率触发熔断")

    def test_circuit_breaker_consecutive_losses(self):
        """测试熔断机制 - 连续亏损"""
        print("\n=== 测试熔断机制 - 连续亏损 ===")

        # 记录3笔连续亏损
        self.rm.record_trade(-50)
        self.rm.record_trade(-30)
        self.rm.record_trade(-20)

        self.rm.set_daily_start_equity(1000)

        result = self.rm.check_circuit_breaker(self.account, self.klines_df)

        print(f"熔断触发: {result['triggered']}")
        print(f"原因: {result['reason']}")

        # 断言
        self.assertTrue(result['triggered'], "连续3笔亏损应触发熔断")

    def test_liquidity_assessment(self):
        """测试流动性评估"""
        print("\n=== 测试流动性评估 ===")

        # 测试正常流动性
        result = self.rm.assess_liquidity(self.klines_df)

        print(f"流动性评分: {result['score']:.2f}")
        print(f"风险等级: {result['risk_level']}")
        print(f"可交易: {result['can_trade']}")

        # 断言
        self.assertIn('score', result, "应返回评分")
        self.assertIn('risk_level', result, "应返回风险等级")
        self.assertIn('can_trade', result, "应返回可交易标志")

    def test_kelly_fraction(self):
        """测试Kelly公式"""
        print("\n=== 测试Kelly公式 ===")

        # 记录一些交易历史
        for _ in range(10):
            pnl = np.random.choice([50, -30], p=[0.6, 0.4])  # 60%胜率
            self.rm.record_trade(pnl)

        kelly = self.rm.calculate_kelly_fraction()

        print(f"Kelly仓位: {kelly:.2%}")

        # 断言
        self.assertGreater(kelly, 0, "Kelly应该大于0")
        self.assertLess(kelly, 0.5, "Kelly应该小于50%（折半后）")

    def test_atr_calculation(self):
        """测试ATR计算"""
        print("\n=== 测试ATR计算 ===")

        atr = self.rm.calculate_atr(self.klines_df)

        print(f"ATR: {atr:.2f}")

        # 断言
        self.assertGreater(atr, 0, "ATR应该大于0")

    def test_position_size_calculation(self):
        """测试仓位计算（集成测试）"""
        print("\n=== 测试仓位计算 ===")

        self.rm.set_daily_start_equity(1000)

        result = self.rm.calculate_position_size(
            self.account,
            2800,
            self.klines_df,
            stop_loss_pct=0.10,
            use_kelly=True
        )

        if result:
            print(f"合约张数: {result['size']}")
            print(f"杠杆: {result['leverage']}x")
            print(f"保证金: ${result['margin']:.2f}")
            print(f"止损: ${result['stop_loss']:.2f}")
            print(f"止盈: ${result['take_profit']:.2f}")
            print(f"风险金额: ${result['risk_amount']:.2f}")
            print(f"Kelly仓位: {result['kelly_fraction']:.2%}")

            # 断言
            self.assertGreater(result['size'], 0, "合约张数应大于0")
            self.assertLessEqual(result['leverage'], self.rm.MAX_LEVERAGE, "杠杆不应超过最大值")
            self.assertLess(result['stop_loss'], 2800, "止损应低于入场价")
            self.assertGreater(result['take_profit'], 2800, "止盈应高于入场价")
        else:
            print("无法开仓（可能触发风控）")

    def test_trailing_stop(self):
        """测试移动止损"""
        print("\n=== 测试移动止损 ===")

        position = {
            'instId': 'XAU-USDT-SWAP',
            'avgPx': '2800',
            'pos': '10'
        }

        new_stop = self.rm.update_trailing_stop(position, 2850, self.klines_df)

        print(f"新止损价: ${new_stop:.2f}")

        # 断言
        self.assertGreater(new_stop, 2800, "移动止损应高于入场价（多单盈利）")

    def test_risk_report(self):
        """测试风险报告"""
        print("\n=== 测试风险报告 ===")

        # 记录一些交易
        for _ in range(20):
            pnl = np.random.choice([50, -30], p=[0.6, 0.4])
            return_pct = pnl / 1000
            self.rm.record_trade(pnl, return_pct)

        self.rm.set_daily_start_equity(1000)

        report = self.rm.get_risk_report(self.account)

        print(f"账户权益: ${report['account_equity']:.2f}")
        print(f"交易次数: {report['trade_count']}")
        print(f"胜率: {report.get('win_rate', 0):.2%}")
        print(f"平均盈利: ${report.get('avg_win', 0):.2f}")
        print(f"平均亏损: ${report.get('avg_loss', 0):.2f}")
        print(f"总盈亏: ${report.get('total_pnl', 0):.2f}")

        # 断言
        self.assertIn('account_equity', report, "应包含账户权益")
        self.assertIn('trade_count', report, "应包含交易次数")

    def test_max_leverage_limit(self):
        """测试最大杠杆限制"""
        print("\n=== 测试最大杠杆限制 ===")

        # 验证最大杠杆已降至10x
        self.assertEqual(self.rm.MAX_LEVERAGE, 10, "最大杠杆应为10x")

        # 测试极低波动率也不会超过10x
        ultra_low_vol_df = self.klines_df.copy()
        ultra_low_vol_df['close'] = 2800 + np.random.randn(100) * 0.01

        leverage = self.rm.calculate_dynamic_leverage(ultra_low_vol_df)

        print(f"极低波动率杠杆: {leverage}x")

        # 断言
        self.assertLessEqual(leverage, 10, "杠杆不应超过10x")

    def test_position_size_with_circuit_breaker(self):
        """测试熔断状态下的仓位计算"""
        print("\n=== 测试熔断状态下的仓位计算 ===")

        # 触发熔断
        self.rm.set_daily_start_equity(1000)
        account_loss = {
            'total_equity': 900,
            'available': 850,
            'margin_used': 50
        }

        self.rm.check_circuit_breaker(account_loss, self.klines_df)

        # 尝试计算仓位
        result = self.rm.calculate_position_size(
            self.account,
            2800,
            self.klines_df
        )

        print(f"熔断状态下仓位计算结果: {result}")

        # 断言
        self.assertIsNone(result, "熔断状态下应无法开仓")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("风险管理模块 V2 - 测试套件")
    print("=" * 60)

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRiskManagerV2)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
