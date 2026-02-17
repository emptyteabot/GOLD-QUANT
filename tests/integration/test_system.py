"""
系统集成测试
测试完整的交易系统工作流
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtest_engine import BacktestEngine
from complete_multi_agent import CompleteMultiAgentSystem
from risk_manager import RiskManager


class TestSystemIntegration:
    """系统集成测试"""

    def setup_method(self):
        """初始化测试环境"""
        self.backtest_engine = BacktestEngine(1000.0)
        self.multi_agent = CompleteMultiAgentSystem()
        self.risk_manager = RiskManager()

    def test_agent_and_risk_integration(self, sample_klines):
        """测试Agent和风控模块集成"""
        # 1. 训练ML模型
        self.multi_agent.train_ml_model(sample_klines)

        # 2. 生成交易信号
        macro_result = {'score': 70}
        tech_result = {'signal': 0.7, 'confidence': 0.8}

        decision = self.multi_agent.make_decision(
            macro_result=macro_result,
            tech_result=tech_result,
            klines_df=sample_klines,
            current_price=2000.0
        )

        # 3. 风控检查
        account = {
            'total_equity': 1000.0,
            'available': 900.0,
            'margin_used': 100.0
        }

        risk_check = self.risk_manager.check_risk_limits(
            account=account,
            daily_start_equity=1000.0
        )

        assert risk_check['can_trade'] is True

        # 4. 计算仓位
        if decision['signal'] > 0.5:
            position = self.risk_manager.calculate_position_size(
                account=account,
                price=2000.0,
                leverage=decision['leverage']
            )

            assert position is not None
            assert position['size'] > 0

    @pytest.mark.asyncio
    async def test_backtest_with_agents(self, sample_klines):
        """测试回测引擎与Agent集成"""
        # 这个测试需要完整的回测流程
        # 由于需要异步和大量数据，这里简化测试

        # 验证回测引擎可以使用Agent
        assert self.backtest_engine.multi_agent is not None
        assert self.backtest_engine.technical_analyst is not None

    def test_position_lifecycle(self, sample_account):
        """测试持仓生命周期"""
        inst_id = 'XAUUSDT-SWAP'

        # 1. 开仓
        position_data = self.risk_manager.calculate_position_size(
            account=sample_account,
            price=2000.0,
            leverage=10
        )

        assert position_data is not None

        # 2. 记录持仓
        self.risk_manager.record_position(inst_id, {
            'initial_risk': position_data['risk_amount'],
            'entry_price': 2000.0
        })

        assert inst_id in self.risk_manager.positions

        # 3. 检查加仓条件
        sample_position = {
            'instId': inst_id,
            'avgPx': '2000.0',
            'pos': '10'
        }

        can_pyramid = self.risk_manager.check_pyramid_condition(
            position=sample_position,
            current_price=2100.0
        )

        # 4. 平仓
        self.risk_manager.clear_position(inst_id)

        assert inst_id not in self.risk_manager.positions


class TestDataFlow:
    """数据流测试"""

    def test_kline_to_features(self, sample_klines):
        """测试K线数据到特征的转换"""
        agent = CompleteMultiAgentSystem()

        # 训练模型（内部会计算特征）
        result = agent.train_ml_model(sample_klines)

        assert result is True

    def test_signal_to_order(self, sample_account):
        """测试信号到订单的转换"""
        risk_manager = RiskManager()

        # 模拟强烈的买入信号
        signal = 0.8
        confidence = 0.9

        # 计算仓位
        position = risk_manager.calculate_position_size(
            account=sample_account,
            price=2000.0,
            leverage=10
        )

        assert position is not None
        assert position['size'] > 0

        # 验证订单参数
        assert position['stop_loss'] < 2000.0
        assert position['take_profit'] > 2000.0


class TestErrorRecovery:
    """错误恢复测试"""

    def test_insufficient_data_recovery(self):
        """测试数据不足时的恢复"""
        agent = CompleteMultiAgentSystem()

        # 数据不足
        df = pd.DataFrame({
            'close': [2000, 2010, 2020],
            'volume': [1000, 1100, 1200]
        })

        result = agent.train_ml_model(df)

        # 应该优雅地失败
        assert result is False
        assert agent.ml_trained is False

        # 系统应该仍然可以做决策（不使用ML）
        decision = agent.make_decision(
            macro_result={'score': 50},
            tech_result={'signal': 0.5, 'confidence': 0.7},
            klines_df=df,
            current_price=2000.0
        )

        assert 'signal' in decision

    def test_risk_limit_enforcement(self, sample_account):
        """测试风控限制执行"""
        risk_manager = RiskManager()

        # 模拟大幅亏损
        sample_account['total_equity'] = 700.0  # 亏损30%

        risk_check = risk_manager.check_risk_limits(
            account=sample_account,
            daily_start_equity=1000.0
        )

        # 应该禁止交易
        assert risk_check['can_trade'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
