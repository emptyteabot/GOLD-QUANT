"""
增强版宏观分析模块
整合 Tushare（中国数据）+ Alpha Vantage（美国数据）
"""
import logging
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)

try:
    from tushare_provider import TushareDataProvider
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False
    logger.warning("⚠️ Tushare未安装")

try:
    from alphavantage_data import AlphaVantageMacroData
    ALPHAVANTAGE_AVAILABLE = True
except ImportError:
    ALPHAVANTAGE_AVAILABLE = False
    logger.warning("⚠️ Alpha Vantage未安装")


class EnhancedMacroAnalyst:
    """增强版宏观分析师（整合多数据源）"""
    
    def __init__(self):
        self.tushare = None
        self.alphavantage = None
        self.cache = {}
        self.cache_duration = 3600  # 1小时缓存
        
        # 初始化数据源
        if TUSHARE_AVAILABLE:
            try:
                self.tushare = TushareDataProvider()
                logger.info("✅ Tushare数据源已加载（一万积分版）")
            except Exception as e:
                logger.warning(f"⚠️ Tushare初始化失败: {e}")
        
        if ALPHAVANTAGE_AVAILABLE:
            try:
                self.alphavantage = AlphaVantageMacroData()
                logger.info("✅ Alpha Vantage数据源已加载")
            except Exception as e:
                logger.warning(f"⚠️ Alpha Vantage初始化失败: {e}")
        
        if not self.tushare and not self.alphavantage:
            logger.error("❌ 没有可用的宏观数据源！")
    
    def _get_cached_or_fetch(self, key: str, fetch_func):
        """缓存机制"""
        if key in self.cache:
            cached_data, cached_time = self.cache[key]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        
        data = fetch_func()
        if data is not None:
            self.cache[key] = (data, time.time())
        
        return data
    
    def get_comprehensive_macro_data(self) -> Dict:
        """
        获取综合宏观数据
        
        Returns:
            {
                # 美国数据（Alpha Vantage）
                'us_treasury_10y': 美债10年期收益率,
                'us_cpi': 美国CPI,
                'us_real_rate': 美国实际利率,
                
                # 中国数据（Tushare）
                'cn_cpi': 中国CPI,
                'cn_ppi': 中国PPI,
                'cn_gdp': 中国GDP,
                'cn_m2': 中国M2,
                'cn_shibor': Shibor利率,
                'usd_cny': 美元兑人民币,
                'cn_gold_reserve': 中国黄金储备,
                'cn_fx_reserve': 中国外汇储备,
                
                # 衍生指标
                'global_liquidity': 全球流动性指数,
                'gold_demand_score': 黄金需求评分
            }
        """
        macro_data = {}
        
        # 1. 获取美国数据
        if self.alphavantage:
            logger.info("📊 获取美国宏观数据...")
            
            us_treasury = self._get_cached_or_fetch('us_treasury', 
                lambda: self.alphavantage.get_treasury_yield())
            if us_treasury:
                macro_data['us_treasury_10y'] = us_treasury
            
            us_cpi = self._get_cached_or_fetch('us_cpi',
                lambda: self.alphavantage.get_cpi())
            if us_cpi:
                macro_data['us_cpi'] = us_cpi
            
            # 计算实际利率
            if us_treasury and us_cpi:
                macro_data['us_real_rate'] = us_treasury - us_cpi
        
        # 2. 获取中国数据
        if self.tushare:
            logger.info("📊 获取中国宏观数据...")
            
            cn_data = self._get_cached_or_fetch('cn_macro',
                lambda: self.tushare.get_macro_data())
            
            if cn_data:
                macro_data.update({
                    'cn_cpi': cn_data.get('cpi'),
                    'cn_ppi': cn_data.get('ppi'),
                    'cn_gdp': cn_data.get('gdp'),
                    'cn_m2': cn_data.get('m2'),
                    'cn_shibor': cn_data.get('shibor'),
                    'usd_cny': cn_data.get('usd_cny'),
                    'cn_gold_reserve': cn_data.get('gold_reserve'),
                    'cn_fx_reserve': cn_data.get('fx_reserve')
                })
        
        # 3. 计算衍生指标
        macro_data['global_liquidity'] = self._calculate_global_liquidity(macro_data)
        macro_data['gold_demand_score'] = self._calculate_gold_demand(macro_data)
        
        return macro_data
    
    def _calculate_global_liquidity(self, data: Dict) -> float:
        """
        计算全球流动性指数（0-100）
        
        考虑因素：
        - 美国实际利率（越低越宽松）
        - 中国M2增速（越高越宽松）
        - Shibor利率（越低越宽松）
        """
        score = 50  # 基准分
        
        # 美国实际利率
        us_real_rate = data.get('us_real_rate')
        if us_real_rate is not None:
            if us_real_rate < 0:
                score += 20
            elif us_real_rate < 1:
                score += 10
            elif us_real_rate > 2:
                score -= 15
        
        # 中国M2
        cn_m2 = data.get('cn_m2')
        if cn_m2 is not None:
            if cn_m2 > 10:
                score += 15
            elif cn_m2 > 8:
                score += 10
            elif cn_m2 < 6:
                score -= 10
        
        # Shibor
        cn_shibor = data.get('cn_shibor')
        if cn_shibor is not None:
            if cn_shibor < 1.5:
                score += 15
            elif cn_shibor < 2.0:
                score += 10
            elif cn_shibor > 3.0:
                score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_gold_demand(self, data: Dict) -> float:
        """
        计算黄金需求评分（0-100）
        
        考虑因素：
        - 中国黄金储备变化（增加=需求强）
        - 美元兑人民币（贬值=需求强）
        - 通胀水平（高通胀=需求强）
        """
        score = 50
        
        # 中国黄金储备（假设增加是利好）
        gold_reserve = data.get('cn_gold_reserve')
        if gold_reserve is not None:
            # 如果储备>6000万盎司，说明央行在增持
            if gold_reserve > 6500:
                score += 20
            elif gold_reserve > 6200:
                score += 10
        
        # 美元兑人民币
        usd_cny = data.get('usd_cny')
        if usd_cny is not None:
            # 美元贬值（汇率下降）利好黄金
            if usd_cny < 7.0:
                score += 15
            elif usd_cny < 7.2:
                score += 10
            elif usd_cny > 7.3:
                score -= 10
        
        # 通胀（中美平均）
        us_cpi = data.get('us_cpi')
        cn_cpi = data.get('cn_cpi')
        if us_cpi and cn_cpi:
            avg_cpi = (us_cpi + cn_cpi) / 2
            if avg_cpi > 3.5:
                score += 15
            elif avg_cpi > 2.5:
                score += 10
            elif avg_cpi < 1.5:
                score -= 10
        
        return max(0, min(100, score))
    
    def calculate_enhanced_macro_score(self) -> Dict:
        """
        计算增强版宏观评分（-100 to +100）
        
        整合中美数据，更全面的评估
        """
        logger.info("\n" + "="*80)
        logger.info("🔍 增强版宏观基本面分析")
        logger.info("="*80)
        
        # 获取综合数据
        data = self.get_comprehensive_macro_data()
        
        score = 0
        details = []
        
        # 1. 美国实际利率（权重40%）
        us_real_rate = data.get('us_real_rate')
        if us_real_rate is not None:
            if us_real_rate < 0:
                score += 40
                details.append(f"✅ 美国实际利率{us_real_rate:.2f}% < 0，极度利好 (+40)")
            elif us_real_rate < 1.0:
                score += 30
                details.append(f"✅ 美国实际利率{us_real_rate:.2f}% < 1%，强烈利好 (+30)")
            elif us_real_rate < 1.5:
                score += 15
                details.append(f"✅ 美国实际利率{us_real_rate:.2f}% < 1.5%，利好 (+15)")
            elif us_real_rate > 2.5:
                score -= 30
                details.append(f"❌ 美国实际利率{us_real_rate:.2f}%过高，利空 (-30)")
        
        # 2. 全球流动性（权重30%）
        liquidity = data.get('global_liquidity', 50)
        if liquidity > 70:
            score += 30
            details.append(f"✅ 全球流动性{liquidity:.0f}/100，极度宽松 (+30)")
        elif liquidity > 60:
            score += 20
            details.append(f"✅ 全球流动性{liquidity:.0f}/100，宽松 (+20)")
        elif liquidity < 40:
            score -= 20
            details.append(f"❌ 全球流动性{liquidity:.0f}/100，紧缩 (-20)")
        
        # 3. 黄金需求（权重30%）
        gold_demand = data.get('gold_demand_score', 50)
        if gold_demand > 70:
            score += 30
            details.append(f"✅ 黄金需求{gold_demand:.0f}/100，强劲 (+30)")
        elif gold_demand > 60:
            score += 20
            details.append(f"✅ 黄金需求{gold_demand:.0f}/100，良好 (+20)")
        elif gold_demand < 40:
            score -= 20
            details.append(f"❌ 黄金需求{gold_demand:.0f}/100，疲软 (-20)")
        
        # 打印详情
        for detail in details:
            logger.info(f"   {detail}")
        
        # 确定市场体制
        if score > 60:
            regime = "🔥 强势看多（激进模式）"
        elif score > 30:
            regime = "📈 温和看多（保守模式）"
        elif score > -30:
            regime = "⚖️ 中性观望"
        else:
            regime = "📉 看空（防守模式）"
        
        logger.info(f"\n📊 增强版宏观评分: {score:.0f}/100")
        logger.info(f"📊 市场体制: {regime}")
        logger.info(f"📊 全球流动性: {liquidity:.0f}/100")
        logger.info(f"📊 黄金需求: {gold_demand:.0f}/100")
        
        return {
            'score': score,
            'regime': regime,
            'liquidity': liquidity,
            'gold_demand': gold_demand,
            'raw_data': data
        }


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    analyst = EnhancedMacroAnalyst()
    result = analyst.calculate_enhanced_macro_score()
    
    print(f"\n" + "="*80)
    print(f"📊 最终评分: {result['score']:.0f}/100")
    print(f"📊 市场体制: {result['regime']}")
    print(f"📊 全球流动性: {result['liquidity']:.0f}/100")
    print(f"📊 黄金需求: {result['gold_demand']:.0f}/100")
    print("="*80)
