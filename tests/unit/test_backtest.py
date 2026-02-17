"""
回测引擎单元测试
测试BacktestEngine的核心功能
"""
import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtest_engine import BacktestEngine


class TestBacktestEngine:
    """回测引擎测试类"""

    def setup_method(self):
        """每个测试前初始化"""
        self.engine = BacktestEngine(initial_capital=1000.0)

    def test_initialization(self):
        """测试初始化"""
        assert self.engine.initial_capital == 1000.0
        assert self.engine.capital == 1000.0
        assert len(self.engine.positions) == 0
        assert len(self.engine.trades) == 0

    def test_parse_klines(self):
        """测试K线数据解析"""
        # 模拟OKX K线数据格式
        mock_klines = [
            ['1704067200000', '2000', '2010', '1990', '2005', '1000', '0', '0', '1'],
            ['1704067800000', '2005', '2015', '2000', '2010', '1100', '0', '0', '1'],
        ]

        df = self.engine._parse_klines(mock_klines)

        assert len(df) == 2
        assert 'timestamp' in df.columns
        assert 'close' in df.columns
        assert df['close'].dtype == float

    def test_enter_position_long(self):
        """测试开多单"""
        timestamp = pd.Timestamp.now()

        self.engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='long'
        )

        assert len(self.engine.positions) == 1
        pos = self.engine.positions[0]
        assert pos['side'] == 'long'
        assert pos['entry_price'] == 2000.0
        assert pos['leverage'] == 10
        assert pos['stop_loss'] < 2000.0  # 止损应该低于入场价

    def test_enter_position_short(self):
        """测试开空单"""
        timestamp = pd.Timestamp.now()

        self.engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='short'
        )

        assert len(self.engine.positions) == 1
        pos = self.engine.positions[0]
        assert pos['side'] == 'short'
        assert pos['stop_loss'] > 2000.0  # 止损应该高于入场价

    def test_close_position_profit(self):
        """测试盈利平仓"""
        timestamp = pd.Timestamp.now()

        # 开多单
        self.engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='long'
        )

        initial_capital = self.engine.capital
        pos = self.engine.positions[0]

        # 价格上涨后平仓
        self.engine._close_position(
            position=pos,
            price=2100.0,
            timestamp=timestamp,
            reason="测试"
        )

        # 应该盈利
        assert self.engine.capital > initial_capital
        assert len(self.engine.positions) == 0
        assert len(self.engine.trades) == 1

    def test_close_position_loss(self):
        """测试亏损平仓"""
        timestamp = pd.Timestamp.now()

        # 开多单
        self.engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='long'
        )

        initial_capital = self.engine.capital
        pos = self.engine.positions[0]

        # 价格下跌后平仓
        self.engine._close_position(
            position=pos,
            price=1900.0,
            timestamp=timestamp,
            reason="止损"
        )

        # 应该亏损
        assert self.engine.capital < initial_capital
        assert len(self.engine.trades) == 1
        assert self.engine.trades[0]['reason'] == "止损"

    def test_check_exit_stop_loss(self):
        """测试止损触发"""
        timestamp = pd.Timestamp.now()

        # 开多单，止损价约1970
        self.engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='long'
        )

        # 价格跌破止损
        self.engine._check_exit(price=1960.0, timestamp=timestamp)

        # 应该已平仓
        assert len(self.engine.positions) == 0
        assert len(self.engine.trades) == 1

    def test_check_exit_trailing_stop(self):
        """测试移动止损"""
        timestamp = pd.Timestamp.now()

        # 开多单
        self.engine._enter_position(
            price=2000.0,
            timestamp=timestamp,
            leverage=10,
            confidence=0.8,
            side='long'
        )

        pos = self.engine.positions[0]
        initial_stop = pos['stop_loss']

        # 价格上涨2%，应该触发保本止损
        self.engine._check_exit(price=2040.0, timestamp=timestamp)

        # 止损应该上移
        assert pos['stop_loss'] > initial_stop

    def test_calculate_statistics_no_trades(self):
        """测试无交易时的统计"""
        stats = self.engine._calculate_statistics()

        assert stats['total_trades'] == 0
        assert stats['win_rate'] == 0
        assert stats['total_return'] == 0

    def test_calculate_statistics_with_trades(self):
        """测试有交易时的统计"""
        timestamp = pd.Timestamp.now()

        # 模拟几笔交易
        self.engine.trades = [
            {'pnl': 100, 'pnl_pct': 0.1},
            {'pnl': -50, 'pnl_pct': -0.05},
            {'pnl': 80, 'pnl_pct': 0.08},
        ]

        self.engine.capital = 1130  # 初始1000 + 净盈利130

        # 模拟权益曲线
        self.engine.equity_curve = [
            {'equity': 1000},
            {'equity': 1100},
            {'equity': 1050},
            {'equity': 1130},
        ]

        stats = self.engine._calculate_statistics()

        assert stats['total_trades'] == 3
        assert stats['winning_trades'] == 2
        assert stats['losing_trades'] == 1
        assert stats['win_rate'] == pytest.approx(2/3, 0.01)
        assert stats['total_return'] == pytest.approx(0.13, 0.01)

    def test_max_drawdown_calculation(self):
        """测试最大回撤计算"""
        # 模拟权益曲线
        self.engine.equity_curve = [
            {'equity': 1000},
            {'equity': 1200},  # 峰值
            {'equity': 1000},  # 回撤16.7%
            {'equity': 1100},
        ]

        stats = self.engine._calculate_statistics()

        # 最大回撤应该约16.7%
        assert stats['max_drawdown'] == pytest.approx(0.167, 0.01)

    @pytest.mark.asyncio
    async def test_run_backtest_basic(self, sample_klines):
        """测试基础回测流程（需要mock OKX API）"""
        # 这个测试需要mock OKX客户端
        # 暂时跳过，在集成测试中完成
        pass


class TestBacktestStatistics:
    """回测统计功能测试"""

    def test_profit_factor_calculation(self):
        """测试盈亏比计算"""
        engine = BacktestEngine(1000)

        engine.trades = [
            {'pnl': 100},
            {'pnl': 150},
            {'pnl': -50},
            {'pnl': -30},
        ]

        stats = engine._calculate_statistics()

        # 平均盈利 = (100+150)/2 = 125
        # 平均亏损 = (-50-30)/2 = -40
        # 盈亏比 = 125/40 = 3.125
        assert stats['profit_factor'] == pytest.approx(3.125, 0.01)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
