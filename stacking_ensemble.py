"""
Stacking集成学习 - 元学习器
组合多个基础模型,用元学习器做最终预测
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List
from sklearn.ensemble import RandomForestClassifier
try:
    import xgboost as xgb
    from lightgbm import LGBMClassifier
    ADVANCED_MODELS = True
except ImportError:
    ADVANCED_MODELS = False
    logging.warning("⚠️ XGBoost/LightGBM未安装,使用基础模型")

logger = logging.getLogger(__name__)


class StackingEnsemble:
    """Stacking集成学习器"""
    
    def __init__(self):
        # 基础模型
        self.base_models = []
        
        if ADVANCED_MODELS:
            self.base_models = [
                ('rf', RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)),
                ('xgb', xgb.XGBClassifier(n_estimators=50, max_depth=5, learning_rate=0.1, random_state=42, eval_metric='logloss', use_label_encoder=False)),
                ('lgb', LGBMClassifier(n_estimators=50, max_depth=5, learning_rate=0.1, random_state=42, verbose=-1))
            ]
        else:
            self.base_models = [
                ('rf1', RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)),
                ('rf2', RandomForestClassifier(n_estimators=100, max_depth=7, random_state=43)),
                ('rf3', RandomForestClassifier(n_estimators=30, max_depth=3, random_state=44))
            ]
        
        # 元学习器
        self.meta_model = RandomForestClassifier(n_estimators=50, max_depth=3, random_state=42)
        
        self.trained = False
        logger.info(f"✅ Stacking集成初始化 ({len(self.base_models)}个基础模型)")
    
    def train(self, klines_df: pd.DataFrame) -> bool:
        """训练Stacking模型"""
        try:
            if len(klines_df) < 100:
                logger.warning(f"⚠️ 数据不足({len(klines_df)}根)")
                return False
            
            df = klines_df.copy()
            
            # 计算特征
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
            df['momentum'] = df['close'].pct_change(10)
            
            # 标签
            df['future_return'] = df['close'].shift(-5) / df['close'] - 1
            df['label'] = (df['future_return'] > 0).astype(int)
            
            df = df.dropna()
            
            if len(df) < 50:
                return False
            
            features = ['rsi', 'macd', 'macd_signal', 'sma_20', 'sma_50', 
                       'volatility', 'volume_ratio', 'momentum']
            X = df[features].values
            y = df['label'].values
            
            # 训练基础模型并生成元特征
            meta_features = []
            for name, model in self.base_models:
                logger.info(f"训练基础模型: {name}")
                model.fit(X, y)
                
                # 生成预测概率作为元特征
                proba = model.predict_proba(X)
                meta_features.append(proba)
            
            # 组合元特征
            X_meta = np.hstack(meta_features)
            
            # 训练元学习器
            logger.info("训练元学习器")
            self.meta_model.fit(X_meta, y)
            
            self.trained = True
            
            # 计算准确率
            final_pred = self.meta_model.predict(X_meta)
            accuracy = (final_pred == y).mean()
            
            logger.info(f"✅ Stacking训练完成! 准确率: {accuracy:.1%}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Stacking训练失败: {e}")
            return False
    
    def predict(self, features: Dict) -> Dict:
        """预测"""
        try:
            if not self.trained:
                return {'signal': 0, 'confidence': 0.5}
            
            feature_vector = np.array([[
                features.get('rsi', 50),
                features.get('macd', 0),
                features.get('macd_signal', 0),
                features.get('sma_20', 0),
                features.get('sma_50', 0),
                features.get('volatility', 0.02),
                features.get('volume_ratio', 1.0),
                features.get('momentum', 0)
            ]])
            
            # 基础模型预测
            meta_features = []
            for name, model in self.base_models:
                proba = model.predict_proba(feature_vector)
                meta_features.append(proba)
            
            X_meta = np.hstack(meta_features)
            
            # 元学习器预测
            final_proba = self.meta_model.predict_proba(X_meta)[0]
            signal = final_proba[1] - final_proba[0]
            confidence = max(final_proba)
            
            return {
                'signal': signal,
                'confidence': confidence,
                'up_prob': final_proba[1],
                'down_prob': final_proba[0]
            }
            
        except Exception as e:
            logger.error(f"❌ Stacking预测失败: {e}")
            return {'signal': 0, 'confidence': 0.5}
