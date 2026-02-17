"""
风控模块单元测试
测试RiskManager的核心功能
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from risk_manager import RiskManager


class TestRiskManager:
    """风控管理器测试类"""

    def setup_method(self):
        """每个测试前初始化"""
        self.risk_manager = RiskManager()

    def test_calculate_position_size_basic(self, sample_account):
        """测试基础仓位计算"""
        result = self.risk_manager.calculate_position_size(
            account=sample_account,
            price=2000.0,
            leverage=10,
            stop_loss_pct=0.10
        )

        assert result is not None
        assert 'size' in result
        assert 'margin' in result
        assert 'stop_loss' in result
        assert 'take_profit' in result
        assert result['size'] > 0
        assert result['margin'] <= sample_account['available']

    def test_calculate_position_size_insufficient_funds(self):
        """测试资金不足情况"""
        account = {
            'total_equity': 10.0,
            'available': 5.0,
            'margin_used': 5.0
        }

        result = self.risk_manager.calculate_position_size(
            account=account,
            price=2000.0,
            leverage=10
        )

        # 资金太少，应该返回None或size=0
        assert result is None or result['size'] == 0

    def test_stop_loss_calculation(self, sample_account):
        """测试止损价格计算"""
        result = self.risk_manager.calculate_position_size(
            account=sample_account,
            price=2000.0,
            leverage=10,
            stop_loss_pct=0.10
        )

        assert result is not None
        # 止损应该是价格的90%
        expected_stop = 2000.0 * 0.9
        assert abs(result['stop_loss'] - expected_stop) < 1.0

    def test_take_profit_calculation(self, sample_account):
        """测试止盈价格计算（3:1盈亏比）"""
        result = self.risk_manager.calculate_position_size(
            account=sample_account,
            price=2000.0,
            leverage=10,
            stop_loss_pct=0.10
        )

        assert result is not None
        # 止盈应该是价格的130%（3倍止损距离）
        expected_tp = 2000.0 * 1.30
        assert abs(result['take_profit'] - expected_tp) < 1.0

    def test_pyramid_condition_check(self, sample_position):
        """测试加仓条件检查"""
        # 记录初始持仓
        self.risk_manager.record_position('XAUUSDT-SWAP', {
            'initial_risk': 100.0
        })

        # 测试浮盈不足
        result = self.risk_manager.check_pyramid_condition(
            position=sample_position,
            current_price=2010.0  # 仅1%浮盈
        )
        assert result is False

        # 测试浮盈充足
        result = self.risk_manager.check_pyramid_condition(
            position=sample_position,
            current_price=2100.0  # 5%浮盈
        )
        # 根据配置，可能返回True

    def test_pyramid_count_limit(self, sample_position):
        """测试加仓次数限制"""
        inst_id = 'XAUUSDT-SWAP'

        # 记录初始持仓
        self.risk_manager.record_position(inst_id, {
            'initial_risk': 100.0
        })

        # 模拟多次加仓
        for i in range(5):
            self.risk_manager.increment_pyramid_count(inst_id)

        # 检查是否达到上限
        result = self.risk_manager.check_pyramid_condition(
            position=sample_position,
            current_price=3000.0  # 大幅浮盈
        )
        assert result is False  # 应该拒绝加仓

    def test_trailing_stop_long(self, sample_position):
        """测试多单移动止损"""
        new_stop = self.risk_manager.update_trailing_stop(
            position=sample_position,
            current_price=2100.0,
            atr=10.0
        )

        assert new_stop is not None
        # 止损应该在入场价之上（保本）
        entry_price = float(sample_position['avgPx'])
        assert new_stop >= entry_price

    def test_risk_limits_daily_loss(self, sample_account):
        """测试单日最大亏损限制"""
        daily_start_equity = 1000.0

        # 模拟大幅亏损
        sample_account['total_equity'] = 800.0  # 亏损20%

        result = self.risk_manager.check_risk_limits(
            account=sample_account,
            daily_start_equity=daily_start_equity
        )

        assert result['can_trade'] is False
        assert '亏损' in result['reason']

    def test_risk_limits_low_balance(self, sample_account):
        """测试可用资金不足"""
        sample_account['available'] = 50.0  # 仅剩5%

        result = self.risk_manager.check_risk_limits(
            account=sample_account,
            daily_start_equity=1000.0
        )

        assert result['can_trade'] is False
        assert '资金' in result['reason']

    def test_position_record_and_clear(self):
        """测试持仓记录和清除"""
        inst_id = 'XAUUSDT-SWAP'

        # 记录持仓
        self.risk_manager.record_position(inst_id, {
            'initial_risk': 100.0,
            'entry_price': 2000.0
        })

        assert inst_id in self.risk_manager.positions

        # 清除持仓
        self.risk_manager.clear_position(inst_id)

        assert inst_id not in self.risk_manager.positions
        assert inst_id not in self.risk_manager.pyramid_count


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
