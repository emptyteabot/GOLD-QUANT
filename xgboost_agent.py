"""
XGBoost机器学习代理 - 增强版
使用XGBoost替代RandomForest,提升预测准确率
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("⚠️ XGBoost未安装,将使用RandomForest")
    from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger(__name__)


class XGBoostAgent:
    """XGBoost机器学习代理"""
    
    def __init__(self):
        if XGBOOST_AVAILABLE:
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='logloss',
                use_label_encoder=False
            )
        else:
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
        self.trained = False
        logger.info(f"✅ XGBoost代理初始化 (使用{'XGBoost' if XGBOOST_AVAILABLE else 'RandomForest'})")
    
    def train(self, klines_df: pd.DataFrame) -> bool:
        """训练模型"""
        try:
            if len(klines_df) < 100:
                logger.warning(f"⚠️ 数据不足({len(klines_df)}根)")
                return False
            
            df = klines_df.copy()
            
            # 计算技术指标
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            df['macd'] = ema12 - ema26
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            
            df['volatility'] = df['close'].pct_change().rolling(20).std()
            df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
            
            # 动量指标
            df['momentum'] = df['close'].pct_change(10)
            df['roc'] = (df['close'] - df['close'].shift(10)) / df['close'].shift(10)
            
            # 标签
            df['future_return'] = df['close'].shift(-5) / df['close'] - 1
            df['label'] = (df['future_return'] > 0).astype(int)
            
            df = df.dropna()
            
            if len(df) < 50:
                return False
            
            features = ['rsi', 'macd', 'macd_signal', 'sma_20', 'sma_50', 
                       'volatility', 'volume_ratio', 'momentum', 'roc']
            X = df[features].values
            y = df['label'].values
            
            self.model.fit(X, y)
            self.trained = True
            
            score = self.model.score(X, y)
            logger.info(f"✅ XGBoost训练完成! 准确率: {score:.1%}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ XGBoost训练失败: {e}")
            return False
    
    def predict(self, features: Dict) -> Dict:
        """预测"""
        try:
            feature_vector = np.array([[
                features.get('rsi', 50),
                features.get('macd', 0),
                features.get('macd_signal', 0),
                features.get('sma_20', 0),
                features.get('sma_50', 0),
                features.get('volatility', 0.02),
                features.get('volume_ratio', 1.0),
                features.get('momentum', 0),
                features.get('roc', 0)
            ]])
            
            if self.trained:
                proba = self.model.predict_proba(feature_vector)[0]
                signal = proba[1] - proba[0]
                confidence = max(proba)
                
                return {
                    'signal': signal,
                    'confidence': confidence,
                    'up_prob': proba[1],
                    'down_prob': proba[0]
                }
            else:
                return {'signal': 0, 'confidence': 0.5, 'up_prob': 0.5, 'down_prob': 0.5}
                
        except Exception as e:
            logger.error(f"❌ XGBoost预测失败: {e}")
            return {'signal': 0, 'confidence': 0.5, 'up_prob': 0.5, 'down_prob': 0.5}
