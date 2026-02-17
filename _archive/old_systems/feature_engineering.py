"""
特征工程模块 - 专业版
基于机器学习资料，构建完整的特征体系
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import talib


class FeatureEngineer:
    """特征工程器"""
    
    def __init__(self):
        self.feature_names = []
        self.feature_importance = {}
    
    # ==================== 技术指标特征 ====================
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        基于 TA-Lib 和自定义指标
        
        Args:
            df: DataFrame with columns [open, high, low, close, volume]
        
        Returns:
            DataFrame with additional technical indicator columns
        """
        df = df.copy()
        
        # 价格数据
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        # 1. 趋势指标
        # SMA - 简单移动平均
        df['sma_5'] = talib.SMA(close, timeperiod=5)
        df['sma_10'] = talib.SMA(close, timeperiod=10)
        df['sma_20'] = talib.SMA(close, timeperiod=20)
        df['sma_60'] = talib.SMA(close, timeperiod=60)
        
        # EMA - 指数移动平均
        df['ema_5'] = talib.EMA(close, timeperiod=5)
        df['ema_10'] = talib.EMA(close, timeperiod=10)
        df['ema_20'] = talib.EMA(close, timeperiod=20)
        
        # MACD - 移动平均收敛散度
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            close, fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # 2. 动量指标
        # RSI - 相对强弱指标
        df['rsi_6'] = talib.RSI(close, timeperiod=6)
        df['rsi_12'] = talib.RSI(close, timeperiod=12)
        df['rsi_24'] = talib.RSI(close, timeperiod=24)
        
        # CCI - 商品通道指标
        df['cci'] = talib.CCI(high, low, close, timeperiod=14)
        
        # MOM - 动量指标
        df['mom'] = talib.MOM(close, timeperiod=10)
        
        # ROC - 变动率指标
        df['roc'] = talib.ROC(close, timeperiod=10)
        
        # 3. 波动率指标
        # ATR - 真实波动幅度
        df['atr'] = talib.ATR(high, low, close, timeperiod=14)
        df['atr_pct'] = df['atr'] / close * 100
        
        # 布林带
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            close, timeperiod=20, nbdevup=2, nbdevdn=2
        )
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 4. 成交量指标
        # OBV - 能量潮
        df['obv'] = talib.OBV(close, volume)
        
        # AD - 累积/派发线
        df['ad'] = talib.AD(high, low, close, volume)
        
        # ADOSC - 累积/派发震荡指标
        df['adosc'] = talib.ADOSC(high, low, close, volume, fastperiod=3, slowperiod=10)
        
        # 5. 价格形态
        # CDL - K线形态
        df['cdl_doji'] = talib.CDLDOJI(df['open'], high, low, close)
        df['cdl_hammer'] = talib.CDLHAMMER(df['open'], high, low, close)
        df['cdl_engulfing'] = talib.CDLENGULFING(df['open'], high, low, close)
        
        return df
    
    # ==================== 价量特征 ====================
    
    def calculate_price_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        价量特征
        
        参考往期策略：价量共振指标
        """
        df = df.copy()
        
        close = df['close'].values
        volume = df['volume'].values
        
        # 1. 价格变化
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # 多周期收益率
        for period in [5, 10, 20, 60]:
            df[f'returns_{period}'] = df['close'].pct_change(period)
        
        # 2. 成交量变化
        df['volume_change'] = df['volume'].pct_change()
        df['volume_ma_5'] = df['volume'].rolling(5).mean()
        df['volume_ma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']
        
        # 3. 价量背离
        # 价格上涨但成交量下降 → 背离
        df['price_up'] = (df['returns'] > 0).astype(int)
        df['volume_up'] = (df['volume_change'] > 0).astype(int)
        df['pv_divergence'] = df['price_up'] - df['volume_up']
        
        # 4. 价量共振
        # 价格和成交量同时上涨 → 共振
        df['pv_resonance'] = ((df['returns'] > 0) & (df['volume_change'] > 0)).astype(int)
        
        # 5. 振幅
        df['amplitude'] = (df['high'] - df['low']) / df['close']
        df['amplitude_ma'] = df['amplitude'].rolling(20).mean()
        
        # 6. 价格位置
        df['price_position'] = (df['close'] - df['low'].rolling(20).min()) / \
                               (df['high'].rolling(20).max() - df['low'].rolling(20).min())
        
        return df
    
    # ==================== 订单簿特征 ====================
    
    def calculate_orderbook_features(self, orderbook_data: Dict) -> Dict:
        """
        订单簿特征
        
        Args:
            orderbook_data: {
                'bids': [[price, amount], ...],
                'asks': [[price, amount], ...],
                'imbalance': float,
                'spread': float
            }
        
        Returns:
            Dict of orderbook features
        """
        features = {}
        
        bids = orderbook_data.get('bids', [])
        asks = orderbook_data.get('asks', [])
        
        if not bids or not asks:
            return features
        
        # 1. 基础特征
        features['ob_imbalance'] = orderbook_data.get('imbalance', 0)
        features['ob_spread'] = orderbook_data.get('spread', 0)
        features['ob_spread_bps'] = features['ob_spread'] * 10000  # 基点
        
        # 2. 深度特征
        # 前5档深度
        bid_depth_5 = sum([bid[1] for bid in bids[:5]])
        ask_depth_5 = sum([ask[1] for ask in asks[:5]])
        features['ob_depth_5_ratio'] = bid_depth_5 / ask_depth_5 if ask_depth_5 > 0 else 0
        
        # 前10档深度
        bid_depth_10 = sum([bid[1] for bid in bids[:10]])
        ask_depth_10 = sum([ask[1] for ask in asks[:10]])
        features['ob_depth_10_ratio'] = bid_depth_10 / ask_depth_10 if ask_depth_10 > 0 else 0
        
        # 3. 价格分布
        # 买单价格标准差
        bid_prices = [bid[0] for bid in bids[:10]]
        ask_prices = [ask[0] for ask in asks[:10]]
        features['ob_bid_price_std'] = np.std(bid_prices) if bid_prices else 0
        features['ob_ask_price_std'] = np.std(ask_prices) if ask_prices else 0
        
        # 4. 量分布
        bid_amounts = [bid[1] for bid in bids[:10]]
        ask_amounts = [ask[1] for ask in asks[:10]]
        features['ob_bid_amount_std'] = np.std(bid_amounts) if bid_amounts else 0
        features['ob_ask_amount_std'] = np.std(ask_amounts) if ask_amounts else 0
        
        # 5. 大单特征
        bid_amounts_sorted = sorted(bid_amounts, reverse=True)
        ask_amounts_sorted = sorted(ask_amounts, reverse=True)
        
        # 最大单占比
        features['ob_max_bid_ratio'] = bid_amounts_sorted[0] / sum(bid_amounts) if bid_amounts else 0
        features['ob_max_ask_ratio'] = ask_amounts_sorted[0] / sum(ask_amounts) if ask_amounts else 0
        
        # 前3大单占比
        features['ob_top3_bid_ratio'] = sum(bid_amounts_sorted[:3]) / sum(bid_amounts) if bid_amounts else 0
        features['ob_top3_ask_ratio'] = sum(ask_amounts_sorted[:3]) / sum(ask_amounts) if ask_amounts else 0
        
        return features
    
    # ==================== 情绪特征 ====================
    
    def calculate_sentiment_features(
        self,
        news_sentiment: float = 0,
        twitter_sentiment: float = 0,
        vix: float = 0
    ) -> Dict:
        """
        情绪特征
        
        Args:
            news_sentiment: 新闻情感 (-1 to 1)
            twitter_sentiment: Twitter情感 (-1 to 1)
            vix: 波动率指数
        
        Returns:
            Dict of sentiment features
        """
        features = {}
        
        # 1. 情感得分
        features['sentiment_news'] = news_sentiment
        features['sentiment_twitter'] = twitter_sentiment
        features['sentiment_combined'] = (news_sentiment + twitter_sentiment) / 2
        
        # 2. 恐慌指数
        features['vix'] = vix
        features['vix_level'] = 'low' if vix < 15 else ('medium' if vix < 25 else 'high')
        
        # 3. 情感强度
        features['sentiment_strength'] = abs(features['sentiment_combined'])
        
        # 4. 情感方向
        features['sentiment_direction'] = 1 if features['sentiment_combined'] > 0 else (-1 if features['sentiment_combined'] < 0 else 0)
        
        return features
    
    # ==================== 宏观特征 ====================
    
    def calculate_macro_features(
        self,
        dxy: float = 0,
        dxy_change: float = 0,
        us10y: float = 0,
        us10y_change: float = 0
    ) -> Dict:
        """
        宏观特征
        
        Args:
            dxy: 美元指数
            dxy_change: 美元指数变化
            us10y: 美债10年期收益率
            us10y_change: 收益率变化
        
        Returns:
            Dict of macro features
        """
        features = {}
        
        # 1. 美元指数
        features['dxy'] = dxy
        features['dxy_change'] = dxy_change
        features['dxy_strength'] = 'strong' if dxy > 105 else ('medium' if dxy > 100 else 'weak')
        
        # 2. 美债收益率
        features['us10y'] = us10y
        features['us10y_change'] = us10y_change
        features['us10y_level'] = 'high' if us10y > 4.5 else ('medium' if us10y > 3.5 else 'low')
        
        # 3. 黄金驱动因子
        # DXY涨 → 黄金跌
        # US10Y涨 → 黄金跌
        features['gold_headwind'] = (dxy_change > 0.003) or (us10y_change > 0.1)
        features['gold_tailwind'] = (dxy_change < -0.003) or (us10y_change < -0.1)
        
        return features
    
    # ==================== 时间特征 ====================
    
    def calculate_time_features(self, timestamp: datetime) -> Dict:
        """
        时间特征
        
        参考：日历效应策略
        """
        features = {}
        
        # 1. 基础时间
        features['hour'] = timestamp.hour
        features['day_of_week'] = timestamp.weekday()
        features['day_of_month'] = timestamp.day
        features['month'] = timestamp.month
        
        # 2. 交易时段
        # 亚洲时段: 0-8
        # 欧洲时段: 8-16
        # 美国时段: 16-24
        if 0 <= timestamp.hour < 8:
            features['session'] = 'asia'
        elif 8 <= timestamp.hour < 16:
            features['session'] = 'europe'
        else:
            features['session'] = 'us'
        
        # 3. 重要时间点
        # 美国非农数据: 每月第一个周五 20:30
        # 美联储会议: 通常周三 02:00
        features['is_nonfarm_day'] = (timestamp.weekday() == 4 and timestamp.day <= 7)
        features['is_fomc_time'] = (timestamp.hour == 2)
        
        # 4. 周期特征
        features['is_month_start'] = (timestamp.day <= 5)
        features['is_month_end'] = (timestamp.day >= 25)
        features['is_quarter_end'] = (timestamp.month in [3, 6, 9, 12] and timestamp.day >= 25)
        
        return features
    
    # ==================== 综合特征 ====================
    
    def create_features(
        self,
        price_df: pd.DataFrame,
        orderbook_data: Optional[Dict] = None,
        macro_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        创建完整特征集
        
        Args:
            price_df: 价格K线数据
            orderbook_data: 订单簿数据
            macro_data: 宏观数据
            sentiment_data: 情绪数据
            timestamp: 时间戳
        
        Returns:
            DataFrame with all features
        """
        # 1. 技术指标
        df = self.calculate_technical_indicators(price_df)
        
        # 2. 价量特征
        df = self.calculate_price_volume_features(df)
        
        # 3. 订单簿特征（添加到最后一行）
        if orderbook_data:
            ob_features = self.calculate_orderbook_features(orderbook_data)
            for key, value in ob_features.items():
                df.loc[df.index[-1], key] = value
        
        # 4. 宏观特征
        if macro_data:
            macro_features = self.calculate_macro_features(
                dxy=macro_data.get('dxy', 0),
                dxy_change=macro_data.get('dxy_change', 0),
                us10y=macro_data.get('us10y', 0),
                us10y_change=macro_data.get('us10y_change', 0)
            )
            for key, value in macro_features.items():
                df.loc[df.index[-1], key] = value
        
        # 5. 情绪特征
        if sentiment_data:
            sentiment_features = self.calculate_sentiment_features(
                news_sentiment=sentiment_data.get('news_sentiment', 0),
                twitter_sentiment=sentiment_data.get('twitter_sentiment', 0),
                vix=sentiment_data.get('vix', 0)
            )
            for key, value in sentiment_features.items():
                df.loc[df.index[-1], key] = value
        
        # 6. 时间特征
        if timestamp:
            time_features = self.calculate_time_features(timestamp)
            for key, value in time_features.items():
                df.loc[df.index[-1], key] = value
        
        # 记录特征名称
        self.feature_names = [col for col in df.columns if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        return df
    
    # ==================== 特征选择 ====================
    
    def select_features(
        self,
        df: pd.DataFrame,
        target: str = 'returns',
        method: str = 'correlation',
        top_k: int = 50
    ) -> List[str]:
        """
        特征选择
        
        参考机器学习资料：特征工程之变量选择
        
        Args:
            df: 特征DataFrame
            target: 目标变量
            method: 选择方法 (correlation/mutual_info/importance)
            top_k: 选择前k个特征
        
        Returns:
            List of selected feature names
        """
        if method == 'correlation':
            # 相关性选择
            correlations = df.corr()[target].abs().sort_values(ascending=False)
            selected = correlations.head(top_k + 1).index.tolist()
            selected.remove(target)
            return selected[:top_k]
        
        elif method == 'mutual_info':
            # 互信息选择
            from sklearn.feature_selection import mutual_info_regression
            
            X = df[self.feature_names].fillna(0)
            y = df[target].fillna(0)
            
            mi_scores = mutual_info_regression(X, y)
            mi_df = pd.DataFrame({'feature': self.feature_names, 'score': mi_scores})
            mi_df = mi_df.sort_values('score', ascending=False)
            
            return mi_df.head(top_k)['feature'].tolist()
        
        return self.feature_names[:top_k]
    
    def get_feature_importance(self) -> Dict:
        """获取特征重要性"""
        return self.feature_importance


# ==================== 测试 ====================

def test_feature_engineer():
    """测试特征工程"""
    print("\n" + "=" * 70)
    print("🧪 测试特征工程")
    print("=" * 70)
    
    # 创建模拟数据
    np.random.seed(42)
    n = 100
    
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n, freq='1min'),
        'open': 2650 + np.random.randn(n) * 10,
        'high': 2660 + np.random.randn(n) * 10,
        'low': 2640 + np.random.randn(n) * 10,
        'close': 2650 + np.random.randn(n) * 10,
        'volume': 1000 + np.random.randn(n) * 100
    })
    
    engineer = FeatureEngineer()
    
    # 测试技术指标
    print("\n1️⃣ 测试技术指标...")
    df_tech = engineer.calculate_technical_indicators(df)
    print(f"   ✅ 生成 {len(df_tech.columns) - len(df.columns)} 个技术指标")
    print(f"   📊 RSI: {df_tech['rsi_12'].iloc[-1]:.2f}")
    print(f"   📊 MACD: {df_tech['macd'].iloc[-1]:.2f}")
    
    # 测试价量特征
    print("\n2️⃣ 测试价量特征...")
    df_pv = engineer.calculate_price_volume_features(df_tech)
    print(f"   ✅ 生成 {len(df_pv.columns) - len(df_tech.columns)} 个价量特征")
    print(f"   📊 收益率: {df_pv['returns'].iloc[-1]:.4f}")
    print(f"   📊 成交量比率: {df_pv['volume_ratio'].iloc[-1]:.2f}")
    
    # 测试订单簿特征
    print("\n3️⃣ 测试订单簿特征...")
    orderbook_data = {
        'bids': [[2650 - i, 100 + i*10] for i in range(20)],
        'asks': [[2650 + i, 100 + i*10] for i in range(20)],
        'imbalance': 0.15,
        'spread': 0.0001
    }
    ob_features = engineer.calculate_orderbook_features(orderbook_data)
    print(f"   ✅ 生成 {len(ob_features)} 个订单簿特征")
    print(f"   📊 买卖失衡: {ob_features['ob_imbalance']:.2%}")
    print(f"   📊 深度比率: {ob_features['ob_depth_5_ratio']:.2f}")
    
    # 测试宏观特征
    print("\n4️⃣ 测试宏观特征...")
    macro_features = engineer.calculate_macro_features(
        dxy=104.5,
        dxy_change=0.005,
        us10y=4.2,
        us10y_change=0.05
    )
    print(f"   ✅ 生成 {len(macro_features)} 个宏观特征")
    print(f"   📊 DXY强度: {macro_features['dxy_strength']}")
    print(f"   📊 黄金逆风: {macro_features['gold_headwind']}")
    
    # 测试综合特征
    print("\n5️⃣ 测试综合特征生成...")
    df_full = engineer.create_features(
        price_df=df,
        orderbook_data=orderbook_data,
        macro_data={'dxy': 104.5, 'dxy_change': 0.005},
        timestamp=datetime.now()
    )
    print(f"   ✅ 总特征数: {len(engineer.feature_names)}")
    print(f"   📊 数据形状: {df_full.shape}")
    
    # 测试特征选择
    print("\n6️⃣ 测试特征选择...")
    df_full['returns'] = df_full['close'].pct_change()
    selected = engineer.select_features(df_full, target='returns', top_k=20)
    print(f"   ✅ 选择 {len(selected)} 个重要特征")
    print(f"   📊 前5个: {selected[:5]}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_feature_engineer()



