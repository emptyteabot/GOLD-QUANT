"""
机器学习模型单元测试
测试CompleteMultiAgentSystem的ML功能
"""
import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from complete_multi_agent import CompleteMultiAgentSystem


class TestMLModels:
    """机器学习模型测试类"""

    def setup_method(self):
        """每个测试前初始化"""
        self.agent = CompleteMultiAgentSystem()

    def test_initialization(self):
        """测试初始化"""
        assert self.agent.ml_trained is False
        assert self.agent.ml_model is not None
        assert 'macro' in self.agent.weights
        assert 'ml' in self.agent.weights

    def test_train_ml_model_insufficient_data(self):
        """测试数据不足时的训练"""
        # 只有50根K线
        df = pd.DataFrame({
            'close': np.random.randn(50) + 2000,
            'volume': np.random.randint(1000, 10000, 50)
        })

        result = self.agent.train_ml_model(df)

        # 数据不足，应该返回False
        assert result is False
        assert self.agent.ml_trained is False

    def test_train_ml_model_success(self, sample_klines):
        """测试成功训练模型"""
        result = self.agent.train_ml_model(sample_klines)

        assert result is True
        assert self.agent.ml_trained is True

    def test_ml_features_calculation(self, sample_klines):
        """测试特征计算"""
        self.agent.train_ml_model(sample_klines)

        # 验证模型已训练
        assert self.agent.ml_model is not None
        assert hasattr(self.agent.ml_model, 'feature_importances_')

    def test_make_decision_without_training(self, sample_klines):
        """测试未训练时的决策"""
        macro_result = {'score': 50}
        tech_result = {'signal': 0.5, 'confidence': 0.7}

        decision = self.agent.make_decision(
            macro_result=macro_result,
            tech_result=tech_result,
            klines_df=sample_klines,
            current_price=2000.0
        )

        # 应该返回决策，但ML权重为0
        assert 'signal' in decision
        assert 'confidence' in decision
        assert 'leverage' in decision

    def test_make_decision_with_training(self, sample_klines):
        """测试训练后的决策"""
        # 先训练模型
        self.agent.train_ml_model(sample_klines)

        macro_result = {'score': 60}
        tech_result = {'signal': 0.6, 'confidence': 0.8}

        decision = self.agent.make_decision(
            macro_result=macro_result,
            tech_result=tech_result,
            klines_df=sample_klines,
            current_price=2000.0
        )

        assert 'signal' in decision
        assert 'confidence' in decision
        assert -1 <= decision['signal'] <= 1
        assert 0 <= decision['confidence'] <= 1

    def test_ml_prediction_range(self, sample_klines):
        """测试ML预测值范围"""
        self.agent.train_ml_model(sample_klines)

        # 准备特征
        df = sample_klines.copy()

        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # 计算其他特征
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        df['adx'] = df['close'].rolling(14).std() / df['close'].rolling(14).mean() * 100
        df['volatility'] = df['close'].pct_change().rolling(20).std()
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()

        df = df.dropna()

        if len(df) > 0:
            features = df[['rsi', 'macd', 'adx', 'volatility', 'volume_ratio']].iloc[-1:].values
            prediction = self.agent.ml_model.predict_proba(features)

            # 预测概率应该在0-1之间
            assert 0 <= prediction[0][0] <= 1
            assert 0 <= prediction[0][1] <= 1
            # 概率和应该为1
            assert abs(sum(prediction[0]) - 1.0) < 0.01

    def test_agent_weights_sum(self):
        """测试Agent权重总和"""
        total_weight = sum(self.agent.weights.values())

        # 权重总和应该为1
        assert abs(total_weight - 1.0) < 0.01

    def test_signal_aggregation(self, sample_klines):
        """测试信号聚合"""
        self.agent.train_ml_model(sample_klines)

        # 所有Agent都看多
        macro_result = {'score': 80}
        tech_result = {'signal': 0.8, 'confidence': 0.9}

        decision = self.agent.make_decision(
            macro_result=macro_result,
            tech_result=tech_result,
            klines_df=sample_klines,
            current_price=2000.0
        )

        # 综合信号应该为正
        assert decision['signal'] > 0

    def test_confidence_calculation(self, sample_klines):
        """测试置信度计算"""
        self.agent.train_ml_model(sample_klines)

        # 高一致性信号
        macro_result = {'score': 80}
        tech_result = {'signal': 0.8, 'confidence': 0.9}

        decision = self.agent.make_decision(
            macro_result=macro_result,
            tech_result=tech_result,
            klines_df=sample_klines,
            current_price=2000.0
        )

        # 置信度应该较高
        assert decision['confidence'] > 0.5

    def test_leverage_adjustment(self, sample_klines):
        """测试杠杆调整"""
        self.agent.train_ml_model(sample_klines)

        # 高置信度信号
        macro_result = {'score': 90}
        tech_result = {'signal': 0.9, 'confidence': 0.95}

        decision = self.agent.make_decision(
            macro_result=macro_result,
            tech_result=tech_result,
            klines_df=sample_klines,
            current_price=2000.0
        )

        # 杠杆应该在合理范围
        assert 1 <= decision['leverage'] <= 20


class TestModelPersistence:
    """模型持久化测试"""

    def test_model_retrain(self, sample_klines):
        """测试模型重新训练"""
        agent = CompleteMultiAgentSystem()

        # 第一次训练
        agent.train_ml_model(sample_klines)
        assert agent.ml_trained is True

        # 第二次训练（应该覆盖）
        agent.train_ml_model(sample_klines)
        assert agent.ml_trained is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
