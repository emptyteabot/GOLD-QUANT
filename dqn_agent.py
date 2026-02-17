"""
DQN强化学习代理 - 交易决策
使用Deep Q-Network学习最优交易策略
"""
import logging
import numpy as np
from collections import deque
import random
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("⚠️ PyTorch未安装,DQN代理不可用")

logger = logging.getLogger(__name__)


class DQN(nn.Module):
    """Deep Q-Network"""
    
    def __init__(self, state_size=10, action_size=3):
        super(DQN, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, action_size)
        )
    
    def forward(self, x):
        return self.fc(x)


class DQNAgent:
    """DQN交易代理"""
    
    def __init__(self, state_size=10, action_size=3):
        if not TORCH_AVAILABLE:
            logger.error("❌ PyTorch未安装,无法使用DQN代理")
            self.available = False
            return
        
        self.available = True
        self.state_size = state_size
        self.action_size = action_size  # 0=做空, 1=观望, 2=做多
        
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        
        self.model = DQN(state_size, action_size)
        self.target_model = DQN(state_size, action_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()
        
        self.update_target_model()
        
        logger.info(f"✅ DQN代理初始化 (状态维度={state_size}, 动作空间={action_size})")
    
    def update_target_model(self):
        """更新目标网络"""
        self.target_model.load_state_dict(self.model.state_dict())
    
    def remember(self, state, action, reward, next_state, done):
        """存储经验"""
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state, training=True):
        """选择动作"""
        if training and random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        self.model.eval()
        with torch.no_grad():
            q_values = self.model(state_tensor)
        
        return q_values.argmax().item()
    
    def replay(self, batch_size=32):
        """经验回放"""
        if len(self.memory) < batch_size:
            return
        
        minibatch = random.sample(self.memory, batch_size)
        
        states = torch.FloatTensor([x[0] for x in minibatch])
        actions = torch.LongTensor([x[1] for x in minibatch])
        rewards = torch.FloatTensor([x[2] for x in minibatch])
        next_states = torch.FloatTensor([x[3] for x in minibatch])
        dones = torch.FloatTensor([x[4] for x in minibatch])
        
        self.model.train()
        current_q = self.model(states).gather(1, actions.unsqueeze(1))
        
        with torch.no_grad():
            next_q = self.target_model(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        loss = self.criterion(current_q.squeeze(), target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        return loss.item()
    
    def get_state(self, klines_df, position=0):
        """从K线数据提取状态"""
        df = klines_df.tail(50).copy()
        
        # 计算特征
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        macd = ema12 - ema26
        
        returns = df['close'].pct_change()
        volatility = returns.rolling(20).std()
        
        state = [
            rsi.iloc[-1] / 100,
            macd.iloc[-1] / df['close'].iloc[-1],
            volatility.iloc[-1],
            returns.iloc[-1],
            position  # 当前持仓状态
        ]
        
        return np.array(state)
    
    def predict(self, state):
        """预测动作"""
        if not self.available:
            return {'signal': 0, 'action': '观望', 'confidence': 0.5}
        
        try:
            action = self.act(state, training=False)
            
            # 转换为信号
            if action == 0:
                signal = -1
                action_name = '做空'
            elif action == 2:
                signal = 1
                action_name = '做多'
            else:
                signal = 0
                action_name = '观望'
            
            # 计算置信度
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                q_values = self.model(state_tensor)[0]
                confidence = torch.softmax(q_values, dim=0)[action].item()
            
            return {
                'signal': signal,
                'action': action_name,
                'confidence': confidence,
                'q_values': q_values.tolist()
            }
            
        except Exception as e:
            logger.error(f"❌ DQN预测失败: {e}")
            return {'signal': 0, 'action': '观望', 'confidence': 0.5}
