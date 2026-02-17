"""
机器学习预测模块 - 增强版
参考: 251129神经网络入门.ipynb + Advances in Financial Machine Learning

功能增强:
1. LSTM价格预测 (时间序列)
2. XGBoost信号分类 (涨跌方向)
3. 在线学习 (实时更新)
4. 集成学习 (多模型融合)
5. 特征重要性分析
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, List
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb
from collections import deque
import warnings
warnings.filterwarnings('ignore')


class GoldLSTMPredictor(nn.Module):
    """
    LSTM 黄金价格预测模型
    
    适用于捕捉黄金价格的时间序列特征
    """
    
    def __init__(self, input_size: int = 10, hidden_size: int = 64, num_layers: int = 2):
        """
        Args:
            input_size: 输入特征数量
            hidden_size: LSTM 隐藏层大小
            num_layers: LSTM 层数
        """
        super(GoldLSTMPredictor, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM 层
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0
        )
        
        # 全连接层
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(32, 1)
    
    def forward(self, x):
        """
        前向传播
        
        Args:
            x: (batch_size, sequence_length, input_size)
        
        Returns:
            prediction: (batch_size, 1)
        """
        # LSTM
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # 取最后一个时间步的输出
        last_output = lstm_out[:, -1, :]
        
        # 全连接层
        out = self.fc1(last_output)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        
        return out


class GoldMLPPredictor(nn.Module):
    """
    多层感知机 (MLP) 黄金价格预测模型
    
    适用于基于特征的预测 (不考虑时间序列)
    """
    
    def __init__(self, input_size: int = 20):
        """
        Args:
            input_size: 输入特征数量
        """
        super(GoldMLPPredictor, self).__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(32, 1)
        )
    
    def forward(self, x):
        """
        前向传播
        
        Args:
            x: (batch_size, input_size)
        
        Returns:
            prediction: (batch_size, 1)
        """
        return self.network(x)


class GoldPricePredictor:
    """
    黄金价格预测器 (封装)
    
    提供训练、预测、评估的完整流程
    """
    
    def __init__(self, model_type: str = 'lstm', device: str = 'cpu'):
        """
        Args:
            model_type: 'lstm' 或 'mlp'
            device: 'cpu' 或 'cuda'
        """
        self.model_type = model_type
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_data(self, 
                     df: pd.DataFrame, 
                     feature_cols: list,
                     target_col: str = 'future_return',
                     sequence_length: int = 24) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        准备训练数据
        
        Args:
            df: 数据框
            feature_cols: 特征列名
            target_col: 目标列名
            sequence_length: 序列长度 (仅 LSTM 使用)
        
        Returns:
            (X, y): 特征和标签的 Tensor
        """
        # 提取特征和标签
        X = df[feature_cols].values
        y = df[target_col].values
        
        # 标准化
        X_scaled = self.scaler.fit_transform(X)
        
        if self.model_type == 'lstm':
            # 构建序列数据
            X_seq = []
            y_seq = []
            
            for i in range(len(X_scaled) - sequence_length):
                X_seq.append(X_scaled[i:i+sequence_length])
                y_seq.append(y[i+sequence_length])
            
            X_tensor = torch.FloatTensor(np.array(X_seq)).to(self.device)
            y_tensor = torch.FloatTensor(np.array(y_seq)).unsqueeze(1).to(self.device)
        else:
            # MLP 直接使用特征
            X_tensor = torch.FloatTensor(X_scaled).to(self.device)
            y_tensor = torch.FloatTensor(y).unsqueeze(1).to(self.device)
        
        return X_tensor, y_tensor
    
    def train(self, 
              X_train: torch.Tensor, 
              y_train: torch.Tensor,
              epochs: int = 100,
              batch_size: int = 32,
              learning_rate: float = 0.001):
        """
        训练模型
        
        Args:
            X_train: 训练特征
            y_train: 训练标签
            epochs: 训练轮数
            batch_size: 批次大小
            learning_rate: 学习率
        """
        # 初始化模型
        if self.model_type == 'lstm':
            input_size = X_train.shape[2]
            self.model = GoldLSTMPredictor(input_size=input_size).to(self.device)
        else:
            input_size = X_train.shape[1]
            self.model = GoldMLPPredictor(input_size=input_size).to(self.device)
        
        # 损失函数和优化器
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # 训练循环
        self.model.train()
        
        for epoch in range(epochs):
            total_loss = 0
            num_batches = 0
            
            # 分批训练
            for i in range(0, len(X_train), batch_size):
                batch_X = X_train[i:i+batch_size]
                batch_y = y_train[i:i+batch_size]
                
                # 前向传播
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                
                # 反向传播
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                num_batches += 1
            
            # 打印进度
            if (epoch + 1) % 10 == 0:
                avg_loss = total_loss / num_batches
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.6f}')
        
        self.is_trained = True
        print("✅ 模型训练完成！")
    
    def predict(self, X: torch.Tensor) -> np.ndarray:
        """
        预测
        
        Args:
            X: 输入特征
        
        Returns:
            predictions: 预测结果
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练！请先调用 train() 方法")
        
        self.model.eval()
        
        with torch.no_grad():
            predictions = self.model(X)
        
        return predictions.cpu().numpy()
    
    def evaluate(self, X_test: torch.Tensor, y_test: torch.Tensor) -> dict:
        """
        评估模型
        
        Returns:
            metrics: {'mse', 'rmse', 'mae', 'direction_accuracy'}
        """
        predictions = self.predict(X_test)
        y_true = y_test.cpu().numpy()
        
        # 计算指标
        mse = np.mean((predictions - y_true) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions - y_true))
        
        # 方向准确率 (预测涨跌方向)
        pred_direction = (predictions > 0).astype(int)
        true_direction = (y_true > 0).astype(int)
        direction_accuracy = np.mean(pred_direction == true_direction)
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'direction_accuracy': direction_accuracy
        }
        
        return metrics
    
    def save_model(self, path: str):
        """保存模型"""
        if not self.is_trained:
            raise ValueError("模型尚未训练！")
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_type': self.model_type,
            'scaler': self.scaler
        }, path)
        
        print(f"✅ 模型已保存到: {path}")
    
    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        
        self.model_type = checkpoint['model_type']
        self.scaler = checkpoint['scaler']
        
        # 重建模型 (需要知道输入大小)
        # 这里简化处理，实际使用时需要保存模型结构
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.is_trained = True
        
        print(f"✅ 模型已加载: {path}")


class XGBoostSignalClassifier:
    """
    XGBoost信号分类器
    
    预测涨跌方向 (多头/空头/观望)
    """
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 6):
        """
        Args:
            n_estimators: 树的数量
            max_depth: 树的最大深度
        """
        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=0.1,
            objective='multi:softmax',
            num_class=3,  # 0=空头, 1=观望, 2=多头
            random_state=42
        )
        self.scaler = RobustScaler()
        self.is_trained = False
        self.feature_importance = None
    
    def prepare_labels(self, returns: np.ndarray, threshold: float = 0.001) -> np.ndarray:
        """
        将收益率转换为分类标签
        
        Args:
            returns: 未来收益率
            threshold: 分类阈值
        
        Returns:
            labels: 0=空头, 1=观望, 2=多头
        """
        labels = np.ones(len(returns), dtype=int)  # 默认观望
        labels[returns > threshold] = 2  # 多头
        labels[returns < -threshold] = 0  # 空头
        return labels
    
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None):
        """
        训练模型
        
        Args:
            X: 特征矩阵
            y: 标签 (0/1/2)
            feature_names: 特征名称列表
        """
        # 标准化
        X_scaled = self.scaler.fit_transform(X)
        
        # 训练
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # 特征重要性
        self.feature_importance = self.model.feature_importances_
        
        if feature_names:
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': self.feature_importance
            }).sort_values('importance', ascending=False)
            
            print("\n📊 特征重要性 Top 10:")
            print(importance_df.head(10).to_string(index=False))
        
        print("✅ XGBoost模型训练完成！")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测信号
        
        Returns:
            signals: 0=空头, 1=观望, 2=多头
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练！")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        预测概率
        
        Returns:
            probabilities: (n_samples, 3) 每个类别的概率
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练！")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        评估模型
        
        Returns:
            metrics: 准确率、精确率、召回率等
        """
        predictions = self.predict(X)
        
        accuracy = np.mean(predictions == y)
        
        # 计算每个类别的精确率和召回率
        metrics = {'accuracy': accuracy}
        
        for label, name in [(0, 'short'), (1, 'neutral'), (2, 'long')]:
            mask_true = (y == label)
            mask_pred = (predictions == label)
            
            if mask_pred.sum() > 0:
                precision = np.sum(mask_true & mask_pred) / mask_pred.sum()
            else:
                precision = 0.0
            
            if mask_true.sum() > 0:
                recall = np.sum(mask_true & mask_pred) / mask_true.sum()
            else:
                recall = 0.0
            
            metrics[f'{name}_precision'] = precision
            metrics[f'{name}_recall'] = recall
        
        return metrics


class OnlineLearningPredictor:
    """
    在线学习预测器
    
    实时更新模型，适应市场变化
    """
    
    def __init__(self, base_model: GoldPricePredictor, buffer_size: int = 1000):
        """
        Args:
            base_model: 基础预测模型
            buffer_size: 数据缓冲区大小
        """
        self.base_model = base_model
        self.buffer_size = buffer_size
        
        # 数据缓冲区
        self.X_buffer = deque(maxlen=buffer_size)
        self.y_buffer = deque(maxlen=buffer_size)
        
        self.update_count = 0
        self.update_interval = 100  # 每100个样本更新一次
    
    def add_sample(self, X: np.ndarray, y: float):
        """
        添加新样本
        
        Args:
            X: 特征向量
            y: 真实标签
        """
        self.X_buffer.append(X)
        self.y_buffer.append(y)
        
        self.update_count += 1
        
        # 定期更新模型
        if self.update_count >= self.update_interval and len(self.X_buffer) >= 100:
            self.update_model()
            self.update_count = 0
    
    def update_model(self):
        """
        使用缓冲区数据更新模型
        """
        print(f"🔄 在线学习: 使用 {len(self.X_buffer)} 个样本更新模型...")
        
        # 转换为张量
        X_array = np.array(list(self.X_buffer))
        y_array = np.array(list(self.y_buffer))
        
        if self.base_model.model_type == 'lstm':
            # LSTM需要序列数据
            sequence_length = 24
            if len(X_array) > sequence_length:
                X_seq = []
                y_seq = []
                for i in range(len(X_array) - sequence_length):
                    X_seq.append(X_array[i:i+sequence_length])
                    y_seq.append(y_array[i+sequence_length])
                
                X_tensor = torch.FloatTensor(np.array(X_seq)).to(self.base_model.device)
                y_tensor = torch.FloatTensor(np.array(y_seq)).unsqueeze(1).to(self.base_model.device)
            else:
                return  # 数据不足
        else:
            X_tensor = torch.FloatTensor(X_array).to(self.base_model.device)
            y_tensor = torch.FloatTensor(y_array).unsqueeze(1).to(self.base_model.device)
        
        # 微调模型 (少量epoch)
        self.base_model.train(X_tensor, y_tensor, epochs=10, batch_size=32, learning_rate=0.0001)
        
        print("✅ 模型更新完成！")
    
    def predict(self, X: torch.Tensor) -> np.ndarray:
        """
        预测
        """
        return self.base_model.predict(X)


class EnsemblePredictor:
    """
    集成预测器 - 增强版
    
    结合LSTM、MLP、XGBoost的预测结果
    """
    
    def __init__(self, 
                 lstm_model: Optional[GoldPricePredictor] = None,
                 mlp_model: Optional[GoldPricePredictor] = None,
                 xgb_model: Optional[XGBoostSignalClassifier] = None,
                 weights: Optional[Dict[str, float]] = None):
        """
        Args:
            lstm_model: LSTM预测器
            mlp_model: MLP预测器
            xgb_model: XGBoost分类器
            weights: 权重字典 {'lstm': 0.4, 'mlp': 0.3, 'xgb': 0.3}
        """
        self.lstm_model = lstm_model
        self.mlp_model = mlp_model
        self.xgb_model = xgb_model
        
        if weights is None:
            # 默认权重
            self.weights = {'lstm': 0.4, 'mlp': 0.3, 'xgb': 0.3}
        else:
            self.weights = weights
    
    def predict_regression(self, X_lstm: torch.Tensor, X_mlp: torch.Tensor) -> np.ndarray:
        """
        回归预测 (预测具体价格变化)
        
        Args:
            X_lstm: LSTM输入 (序列数据)
            X_mlp: MLP输入 (特征数据)
        
        Returns:
            ensemble_prediction: 集成预测结果
        """
        predictions = []
        weights = []
        
        if self.lstm_model and self.lstm_model.is_trained:
            pred_lstm = self.lstm_model.predict(X_lstm)
            predictions.append(pred_lstm)
            weights.append(self.weights['lstm'])
        
        if self.mlp_model and self.mlp_model.is_trained:
            pred_mlp = self.mlp_model.predict(X_mlp)
            predictions.append(pred_mlp)
            weights.append(self.weights['mlp'])
        
        if not predictions:
            raise ValueError("没有可用的回归模型！")
        
        # 加权平均
        weights = np.array(weights) / sum(weights)
        ensemble_pred = sum(pred * w for pred, w in zip(predictions, weights))
        
        return ensemble_pred
    
    def predict_signal(self, X_lstm: torch.Tensor, X_mlp: torch.Tensor, X_xgb: np.ndarray) -> Dict[str, any]:
        """
        信号预测 (综合多个模型)
        
        Returns:
            {
                'signal': 0/1/2 (空头/观望/多头),
                'confidence': 0-1 (置信度),
                'price_change': 预测价格变化,
                'details': 各模型的预测详情
            }
        """
        details = {}
        
        # 1. LSTM价格预测
        if self.lstm_model and self.lstm_model.is_trained:
            pred_lstm = self.lstm_model.predict(X_lstm)
            details['lstm_price_change'] = float(pred_lstm[0][0])
        
        # 2. MLP价格预测
        if self.mlp_model and self.mlp_model.is_trained:
            pred_mlp = self.mlp_model.predict(X_mlp)
            details['mlp_price_change'] = float(pred_mlp[0][0])
        
        # 3. XGBoost信号分类
        if self.xgb_model and self.xgb_model.is_trained:
            pred_xgb = self.xgb_model.predict(X_xgb)
            proba_xgb = self.xgb_model.predict_proba(X_xgb)
            details['xgb_signal'] = int(pred_xgb[0])
            details['xgb_confidence'] = float(proba_xgb[0][pred_xgb[0]])
        
        # 综合决策
        signal = 1  # 默认观望
        confidence = 0.5
        
        # 如果有价格预测，转换为信号
        price_changes = []
        if 'lstm_price_change' in details:
            price_changes.append(details['lstm_price_change'])
        if 'mlp_price_change' in details:
            price_changes.append(details['mlp_price_change'])
        
        if price_changes:
            avg_price_change = np.mean(price_changes)
            details['avg_price_change'] = avg_price_change
            
            # 转换为信号
            if avg_price_change > 0.002:  # 涨幅 > 0.2%
                signal = 2  # 多头
                confidence = min(abs(avg_price_change) * 100, 1.0)
            elif avg_price_change < -0.002:  # 跌幅 > 0.2%
                signal = 0  # 空头
                confidence = min(abs(avg_price_change) * 100, 1.0)
        
        # 如果有XGBoost信号，进行投票
        if 'xgb_signal' in details:
            xgb_signal = details['xgb_signal']
            xgb_confidence = details['xgb_confidence']
            
            # 加权投票
            if xgb_confidence > 0.6:  # XGBoost置信度高
                signal = int((signal + xgb_signal * 2) / 3)  # XGBoost权重更高
                confidence = (confidence + xgb_confidence * 2) / 3
            else:
                signal = int((signal * 2 + xgb_signal) / 3)  # 价格预测权重更高
                confidence = (confidence * 2 + xgb_confidence) / 3
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': details
        }
    
    def get_signal_name(self, signal: int) -> str:
        """
        获取信号名称
        """
        names = {0: '空头', 1: '观望', 2: '多头'}
        return names.get(signal, '未知')


# 使用示例
if __name__ == "__main__":
    print("🧪 机器学习预测模块测试 - 增强版\n")
    
    # 生成模拟数据
    np.random.seed(42)
    n_samples = 1000
    
    # 模拟特征 (价格、RSI、MACD等)
    features = np.random.randn(n_samples, 10)
    
    # 模拟目标 (未来1小时收益率)
    target = np.random.randn(n_samples) * 0.01
    
    # 创建 DataFrame
    feature_cols = [f'feature_{i}' for i in range(10)]
    df = pd.DataFrame(features, columns=feature_cols)
    df['future_return'] = target
    
    # 划分训练集和测试集
    train_size = int(0.8 * len(df))
    train_df = df[:train_size]
    test_df = df[train_size:]
    
    print("=" * 70)
    print("1. LSTM 模型测试")
    print("=" * 70)
    
    # 初始化 LSTM 预测器
    lstm_predictor = GoldPricePredictor(model_type='lstm', device='cpu')
    
    # 准备数据
    X_train, y_train = lstm_predictor.prepare_data(train_df, feature_cols, sequence_length=24)
    X_test, y_test = lstm_predictor.prepare_data(test_df, feature_cols, sequence_length=24)
    
    print(f"训练集大小: {X_train.shape}")
    print(f"测试集大小: {X_test.shape}")
    
    # 训练模型
    print("\n开始训练...")
    lstm_predictor.train(X_train, y_train, epochs=30, batch_size=32)
    
    # 评估模型
    print("\n评估模型...")
    metrics = lstm_predictor.evaluate(X_test, y_test)
    print(f"RMSE: {metrics['rmse']:.6f}")
    print(f"MAE: {metrics['mae']:.6f}")
    print(f"方向准确率: {metrics['direction_accuracy']:.2%}")
    
    print("\n" + "=" * 70)
    print("2. MLP 模型测试")
    print("=" * 70)
    
    # 初始化 MLP 预测器
    mlp_predictor = GoldPricePredictor(model_type='mlp', device='cpu')
    
    # 准备数据 (MLP 不需要序列)
    X_train_mlp, y_train_mlp = mlp_predictor.prepare_data(train_df, feature_cols)
    X_test_mlp, y_test_mlp = mlp_predictor.prepare_data(test_df, feature_cols)
    
    # 训练模型
    print("\n开始训练...")
    mlp_predictor.train(X_train_mlp, y_train_mlp, epochs=30, batch_size=32)
    
    # 评估模型
    print("\n评估模型...")
    metrics_mlp = mlp_predictor.evaluate(X_test_mlp, y_test_mlp)
    print(f"RMSE: {metrics_mlp['rmse']:.6f}")
    print(f"MAE: {metrics_mlp['mae']:.6f}")
    print(f"方向准确率: {metrics_mlp['direction_accuracy']:.2%}")
    
    print("\n" + "=" * 70)
    print("3. XGBoost 信号分类测试")
    print("=" * 70)
    
    # 初始化 XGBoost 分类器
    xgb_classifier = XGBoostSignalClassifier(n_estimators=100, max_depth=6)
    
    # 准备标签
    train_labels = xgb_classifier.prepare_labels(train_df['future_return'].values)
    test_labels = xgb_classifier.prepare_labels(test_df['future_return'].values)
    
    print(f"训练集标签分布: 空头={np.sum(train_labels==0)}, 观望={np.sum(train_labels==1)}, 多头={np.sum(train_labels==2)}")
    
    # 训练模型
    print("\n开始训练...")
    xgb_classifier.train(train_df[feature_cols].values, train_labels, feature_names=feature_cols)
    
    # 评估模型
    print("\n评估模型...")
    metrics_xgb = xgb_classifier.evaluate(test_df[feature_cols].values, test_labels)
    print(f"准确率: {metrics_xgb['accuracy']:.2%}")
    print(f"多头精确率: {metrics_xgb['long_precision']:.2%}")
    print(f"多头召回率: {metrics_xgb['long_recall']:.2%}")
    print(f"空头精确率: {metrics_xgb['short_precision']:.2%}")
    print(f"空头召回率: {metrics_xgb['short_recall']:.2%}")
    
    print("\n" + "=" * 70)
    print("4. 集成预测器测试")
    print("=" * 70)
    
    # 初始化集成预测器
    ensemble = EnsemblePredictor(
        lstm_model=lstm_predictor,
        mlp_model=mlp_predictor,
        xgb_model=xgb_classifier,
        weights={'lstm': 0.4, 'mlp': 0.3, 'xgb': 0.3}
    )
    
    # 测试预测
    print("\n测试集成预测...")
    test_sample_lstm = X_test[:1]
    test_sample_mlp = X_test_mlp[:1]
    test_sample_xgb = test_df[feature_cols].values[:1]
    
    result = ensemble.predict_signal(test_sample_lstm, test_sample_mlp, test_sample_xgb)
    
    print(f"\n集成预测结果:")
    print(f"  信号: {ensemble.get_signal_name(result['signal'])}")
    print(f"  置信度: {result['confidence']:.2%}")
    print(f"  详情: {result['details']}")
    
    print("\n" + "=" * 70)
    print("5. 在线学习测试")
    print("=" * 70)
    
    # 初始化在线学习预测器
    online_predictor = OnlineLearningPredictor(mlp_predictor, buffer_size=200)
    
    print("\n模拟在线学习过程...")
    print("添加新样本并定期更新模型...")
    
    # 模拟添加新样本
    for i in range(150):
        sample_X = test_df[feature_cols].values[i % len(test_df)]
        sample_y = test_df['future_return'].values[i % len(test_df)]
        online_predictor.add_sample(sample_X, sample_y)
        
        if (i + 1) % 50 == 0:
            print(f"  已添加 {i+1} 个样本...")
    
    print("\n✅ 机器学习预测模块测试完成！")
    print("\n" + "=" * 70)
    print("📊 功能总结")
    print("=" * 70)
    print("✅ LSTM价格预测 - 捕捉时间序列特征")
    print("✅ MLP价格预测 - 基于特征的快速预测")
    print("✅ XGBoost信号分类 - 涨跌方向判断 + 特征重要性")
    print("✅ 集成预测器 - 多模型融合决策")
    print("✅ 在线学习 - 实时更新适应市场")
    print("\n💡 实际使用建议:")
    print("   1. 使用真实黄金价格数据和完整特征工程")
    print("   2. 进行充分的回测和参数优化")
    print("   3. 使用时间序列交叉验证避免前视偏差")
    print("   4. 定期重新训练模型适应市场变化")
    print("   5. 结合风险管理模块控制仓位和止损")
    print("=" * 70)


