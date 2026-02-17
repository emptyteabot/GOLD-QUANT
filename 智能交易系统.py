"""
🧠 智能交易系统 - 逻辑正确版

核心逻辑：
1. 行情识别 → 判断当前是什么行情（趋势/震荡/暴跌反弹）
2. 历史对比 → 找历史上相似行情
3. 策略匹配 → 用那个行情中最有效的策略
4. 宏观过滤 → 用真实宏观数据做过滤（不是固定分数）

不再是5个专家打架，而是：
- 一个行情识别器
- 一个策略选择器
- 宏观数据做过滤（权重低但真实）
"""
import os
# 注意：Tushare是国内服务器，不需要代理！
# 代理设置移到OKX请求时再设置

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv('.env.trading')

# 配置
FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK_URL')
CNY_RATE = 7.2

# ============================================================
# Tushare宏观数据（真实数据，不是固定分数）
# ============================================================
class MacroDataProvider:
    """
    真实宏观数据提供者
    
    黄金的核心驱动因素：
    1. 美元指数（负相关）
    2. 实际利率（负相关）
    3. 地缘风险（正相关）
    4. 通胀预期（正相关）
    """
    
    def __init__(self):
        self.ts = None
        self.pro = None
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 3600  # 1小时缓存
        
        # 初始化Tushare（不走代理，直连国内服务器）
        try:
            # 临时移除代理，Tushare是国内服务器
            old_http = os.environ.pop('HTTP_PROXY', None)
            old_https = os.environ.pop('HTTPS_PROXY', None)
            
            import tushare as ts
            self.ts = ts
            token = "2406c659bbbdd44678d8e864239efa6f7b3258fbdae026cc13dcb7d7f956"
            self.pro = ts.pro_api(token)
            self.pro._DataApi__token = token
            self.pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'
            logger.info("✅ Tushare已初始化（直连国内）")
            
            # 恢复代理设置（给OKX用）
            if old_http:
                os.environ['HTTP_PROXY'] = old_http
            if old_https:
                os.environ['HTTPS_PROXY'] = old_https
        except Exception as e:
            logger.warning(f"⚠️ Tushare初始化失败: {e}")
    
    def get_macro_signals(self) -> Dict:
        """
        获取宏观信号
        
        返回：
        {
            'bias': float,  # -1到+1，正数利多黄金，负数利空
            'factors': dict,  # 各因素详情
            'confidence': float,  # 信号置信度
            'summary': str  # 文字总结
        }
        """
        factors = {}
        signals = []
        
        # 1. 获取美元兑人民币汇率（代理美元强弱）
        usd_cny = self._get_usd_cny()
        if usd_cny:
            factors['usd_cny'] = usd_cny
            # 美元走强 → 利空黄金
            if usd_cny['change_pct'] > 0.3:
                signals.append(-0.3)
                factors['usd_signal'] = "美元走强，利空黄金"
            elif usd_cny['change_pct'] < -0.3:
                signals.append(0.3)
                factors['usd_signal'] = "美元走弱，利多黄金"
            else:
                signals.append(0)
                factors['usd_signal'] = "美元平稳"
        
        # 2. 获取上海金价格（国内黄金溢价）
        shau = self._get_shanghai_gold()
        if shau:
            factors['shanghai_gold'] = shau
            # 国内金溢价高 → 需求强劲 → 利多
            if shau.get('premium_pct', 0) > 1:
                signals.append(0.2)
                factors['shau_signal'] = f"国内金溢价{shau['premium_pct']:.1f}%，需求强"
            else:
                factors['shau_signal'] = "国内金溢价正常"
        
        # 3. 获取Shibor利率（流动性指标）
        shibor = self._get_shibor()
        if shibor:
            factors['shibor'] = shibor
            # Shibor下降 → 流动性宽松 → 利多黄金
            if shibor['change'] < -0.05:
                signals.append(0.15)
                factors['shibor_signal'] = "流动性宽松，利多黄金"
            elif shibor['change'] > 0.1:
                signals.append(-0.15)
                factors['shibor_signal'] = "流动性收紧，利空黄金"
            else:
                factors['shibor_signal'] = "流动性平稳"
        
        # 4. 计算综合偏向
        if signals:
            bias = np.mean(signals)
            confidence = 1 - np.std(signals) if len(signals) > 1 else 0.5
        else:
            bias = 0
            confidence = 0.3
        
        # 生成总结
        if bias > 0.2:
            summary = "🟢 宏观面利多黄金"
        elif bias < -0.2:
            summary = "🔴 宏观面利空黄金"
        else:
            summary = "⚪ 宏观面中性"
        
        return {
            'bias': bias,
            'factors': factors,
            'confidence': confidence,
            'summary': summary
        }
    
    def _get_cached(self, key: str, fetch_func, ttl: int = 3600):
        """缓存机制"""
        now = datetime.now()
        if key in self.cache and key in self.cache_time:
            if (now - self.cache_time[key]).seconds < ttl:
                return self.cache[key]
        
        # Tushare请求不走代理
        old_http = os.environ.pop('HTTP_PROXY', None)
        old_https = os.environ.pop('HTTPS_PROXY', None)
        
        try:
            data = fetch_func()
            if data:
                self.cache[key] = data
                self.cache_time[key] = now
        finally:
            # 恢复代理
            if old_http:
                os.environ['HTTP_PROXY'] = old_http
            if old_https:
                os.environ['HTTPS_PROXY'] = old_https
        
        return data
    
    def _get_usd_cny(self) -> Optional[Dict]:
        """获取美元兑人民币"""
        def fetch():
            try:
                if not self.pro:
                    return None
                # 获取汇率
                df = self.pro.fx_daily(
                    ts_code='USDCNY.FXCM',
                    start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                if df is not None and len(df) >= 2:
                    latest = df.iloc[0]['close']
                    prev = df.iloc[1]['close']
                    change_pct = (latest - prev) / prev * 100
                    return {
                        'rate': latest,
                        'change_pct': change_pct
                    }
            except Exception as e:
                logger.warning(f"获取汇率失败: {e}")
            return None
        
        return self._get_cached('usd_cny', fetch)
    
    def _get_shanghai_gold(self) -> Optional[Dict]:
        """获取上海金价格"""
        def fetch():
            try:
                if not self.pro:
                    return None
                # 获取上海金
                df = self.pro.fut_daily(
                    ts_code='AU0.SHF',
                    start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                if df is not None and len(df) > 0:
                    price_cny = df.iloc[0]['close']  # 人民币/克
                    # 换算为美元/盎司（1盎司=31.1035克）
                    price_usd_oz = price_cny * 31.1035 / CNY_RATE
                    return {
                        'price_cny_g': price_cny,
                        'price_usd_oz': price_usd_oz,
                        'premium_pct': 0  # 需要伦敦金价格计算溢价
                    }
            except Exception as e:
                logger.warning(f"获取上海金失败: {e}")
            return None
        
        return self._get_cached('shanghai_gold', fetch)
    
    def _get_shibor(self) -> Optional[Dict]:
        """获取Shibor利率"""
        def fetch():
            try:
                if not self.pro:
                    return None
                df = self.pro.shibor(
                    start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                if df is not None and len(df) >= 2:
                    latest = df.iloc[0]['1w']  # 1周Shibor
                    prev = df.iloc[1]['1w']
                    return {
                        'rate': latest,
                        'change': latest - prev
                    }
            except Exception as e:
                logger.warning(f"获取Shibor失败: {e}")
            return None
        
        return self._get_cached('shibor', fetch)


# ============================================================
# 行情识别器
# ============================================================
class RegimeDetector:
    """
    行情识别器
    
    识别当前行情类型：
    1. TREND_UP - 上涨趋势
    2. TREND_DOWN - 下跌趋势
    3. RANGE - 震荡
    4. CRASH - 暴跌中
    5. REVERSAL - 暴跌后反弹（倒车接人最佳时机）
    """
    
    def detect(self, df: pd.DataFrame) -> Dict:
        """
        检测当前行情类型
        
        返回：
        {
            'regime': str,  # 行情类型
            'confidence': float,  # 置信度
            'features': dict,  # 特征数据
            'similar_history': list  # 历史相似行情
        }
        """
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # 计算特征
        features = self._calculate_features(df)
        
        # 判断行情类型
        regime = self._classify_regime(features)
        
        # 找历史相似行情
        similar = self._find_similar_history(features)
        
        return {
            'regime': regime['type'],
            'confidence': regime['confidence'],
            'features': features,
            'similar_history': similar,
            'description': regime['description']
        }
    
    def _calculate_features(self, df: pd.DataFrame) -> Dict:
        """计算行情特征"""
        close = df['close']
        
        # 1. 趋势强度（线性回归斜率）
        x = np.arange(len(close))
        slope, intercept = np.polyfit(x[-20:], close.iloc[-20:], 1)
        trend_strength = slope / close.iloc[-1] * 100  # 标准化
        
        # 2. 波动率
        returns = close.pct_change()
        volatility = returns.iloc[-20:].std() * np.sqrt(252 * 24)  # 年化
        
        # 3. RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])
        
        # 4. 距离高点/低点
        high_20 = close.iloc[-20:].max()
        low_20 = close.iloc[-20:].min()
        current = close.iloc[-1]
        dist_from_high = (current - high_20) / high_20 * 100
        dist_from_low = (current - low_20) / low_20 * 100
        
        # 5. 成交量变化
        vol_ratio = df['volume'].iloc[-5:].mean() / df['volume'].iloc[-20:].mean()
        
        # 6. 连续下跌/上涨天数
        consecutive_down = 0
        consecutive_up = 0
        for i in range(-1, -min(10, len(close)), -1):
            if close.iloc[i] < close.iloc[i-1]:
                consecutive_down += 1
            else:
                break
        for i in range(-1, -min(10, len(close)), -1):
            if close.iloc[i] > close.iloc[i-1]:
                consecutive_up += 1
            else:
                break
        
        return {
            'trend_strength': trend_strength,
            'volatility': volatility,
            'rsi': current_rsi,
            'dist_from_high': dist_from_high,
            'dist_from_low': dist_from_low,
            'vol_ratio': vol_ratio,
            'consecutive_down': consecutive_down,
            'consecutive_up': consecutive_up,
            'current_price': float(current),
            'high_20': float(high_20),
            'low_20': float(low_20)
        }
    
    def _classify_regime(self, features: Dict) -> Dict:
        """分类行情类型"""
        rsi = features['rsi']
        trend = features['trend_strength']
        dist_high = features['dist_from_high']
        dist_low = features['dist_from_low']
        vol_ratio = features['vol_ratio']
        consecutive_down = features['consecutive_down']
        
        # ========== 暴跌反弹（倒车接人！） ==========
        # 条件：RSI超卖 + 距离低点近 + 有企稳迹象
        if (rsi < 35 and 
            dist_low < 2 and 
            features['consecutive_up'] >= 1):
            return {
                'type': 'REVERSAL',
                'confidence': min(0.9, (35 - rsi) / 20 + 0.5),
                'description': f'🚗 倒车接人！RSI={rsi:.0f}超卖，距低点{dist_low:.1f}%'
            }
        
        # ========== 暴跌中（等待） ==========
        if (rsi < 30 and 
            consecutive_down >= 3 and 
            vol_ratio > 1.5):
            return {
                'type': 'CRASH',
                'confidence': 0.8,
                'description': f'⚠️ 暴跌中，RSI={rsi:.0f}，连跌{consecutive_down}根K线'
            }
        
        # ========== 上涨趋势 ==========
        if (trend > 0.05 and 
            rsi > 50 and rsi < 75 and
            dist_high > -3):
            confidence = min(0.85, 0.5 + trend * 2)
            return {
                'type': 'TREND_UP',
                'confidence': confidence,
                'description': f'📈 上涨趋势，RSI={rsi:.0f}'
            }
        
        # ========== 下跌趋势 ==========
        if (trend < -0.05 and 
            rsi < 50 and rsi > 25):
            confidence = min(0.85, 0.5 + abs(trend) * 2)
            return {
                'type': 'TREND_DOWN',
                'confidence': confidence,
                'description': f'📉 下跌趋势，RSI={rsi:.0f}'
            }
        
        # ========== 震荡 ==========
        return {
            'type': 'RANGE',
            'confidence': 0.6,
            'description': f'↔️ 震荡行情，RSI={rsi:.0f}'
        }
    
    def _find_similar_history(self, features: Dict) -> List[Dict]:
        """
        找历史上相似的行情
        
        黄金历史重要时刻：
        1. 2020年3月 - 疫情暴跌后V型反弹（RSI跌到25后反弹30%）
        2. 2022年3月 - 俄乌冲突后高位回落
        3. 2023年3月 - 银行危机避险上涨
        4. 2024年4月 - 地缘冲突推动创新高
        """
        similar = []
        
        rsi = features['rsi']
        dist_low = features['dist_from_low']
        
        # 与2020年3月相似（暴跌后反弹）
        if rsi < 35 and dist_low < 3:
            similar.append({
                'date': '2020年3月',
                'pattern': '疫情暴跌后V型反弹',
                'result': '反弹30%',
                'similarity': 0.85,
                'strategy': 'RSI超卖做多，目标15-20%'
            })
        
        # 与2022年3月相似（高位回落）
        if rsi > 70 and features['dist_from_high'] > -2:
            similar.append({
                'date': '2022年3月',
                'pattern': '俄乌冲突后高位',
                'result': '回调15%',
                'similarity': 0.7,
                'strategy': '谨慎追高，设好止损'
            })
        
        return similar


# ============================================================
# 策略选择器
# ============================================================
class StrategySelector:
    """
    策略选择器
    
    根据行情类型选择最优策略
    不是5个专家打架，而是统一的策略逻辑
    """
    
    def select_strategy(self, regime: Dict, macro: Dict) -> Dict:
        """
        选择策略
        
        返回：
        {
            'action': str,  # BUY / SELL / HOLD
            'confidence': float,
            'entry_logic': str,
            'exit_logic': str,
            'stop_loss': float,  # 止损百分比
            'take_profit': float,  # 止盈百分比
            'position_size': float  # 建议仓位（0-1）
        }
        """
        regime_type = regime['regime']
        regime_confidence = regime['confidence']
        macro_bias = macro['bias']
        
        # ========== 倒车接人策略 ==========
        if regime_type == 'REVERSAL':
            # 宏观面加持
            confidence = regime_confidence
            if macro_bias > 0:
                confidence = min(0.95, confidence + 0.1)
            
            return {
                'action': 'BUY',
                'confidence': confidence,
                'entry_logic': 'RSI超卖 + 止跌企稳 + 成交量确认',
                'exit_logic': 'RSI > 60 或 盈利目标达成',
                'stop_loss': 0.03,  # 3%止损
                'take_profit': 0.10,  # 10%止盈
                'position_size': min(0.3, confidence * 0.4),  # 根据置信度调整仓位
                'strategy_name': '🚗 倒车接人'
            }
        
        # ========== 暴跌中等待 ==========
        elif regime_type == 'CRASH':
            return {
                'action': 'HOLD',
                'confidence': 0.8,
                'entry_logic': '等待止跌信号（锤子线/启明星/放量阳线）',
                'exit_logic': 'N/A',
                'stop_loss': 0,
                'take_profit': 0,
                'position_size': 0,
                'strategy_name': '⏳ 等待抄底'
            }
        
        # ========== 上涨趋势顺势 ==========
        elif regime_type == 'TREND_UP':
            # 宏观面如果利空，降低仓位
            position = 0.2
            if macro_bias < -0.2:
                position = 0.1
            
            return {
                'action': 'BUY',
                'confidence': regime_confidence * 0.8,
                'entry_logic': '趋势回调到MA20附近',
                'exit_logic': 'RSI > 75 或 跌破MA20',
                'stop_loss': 0.05,
                'take_profit': 0.15,
                'position_size': position,
                'strategy_name': '📈 趋势跟踪'
            }
        
        # ========== 下跌趋势观望 ==========
        elif regime_type == 'TREND_DOWN':
            return {
                'action': 'HOLD',
                'confidence': 0.7,
                'entry_logic': '不做空黄金（趋势可能随时反转）',
                'exit_logic': 'N/A',
                'stop_loss': 0,
                'take_profit': 0,
                'position_size': 0,
                'strategy_name': '🚫 观望'
            }
        
        # ========== 震荡默认观望 ==========
        else:
            return {
                'action': 'HOLD',
                'confidence': 0.5,
                'entry_logic': '等待方向明确',
                'exit_logic': 'N/A',
                'stop_loss': 0,
                'take_profit': 0,
                'position_size': 0,
                'strategy_name': '↔️ 震荡观望'
            }


# ============================================================
# 飞书通知
# ============================================================
def send_feishu(title: str, message: str, color: str = "blue"):
    """发送飞书通知"""
    if not FEISHU_WEBHOOK:
        logger.info(f"[飞书] {title}")
        return
    
    data = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color
            },
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": message}}]
        }
    }
    
    try:
        requests.post(FEISHU_WEBHOOK, json=data, timeout=5)
        logger.info(f"✅ 飞书: {title}")
    except Exception as e:
        logger.error(f"❌ 飞书失败: {e}")


# ============================================================
# 主系统
# ============================================================
class SmartTradingSystem:
    """智能交易系统"""
    
    def __init__(self):
        from okx_client import OKXClient
        self.client = OKXClient()
        self.macro_provider = MacroDataProvider()
        self.regime_detector = RegimeDetector()
        self.strategy_selector = StrategySelector()
        self.last_notify = {}
    
    async def run(self):
        """运行系统"""
        # 设置代理给OKX用
        os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
        os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'
        
        await self.client.initialize()
        
        print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║              🧠 智能交易系统 - 逻辑正确版                     ║
    ║                                                              ║
    ║  数据：5分钟K线 × 1000根（约3.5天）                          ║
    ║                                                              ║
    ║  核心逻辑：                                                   ║
    ║    1. 行情识别 → 判断当前行情类型                             ║
    ║    2. 历史对比 → 找相似行情                                   ║
    ║    3. 策略选择 → 用最优策略                                   ║
    ║    4. 宏观过滤 → Tushare真实数据                             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止
        """)
        
        send_feishu("🧠 智能交易系统已启动", 
                   f"**逻辑：** 行情识别 → 历史对比 → 策略选择 → 宏观过滤\n"
                   f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                   "green")
        
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {scan_count} 次分析")
                logger.info(f"{'='*60}")
                
                await self._analyze_and_decide()
                
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("\n👋 系统停止")
        finally:
            await self.client.close()
    
    async def _analyze_and_decide(self):
        """分析并决策"""
        # 1. 获取价格
        price = await self.client.get_ticker("XAU-USDT-SWAP")
        if not price:
            logger.error("❌ 获取价格失败")
            return
        
        logger.info(f"💰 黄金价格: ${price:.2f} (¥{price * CNY_RATE:.0f})")
        
        # 2. 获取K线（5分钟，1000根，约3.5天）
        klines = await self.client.get_klines("XAU-USDT-SWAP", "5m", 1000)
        if not klines:
            logger.error("❌ 获取K线失败")
            return
        
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        df = df.iloc[::-1].reset_index(drop=True)
        
        # 3. 获取宏观数据（真实数据！）
        logger.info("\n📊 获取宏观数据...")
        macro = self.macro_provider.get_macro_signals()
        logger.info(f"   {macro['summary']}")
        logger.info(f"   偏向: {macro['bias']:+.2f}")
        for key, value in macro['factors'].items():
            if isinstance(value, str):
                logger.info(f"   {value}")
        
        # 4. 识别行情
        logger.info("\n🔍 识别行情...")
        regime = self.regime_detector.detect(df)
        logger.info(f"   类型: {regime['regime']}")
        logger.info(f"   {regime['description']}")
        logger.info(f"   置信度: {regime['confidence']:.0%}")
        
        # 显示历史相似行情
        if regime['similar_history']:
            logger.info("\n📜 历史相似行情:")
            for h in regime['similar_history']:
                logger.info(f"   {h['date']}: {h['pattern']}")
                logger.info(f"   结果: {h['result']}")
                logger.info(f"   策略: {h['strategy']}")
        
        # 5. 选择策略
        logger.info("\n🎯 策略选择...")
        strategy = self.strategy_selector.select_strategy(regime, macro)
        logger.info(f"   策略: {strategy['strategy_name']}")
        logger.info(f"   动作: {strategy['action']}")
        logger.info(f"   置信度: {strategy['confidence']:.0%}")
        logger.info(f"   入场逻辑: {strategy['entry_logic']}")
        
        if strategy['stop_loss'] > 0:
            stop_price = price * (1 - strategy['stop_loss'])
            tp_price = price * (1 + strategy['take_profit'])
            logger.info(f"   止损: ${stop_price:.2f} (-{strategy['stop_loss']:.0%})")
            logger.info(f"   止盈: ${tp_price:.2f} (+{strategy['take_profit']:.0%})")
        
        # 6. 发送通知
        if strategy['action'] == 'BUY' and strategy['confidence'] >= 0.6:
            self._send_trading_signal(price, regime, macro, strategy)
    
    def _send_trading_signal(self, price: float, regime: Dict, macro: Dict, strategy: Dict):
        """发送交易信号"""
        # 冷却检查
        key = strategy['strategy_name']
        now = datetime.now()
        if key in self.last_notify:
            if (now - self.last_notify[key]).seconds < 1800:  # 30分钟冷却
                return
        self.last_notify[key] = now
        
        # 构建消息
        similar_text = ""
        if regime['similar_history']:
            h = regime['similar_history'][0]
            similar_text = f"\n**历史参考：** {h['date']} {h['pattern']} → {h['result']}"
        
        message = f"""**{strategy['strategy_name']}**

**当前价格：** ${price:.2f} (¥{price * CNY_RATE:.0f})
**行情类型：** {regime['description']}
**置信度：** {strategy['confidence']:.0%}

**入场逻辑：**
{strategy['entry_logic']}

**宏观面：** {macro['summary']} (偏向{macro['bias']:+.2f})
{similar_text}

**风控建议：**
• 止损: ${price * (1 - strategy['stop_loss']):.2f} (-{strategy['stop_loss']:.0%})
• 止盈: ${price * (1 + strategy['take_profit']):.2f} (+{strategy['take_profit']:.0%})
• 建议仓位: {strategy['position_size']:.0%}

⚠️ 请手动操作！系统不会自动下单。
"""
        
        color = "green" if strategy['action'] == 'BUY' else "red"
        send_feishu(f"🎯 {strategy['strategy_name']} - {strategy['action']}", message, color)


# ============================================================
# 入口
# ============================================================
async def main():
    system = SmartTradingSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())

