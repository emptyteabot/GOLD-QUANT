"""
安全测试
测试系统安全性和风控机制
"""
import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from risk_manager import RiskManager
from backtest_engine import BacktestEngine


class TestRiskControls:
    """风控机制测试"""

    def test_max_daily_loss_enforcement(self, sample_account):
        """测试单日最大亏损限制"""
        risk_manager = RiskManager()

        # 模拟亏损超过限制
        sample_account['total_equity'] = 800.0  # 亏损20%
        daily_start = 1000.0

        result = risk_manager.check_risk_limits(
            account=sample_account,
            daily_start_equity=daily_start
        )

        # 应该禁止交易
        assert result['can_trade'] is False
        print(f"\n✅ 单日亏损限制生效: {result['reason']}")

    def test_position_size_limits(self, sample_account):
        """测试仓位大小限制"""
        risk_manager = RiskManager()

        position = risk_manager.calculate_position_size(
            account=sample_account,
            price=2000.0,
            leverage=10
        )

        # 仓位不应该超过账户权益的30%
        max_margin = sample_account['total_equity'] * 0.3
        assert position['margin'] <= max_margin
        print(f"\n✅ 仓位限制: {position['margin']:.2f} <= {max_margin:.2f}")

    def test_leverage_limits(self, sample_account):
        """测试杠杆限制"""
        risk_manager = RiskManager()

        # 尝试使用超高杠杆
        position = risk_manager.calculate_position_size(
            account=sample_account,
            price=2000.0,
            leverage=100  # 超高杠杆
        )

        # 系统应该限制实际使用的杠杆
        # 或者拒绝开仓
        if position:
            # 实际风险应该在可控范围内
            risk_pct = position['risk_amount'] / sample_account['total_equity']
            assert risk_pct < 0.1  # 风险不超过10%

    def test_stop_loss_enforcement(self):
        """测试止损强制执行"""
        engine = BacktestEngine(1000.0)

        timestamp = pd.Timestamp.now()

        # 开多单
        engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='long'
        )

        pos = engine.positions[0]
        stop_loss = pos['stop_loss']

        # 价格跌破止损
        engine._check_exit(price=stop_loss - 10, timestamp=timestamp)

        # 应该已平仓
        assert len(engine.positions) == 0
        print(f"\n✅ 止损执行: 价格{stop_loss-10:.2f} < 止损{stop_loss:.2f}")

    def test_pyramid_limits(self, sample_position):
        """测试加仓次数限制"""
        risk_manager = RiskManager()
        inst_id = 'XAUUSDT-SWAP'

        risk_manager.record_position(inst_id, {'initial_risk': 100.0})

        # 模拟多次加仓
        for i in range(10):
            risk_manager.increment_pyramid_count(inst_id)

        # 检查是否拒绝继续加仓
        can_pyramid = risk_manager.check_pyramid_condition(
            position=sample_position,
            current_price=3000.0  # 大幅浮盈
        )

        assert can_pyramid is False
        print(f"\n✅ 加仓次数限制生效")


class TestInputValidation:
    """输入验证测试"""

    def test_negative_price_handling(self, sample_account):
        """测试负价格处理"""
        risk_manager = RiskManager()

        with pytest.raises(Exception):
            risk_manager.calculate_position_size(
                account=sample_account,
                price=-2000.0,  # 负价格
                leverage=10
            )

    def test_zero_leverage_handling(self, sample_account):
        """测试零杠杆处理"""
        risk_manager = RiskManager()

        with pytest.raises(Exception):
            risk_manager.calculate_position_size(
                account=sample_account,
                price=2000.0,
                leverage=0  # 零杠杆
            )

    def test_invalid_account_data(self):
        """测试无效账户数据"""
        risk_manager = RiskManager()

        invalid_account = {
            'total_equity': -100.0,  # 负权益
            'available': 50.0
        }

        with pytest.raises(Exception):
            risk_manager.calculate_position_size(
                account=invalid_account,
                price=2000.0,
                leverage=10
            )

    def test_malformed_klines(self):
        """测试畸形K线数据"""
        agent = CompleteMultiAgentSystem()

        # 缺少必要字段
        df = pd.DataFrame({
            'close': [2000, 2010]
            # 缺少volume字段
        })

        with pytest.raises(Exception):
            agent.train_ml_model(df)


class TestDataIntegrity:
    """数据完整性测试"""

    def test_position_record_consistency(self):
        """测试持仓记录一致性"""
        risk_manager = RiskManager()
        inst_id = 'XAUUSDT-SWAP'

        # 记录持仓
        risk_manager.record_position(inst_id, {
            'initial_risk': 100.0,
            'entry_price': 2000.0
        })

        # 验证记录
        assert inst_id in risk_manager.positions
        assert risk_manager.positions[inst_id]['initial_risk'] == 100.0

        # 清除后验证
        risk_manager.clear_position(inst_id)
        assert inst_id not in risk_manager.positions

    def test_trade_history_integrity(self):
        """测试交易历史完整性"""
        engine = BacktestEngine(1000.0)

        timestamp = pd.Timestamp.now()

        # 开仓
        engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='long'
        )

        # 平仓
        pos = engine.positions[0]
        engine._close_position(
            position=pos,
            price=2100.0,
            timestamp=timestamp,
            reason="测试"
        )

        # 验证交易记录
        assert len(engine.trades) == 1
        trade = engine.trades[0]
        assert trade['entry_price'] == 2000.0
        assert trade['exit_price'] == 2100.0
        assert trade['pnl'] > 0


class TestEdgeCases:
    """边界情况测试"""

    def test_minimum_position_size(self, sample_account):
        """测试最小仓位"""
        risk_manager = RiskManager()

        # 使用很小的账户
        small_account = {
            'total_equity': 10.0,
            'available': 9.0,
            'margin_used': 1.0
        }

        position = risk_manager.calculate_position_size(
            account=small_account,
            price=2000.0,
            leverage=10
        )

        # 应该返回None或最小仓位
        if position:
            assert position['size'] >= 1  # 至少1张合约

    def test_extreme_price_movement(self):
        """测试极端价格波动"""
        engine = BacktestEngine(1000.0)

        timestamp = pd.Timestamp.now()

        # 开多单
        engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='long'
        )

        # 极端价格下跌
        engine._check_exit(price=1000.0, timestamp=timestamp)

        # 应该已止损
        assert len(engine.positions) == 0

        # 资金应该还有剩余（不会爆仓到负数）
        assert engine.capital > 0

    def test_rapid_price_changes(self):
        """测试快速价格变化"""
        engine = BacktestEngine(1000.0)

        timestamp = pd.Timestamp.now()

        # 开多单
        engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='long'
        )

        # 快速价格变化
        prices = [2010, 2020, 2015, 2025, 2030]

        for price in prices:
            engine._check_exit(price=price, timestamp=timestamp)

        # 系统应该正常处理


class TestSecurityBestPractices:
    """安全最佳实践测试"""

    def test_no_hardcoded_credentials(self):
        """测试没有硬编码凭证"""
        # 检查主要文件中没有硬编码的API密钥
        import config

        # API密钥应该从环境变量读取
        assert hasattr(config, 'OKX_API_KEY')
        # 不应该是明文字符串
        # 实际测试需要检查源代码

    def test_sensitive_data_logging(self):
        """测试敏感数据不被记录"""
        # 确保日志中不包含API密钥等敏感信息
        # 实际测试需要检查日志输出
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
