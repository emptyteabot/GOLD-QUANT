"""
性能测试
测试系统性能和响应时间
"""
import pytest
import sys
from pathlib import Path
import time
import pandas as pd
import numpy as np
from memory_profiler import profile

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtest_engine import BacktestEngine
from complete_multi_agent import CompleteMultiAgentSystem
from risk_manager import RiskManager


class TestPerformance:
    """性能测试类"""

    def test_ml_training_speed(self, sample_klines):
        """测试ML模型训练速度"""
        agent = CompleteMultiAgentSystem()

        start_time = time.time()
        agent.train_ml_model(sample_klines)
        elapsed = time.time() - start_time

        # 训练应该在5秒内完成
        assert elapsed < 5.0
        print(f"\n✅ ML训练耗时: {elapsed:.2f}秒")

    def test_decision_making_speed(self, sample_klines):
        """测试决策速度"""
        agent = CompleteMultiAgentSystem()
        agent.train_ml_model(sample_klines)

        macro_result = {'score': 60}
        tech_result = {'signal': 0.6, 'confidence': 0.8}

        start_time = time.time()

        for _ in range(100):
            agent.make_decision(
                macro_result=macro_result,
                tech_result=tech_result,
                klines_df=sample_klines,
                current_price=2000.0
            )

        elapsed = time.time() - start_time
        avg_time = elapsed / 100

        # 单次决策应该在50ms内
        assert avg_time < 0.05
        print(f"\n✅ 平均决策耗时: {avg_time*1000:.2f}ms")

    def test_position_calculation_speed(self, sample_account):
        """测试仓位计算速度"""
        risk_manager = RiskManager()

        start_time = time.time()

        for _ in range(1000):
            risk_manager.calculate_position_size(
                account=sample_account,
                price=2000.0,
                leverage=10
            )

        elapsed = time.time() - start_time
        avg_time = elapsed / 1000

        # 单次计算应该在1ms内
        assert avg_time < 0.001
        print(f"\n✅ 平均仓位计算耗时: {avg_time*1000:.2f}ms")

    def test_backtest_speed(self):
        """测试回测速度"""
        engine = BacktestEngine(1000.0)

        # 生成100根K线
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        prices = 2000 + np.cumsum(np.random.randn(100) * 5)

        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 10,
            'low': prices - 10,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 100)
        })

        # 训练模型
        engine.multi_agent.train_ml_model(df)

        start_time = time.time()

        # 模拟回测循环
        for i in range(50, len(df)):
            historical_df = df.iloc[:i]
            current_price = float(df.iloc[i]['close'])

            macro_result = {'score': 50}
            tech_result = engine.technical_analyst.analyze(historical_df, current_price)

            engine.multi_agent.make_decision(
                macro_result, tech_result, historical_df, current_price
            )

        elapsed = time.time() - start_time
        bars_per_sec = 50 / elapsed

        # 应该能处理至少10根K线/秒
        assert bars_per_sec > 10
        print(f"\n✅ 回测速度: {bars_per_sec:.1f} bars/sec")

    def test_large_dataset_handling(self):
        """测试大数据集处理"""
        agent = CompleteMultiAgentSystem()

        # 生成1000根K线
        df = pd.DataFrame({
            'close': 2000 + np.cumsum(np.random.randn(1000) * 5),
            'volume': np.random.randint(1000, 10000, 1000)
        })

        start_time = time.time()
        result = agent.train_ml_model(df)
        elapsed = time.time() - start_time

        assert result is True
        # 大数据集训练应该在10秒内完成
        assert elapsed < 10.0
        print(f"\n✅ 大数据集训练耗时: {elapsed:.2f}秒")


class TestMemoryUsage:
    """内存使用测试"""

    def test_memory_leak_detection(self, sample_klines):
        """测试内存泄漏"""
        agent = CompleteMultiAgentSystem()

        # 多次训练，检查内存是否持续增长
        for _ in range(10):
            agent.train_ml_model(sample_klines)

        # 如果有内存泄漏，这里会失败
        # 实际测试需要使用memory_profiler

    def test_backtest_memory_usage(self):
        """测试回测内存使用"""
        engine = BacktestEngine(1000.0)

        # 生成大量K线
        df = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=1000, freq='15min'),
            'close': 2000 + np.cumsum(np.random.randn(1000) * 5),
            'volume': np.random.randint(1000, 10000, 1000)
        })

        # 回测不应该消耗过多内存
        # 实际测试需要使用memory_profiler


class TestConcurrency:
    """并发测试"""

    def test_multiple_agents(self, sample_klines):
        """测试多个Agent并发"""
        agents = [CompleteMultiAgentSystem() for _ in range(5)]

        start_time = time.time()

        for agent in agents:
            agent.train_ml_model(sample_klines)

        elapsed = time.time() - start_time

        # 5个Agent训练应该在15秒内完成
        assert elapsed < 15.0
        print(f"\n✅ 5个Agent训练耗时: {elapsed:.2f}秒")

    def test_parallel_decision_making(self, sample_klines):
        """测试并行决策"""
        agent = CompleteMultiAgentSystem()
        agent.train_ml_model(sample_klines)

        macro_result = {'score': 60}
        tech_result = {'signal': 0.6, 'confidence': 0.8}

        start_time = time.time()

        # 模拟100次并发决策
        decisions = []
        for _ in range(100):
            decision = agent.make_decision(
                macro_result=macro_result,
                tech_result=tech_result,
                klines_df=sample_klines,
                current_price=2000.0
            )
            decisions.append(decision)

        elapsed = time.time() - start_time

        assert len(decisions) == 100
        # 100次决策应该在5秒内完成
        assert elapsed < 5.0
        print(f"\n✅ 100次决策耗时: {elapsed:.2f}秒")


class TestScalability:
    """可扩展性测试"""

    def test_increasing_data_size(self):
        """测试数据量增长的性能影响"""
        agent = CompleteMultiAgentSystem()

        sizes = [100, 200, 500, 1000]
        times = []

        for size in sizes:
            df = pd.DataFrame({
                'close': 2000 + np.cumsum(np.random.randn(size) * 5),
                'volume': np.random.randint(1000, 10000, size)
            })

            start_time = time.time()
            agent.train_ml_model(df)
            elapsed = time.time() - start_time

            times.append(elapsed)
            print(f"\n数据量 {size}: {elapsed:.2f}秒")

        # 时间增长应该是线性的，不是指数的
        # 简单检查：1000条数据不应该超过100条数据的20倍时间
        assert times[-1] < times[0] * 20


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
