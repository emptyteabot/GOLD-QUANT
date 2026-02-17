"""
使用Alpha Vantage获取宏观数据（免费）
官网：https://www.alphavantage.co/
免费额度：每天500次请求，每分钟5次
"""
import requests
import logging
from typing import Optional, Dict
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Alpha Vantage API Key（免费申请）
# 申请地址：https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_KEY = "5TWF0VXJVK5H30R0"  # 您的API Key


class AlphaVantageMacroData:
    """使用Alpha Vantage获取宏观数据"""
    
    def __init__(self, api_key: str = ALPHA_VANTAGE_KEY):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        # 创建session，禁用SSL验证
        self.session = requests.Session()
        self.session.verify = False
    
    def get_treasury_yield(self) -> Optional[float]:
        """获取美债10年期收益率"""
        try:
            params = {
                'function': 'TREASURY_YIELD',
                'interval': 'daily',
                'maturity': '10year',
                'apikey': self.api_key
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                yield_value = float(data['data'][0]['value'])
                logger.info(f"📊 美债10年期收益率: {yield_value:.2f}%")
                return yield_value
        except Exception as e:
            logger.error(f"❌ 获取美债收益率失败: {e}")
        return None
    
    def get_real_gdp(self) -> Optional[float]:
        """获取实际GDP（季度数据）"""
        try:
            params = {
                'function': 'REAL_GDP',
                'interval': 'quarterly',
                'apikey': self.api_key
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                gdp = float(data['data'][0]['value'])
                logger.info(f"📊 实际GDP: {gdp:.2f}B")
                return gdp
        except Exception as e:
            logger.error(f"❌ 获取GDP失败: {e}")
        return None
    
    def get_cpi(self) -> Optional[float]:
        """获取CPI通胀率"""
        try:
            params = {
                'function': 'CPI',
                'interval': 'monthly',
                'apikey': self.api_key
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                cpi = float(data['data'][0]['value'])
                logger.info(f"📊 CPI通胀率: {cpi:.2f}%")
                return cpi
        except Exception as e:
            logger.error(f"❌ 获取CPI失败: {e}")
        return None
    
    def get_forex_rate(self, from_currency: str = 'USD', to_currency: str = 'CNY') -> Optional[float]:
        """获取外汇汇率（可用于美元指数替代）"""
        try:
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_currency,
                'to_currency': to_currency,
                'apikey': self.api_key
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if 'Realtime Currency Exchange Rate' in data:
                rate = float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
                logger.info(f"📊 {from_currency}/{to_currency}: {rate:.4f}")
                return rate
        except Exception as e:
            logger.error(f"❌ 获取汇率失败: {e}")
        return None


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("="*80)
    print("🔍 测试Alpha Vantage宏观数据获取")
    print("="*80)
    print("\n⚠️ 注意：demo key有限制，请申请自己的免费API Key")
    print("申请地址：https://www.alphavantage.co/support/#api-key\n")
    
    av = AlphaVantageMacroData()
    
    print("📊 获取美债收益率...")
    treasury = av.get_treasury_yield()
    
    print("\n📊 获取CPI...")
    cpi = av.get_cpi()
    
    print("\n📊 获取USD/CNY汇率...")
    usd_cny = av.get_forex_rate('USD', 'CNY')
    
    print("\n" + "="*80)
    print("📊 结果总结:")
    print(f"   美债10年期: {treasury if treasury else 'N/A'}%")
    print(f"   CPI通胀率: {cpi if cpi else 'N/A'}%")
    print(f"   USD/CNY: {usd_cny if usd_cny else 'N/A'}")
    print("="*80)

