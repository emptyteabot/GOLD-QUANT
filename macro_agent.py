"""
宏观基本面哨兵 - Agent 1
监控美元指数、美债收益率、CPI等宏观指标
使用Alpha Vantage API（免费）
"""
import logging
import requests
from typing import Dict, Optional
import config

logger = logging.getLogger(__name__)

# Alpha Vantage API配置
ALPHA_VANTAGE_KEY = "5TWF0VXJVK5H30R0"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


class MacroSentinel:
    """宏观基本面哨兵"""
    
    def __init__(self):
        self.api_key = ALPHA_VANTAGE_KEY
        self.base_url = ALPHA_VANTAGE_BASE_URL
        
        # 缓存机制（避免API限流）
        self.cache = {}
        self.cache_duration = 3600  # 1小时缓存
        
        logger.info("✅ 宏观哨兵已初始化（Alpha Vantage + 缓存）")
    
    def _get_cached_or_fetch(self, key: str, fetch_func):
        """缓存机制：避免频繁调用API"""
        import time
        
        # 检查缓存
        if key in self.cache:
            cached_data, cached_time = self.cache[key]
            if time.time() - cached_time < self.cache_duration:
                logger.info(f"📦 使用缓存数据: {key}")
                return cached_data
        
        # 缓存过期或不存在，重新获取
        data = fetch_func()
        if data is not None:
            self.cache[key] = (data, time.time())
        
        return data
    
    def get_treasury_yield(self) -> Optional[float]:
        """获取美债10年期收益率（带缓存）"""
        def fetch():
            try:
                params = {
                    'function': 'TREASURY_YIELD',
                    'interval': 'daily',
                    'maturity': '10year',
                    'apikey': self.api_key
                }
                response = requests.get(self.base_url, params=params, timeout=10)
                data = response.json()
                
                if 'data' in data and len(data['data']) > 0:
                    yield_value = float(data['data'][0]['value'])
                    logger.info(f"📊 美债10年期收益率: {yield_value:.2f}%")
                    return yield_value
            except Exception as e:
                logger.error(f"❌ 获取美债收益率失败: {e}")
            return None
        
        return self._get_cached_or_fetch('treasury_yield', fetch)
    
    def get_cpi(self) -> Optional[float]:
        """获取CPI通胀率（年化同比）"""
        try:
            params = {
                'function': 'CPI',
                'interval': 'monthly',
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and len(data['data']) >= 12:
                # 计算年化同比增长率
                current_cpi = float(data['data'][0]['value'])
                year_ago_cpi = float(data['data'][12]['value'])
                cpi_yoy = ((current_cpi - year_ago_cpi) / year_ago_cpi) * 100
                logger.info(f"📊 CPI通胀率（年化）: {cpi_yoy:.2f}%")
                return cpi_yoy
        except Exception as e:
            logger.error(f"❌ 获取CPI失败: {e}")
        
        # 如果失败，返回默认值2.5%
        logger.warning("⚠️ 使用默认CPI: 2.5%")
        return 2.5
    
    def get_dxy(self) -> Optional[float]:
        """获取美元指数（使用USD/CNY汇率作为替代，带缓存）"""
        def fetch():
            try:
                params = {
                    'function': 'CURRENCY_EXCHANGE_RATE',
                    'from_currency': 'USD',
                    'to_currency': 'CNY',
                    'apikey': self.api_key
                }
                response = requests.get(self.base_url, params=params, timeout=10)
                data = response.json()
                
                if 'Realtime Currency Exchange Rate' in data:
                    rate = float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
                    # 将汇率转换为类似DXY的指数（归一化到100左右）
                    dxy_proxy = rate * 14.3  # 7.0 * 14.3 ≈ 100
                    logger.info(f"📊 美元指数（代理）: {dxy_proxy:.2f}")
                    return dxy_proxy
            except Exception as e:
                logger.error(f"❌ 获取美元指数失败: {e}")
            return None
        
        return self._get_cached_or_fetch('dxy', fetch)
    
    def get_real_rate(self) -> Optional[float]:
        """计算实际利率（名义利率 - 通胀率）"""
        us10y = self.get_treasury_yield()
        cpi = self.get_cpi()
        
        if us10y is not None and cpi is not None:
            real_rate = us10y - cpi
            logger.info(f"📊 实际利率: {real_rate:.2f}% (名义{us10y:.2f}% - 通胀{cpi:.2f}%)")
            return real_rate
        elif us10y is not None:
            # 如果没有CPI，假设通胀2%
            real_rate = us10y - 2.0
            logger.warning(f"⚠️ 使用估算实际利率: {real_rate:.2f}%")
            return real_rate
        
        return None
    
    def calculate_macro_score(self) -> Dict:
        """
        计算宏观评分 (-100 to +100)
        
        评分规则：
        1. 实际利率因子 (±40分)：实际利率 < 1.5% → +40
        2. 美元趋势因子 (±30分)：DXY < 105 → +30
        3. 通胀因子 (±30分)：CPI > 3% → +30
        
        Returns:
            dict: {'score': int, 'dxy': float, 'us10y': float, 'cpi': float, 'real_rate': float}
        """
        logger.info("\n" + "="*80)
        logger.info("🔍 宏观基本面分析")
        logger.info("="*80)
        
        score = 0
        
        # 获取数据
        dxy = self.get_dxy()
        us10y = self.get_treasury_yield()
        cpi = self.get_cpi()
        real_rate = self.get_real_rate()
        
        # 1. 实际利率因子 (最重要！)
        if real_rate is not None:
            if real_rate < 1.0:
                score += 40
                logger.info(f"   ✅ 实际利率{real_rate:.2f}% < 1.0%，强烈利好黄金 (+40分)")
            elif real_rate < 1.5:
                score += 25
                logger.info(f"   ✅ 实际利率{real_rate:.2f}% < 1.5%，利好黄金 (+25分)")
            elif real_rate < 2.0:
                score += 10
                logger.info(f"   ⚖️ 实际利率{real_rate:.2f}%中性 (+10分)")
            else:
                score -= 30
                logger.info(f"   ❌ 实际利率{real_rate:.2f}%过高，利空黄金 (-30分)")
        else:
            logger.warning("   ⚠️ 实际利率数据缺失")
        
        # 2. 美元趋势因子
        if dxy is not None:
            if dxy < 100:
                score += 30
                logger.info(f"   ✅ 美元指数{dxy:.2f} < 100，强烈利好黄金 (+30分)")
            elif dxy < 105:
                score += 15
                logger.info(f"   ✅ 美元指数{dxy:.2f} < 105，利好黄金 (+15分)")
            elif dxy < 110:
                score += 0
                logger.info(f"   ⚖️ 美元指数{dxy:.2f}中性 (0分)")
            else:
                score -= 20
                logger.info(f"   ❌ 美元指数{dxy:.2f}过强，利空黄金 (-20分)")
        else:
            logger.warning("   ⚠️ 美元指数数据缺失")
        
        # 3. 通胀因子
        if cpi is not None:
            if cpi > 4.0:
                score += 30
                logger.info(f"   ✅ CPI{cpi:.2f}% > 4%，高通胀利好黄金 (+30分)")
            elif cpi > 3.0:
                score += 20
                logger.info(f"   ✅ CPI{cpi:.2f}% > 3%，利好黄金 (+20分)")
            elif cpi < 2.0:
                score -= 10
                logger.info(f"   ❌ CPI{cpi:.2f}% < 2%，低通胀利空黄金 (-10分)")
            else:
                score += 0
                logger.info(f"   ⚖️ CPI{cpi:.2f}%中性 (0分)")
        else:
            logger.warning("   ⚠️ CPI数据缺失")
        
        # 确定市场体制
        if score > 50:
            regime_desc = "🔥 强势看多（激进模式）"
        elif score > 0:
            regime_desc = "📈 温和看多（保守模式）"
        else:
            regime_desc = "⚖️ 中性观望"
        
        logger.info(f"\n📊 宏观评分: {score:.0f}/100")
        logger.info(f"📊 市场体制: {regime_desc}")
        
        return {
            'score': score,
            'regime_desc': regime_desc,
            'dxy': dxy,
            'us10y': us10y,
            'cpi': cpi,
            'real_rate': real_rate,
            'vix': None  # Alpha Vantage不提供VIX
        }


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    sentinel = MacroSentinel()
    result = sentinel.calculate_macro_score()
    
    print(f"\n最终评分: {result['score']}")
    print(f"市场体制: {result['regime_desc']}")
