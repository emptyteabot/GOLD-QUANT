"""
LSTM/GRU深度学习代理 - 时序预测
使用PyTorch实现LSTM模型,捕捉长期依赖关系
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("⚠️ PyTorch未安装,LSTM代理不可用")

logger = logging.getLogger(__name__)


class LSTMModel(nn.Module):
    """LSTM神经网络"""
    
    def __init__(self, input_size=10, hidden_size=64, num_layers=2, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 2)
        )
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        output = self.fc(last_output)
        return output


class LSTMAgent:
    """LSTM时序预测代理"""
    
    def __init__(self, sequence_length=20):
        if not TORCH_AVAILABLE:
            logger.error("❌ PyTorch未安装,无法使用LSTM代理")
            self.available = False
            return
        
        self.available = True
        self.sequence_length = sequence_length
        self.model = LSTMModel()
        self.trained = False
        self.scaler_mean = None
        self.scaler_std = None
        
        logger.info(f"✅ LSTM代理初始化 (序列长度={sequence_length})")
    
    def prepare_sequences(self, df: pd.DataFrame):
        """准备时序数据"""
        # 计算特征
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(20).std()
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        df = df.dropna()
        
        features = ['close', 'rsi', 'macd', 'returns', 'volatility', 'volume_ratio']
        data = df[features].values
        
        # 标准化
        self.scaler_mean = data.mean(axis=0)
        self.scaler_std = data.std(axis=0)
        data = (data - self.scaler_mean) / (self.scaler_std + 1e-8)
        
        # 创建序列
        X, y = [], []
        for i in range(len(data) - self.sequence_length - 5):
            X.append(data[i:i+self.sequence_length])
            future_return = df['close'].iloc[i+self.sequence_length+5] / df['close'].iloc[i+self.sequence_length] - 1
            y.append(1 if future_return > 0 else 0)
        
        return np.array(X), np.array(y)
    
    def train(self, klines_df: pd.DataFrame, epochs=50) -> bool:
        """训练LSTM模型"""
        if not self.available:
            return False
        
        try:
            if len(klines_df) < self.sequence_length + 100:
                logger.warning(f"⚠️ 数据不足({len(klines_df)}根)")
                return False
            
            X, y = self.prepare_sequences(klines_df)
            
            if len(X) < 50:
                return False
            
            X_tensor = torch.FloatTensor(X)
            y_tensor = torch.LongTensor(y)
            
            criterion = nn.CrossEntropyLoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            
            self.model.train()
            for epoch in range(epochs):
                optimizer.zero_grad()
                outputs = self.model(X_tensor)
                loss = criterion(outputs, y_tensor)
                loss.backward()
                optimizer.step()
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")
            
            self.trained = True
            
            # 计算准确率
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(X_tensor)
                _, predicted = torch.max(outputs, 1)
                accuracy = (predicted == y_tensor).float().mean()
            
            logger.info(f"✅ LSTM训练完成! 准确率: {accuracy:.1%}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ LSTM训练失败: {e}")
            return False
    
    def predict(self, recent_data: pd.DataFrame) -> Dict:
        """预测"""
        if not self.available or not self.trained:
            return {'signal': 0, 'confidence': 0.5}
        
        try:
            # 准备最近的序列
            df = recent_data.tail(self.sequence_length + 50).copy()
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            df['macd'] = ema12 - ema26
            
            df['returns'] = df['close'].pct_change()
            df['volatility'] = df['returns'].rolling(20).std()
            df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
            
            df = df.dropna()
            
            features = ['close', 'rsi', 'macd', 'returns', 'volatility', 'volume_ratio']
            data = df[features].values[-self.sequence_length:]
            
            # 标准化
            data = (data - self.scaler_mean) / (self.scaler_std + 1e-8)
            
            X = torch.FloatTensor(data).unsqueeze(0)
            
            self.model.eval()
            with torch.no_grad():
                output = self.model(X)
                proba = torch.softmax(output, dim=1)[0]
                
                signal = proba[1].item() - proba[0].item()
                confidence = max(proba).item()
            
            return {
                'signal': signal,
                'confidence': confidence,
                'up_prob': proba[1].item(),
                'down_prob': proba[0].item()
            }
            
        except Exception as e:
            logger.error(f"❌ LSTM预测失败: {e}")
            return {'signal': 0, 'confidence': 0.5}
