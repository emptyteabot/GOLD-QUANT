"""
Tushare高级数据接口
一万积分版本，可获取完整宏观数据
"""
import tushare as ts
import pandas as pd
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

# Tushare配置
TUSHARE_TOKEN = "2406c659bbbdd44678d8e864239efa6f7b3258fbdae026cc13dcb7d7f956"


class TushareDataProvider:
    """Tushare数据提供者（一万积分版）"""
    
    def __init__(self, token: str = TUSHARE_TOKEN):
        self.token = token
        self.pro = None
        self._initialize()
    
    def _initialize(self):
        """初始化Tushare连接"""
        try:
            self.pro = ts.pro_api(self.token)
            self.pro._DataApi__token = self.token
            self.pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'
            
            logger.info("✅ Tushare已初始化（一万积分版）")
            
        except Exception as e:
            logger.error(f"❌ Tushare初始化失败: {e}")
    
    def get_macro_data(self) -> Dict:
        """获取完整宏观数据"""
        macro_data = {}
        
        try:
            # 1. CPI数据
            cpi = self._get_cpi()
            if cpi:
                macro_data['cpi'] = cpi
                logger.info(f"📊 CPI: {cpi:.2f}%")
            
            # 2. PPI数据
            ppi = self._get_ppi()
            if ppi:
                macro_data['ppi'] = ppi
                logger.info(f"📊 PPI: {ppi:.2f}%")
            
            # 3. GDP数据
            gdp = self._get_gdp()
            if gdp:
                macro_data['gdp'] = gdp
                logger.info(f"📊 GDP: {gdp:.2f}%")
            
            # 4. M2货币供应
            m2 = self._get_m2()
            if m2:
                macro_data['m2'] = m2
                logger.info(f"📊 M2: {m2:.2f}%")
            
            # 5. Shibor利率
            shibor = self._get_shibor()
            if shibor:
                macro_data['shibor'] = shibor
                logger.info(f"📊 Shibor: {shibor:.2f}%")
            
            # 6. 美元兑人民币
            usd_cny = self._get_usd_cny()
            if usd_cny:
                macro_data['usd_cny'] = usd_cny
                logger.info(f"📊 USD/CNY: {usd_cny:.4f}")
            
            # 7. 黄金储备（使用默认值）
            macro_data['gold_reserve'] = 6264.0
            logger.info(f"📊 黄金储备: 6264.00万盎司（默认值）")
            
            # 8. 外汇储备（使用默认值）
            macro_data['fx_reserve'] = 32000.0
            logger.info(f"📊 外汇储备: 32000.00亿美元（默认值）")
            
            return macro_data
            
        except Exception as e:
            logger.error(f"❌ 获取宏观数据失败: {e}")
            return {}
    
    def _get_cpi(self) -> Optional[float]:
        """获取CPI同比"""
        try:
            end_date = datetime.now().strftime('%Y%m')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m')
            
            df = self.pro.cn_cpi(start_m=start_date, end_m=end_date)
            
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                return float(latest['nt_yoy'])
            
        except Exception as e:
            logger.warning(f"⚠️ 获取CPI失败: {e}")
        
        return None
    
    def _get_ppi(self) -> Optional[float]:
        """获取PPI同比"""
        try:
            end_date = datetime.now().strftime('%Y%m')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m')
            
            df = self.pro.cn_ppi(start_m=start_date, end_m=end_date)
            
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                return float(latest['ppi_yoy'])
            
        except Exception as e:
            logger.warning(f"⚠️ 获取PPI失败: {e}")
        
        return None
    
    def _get_gdp(self) -> Optional[float]:
        """获取GDP同比"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            df = self.pro.cn_gdp(start_q=start_date, end_q=end_date)
            
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                return float(latest['gdp_yoy'])
            
        except Exception as e:
            logger.warning(f"⚠️ 获取GDP失败: {e}")
        
        return None
    
    def _get_m2(self) -> Optional[float]:
        """获取M2同比"""
        try:
            end_date = datetime.now().strftime('%Y%m')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m')
            
            df = self.pro.cn_m(start_m=start_date, end_m=end_date)
            
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                return float(latest['m2_yoy'])
            
        except Exception as e:
            logger.warning(f"⚠️ 获取M2失败: {e}")
        
        return None
    
    def _get_shibor(self) -> Optional[float]:
        """获取Shibor隔夜利率"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            
            df = self.pro.shibor(start_date=start_date, end_date=end_date)
            
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                return float(latest['on'])
            
        except Exception as e:
            logger.warning(f"⚠️ 获取Shibor失败: {e}")
        
        return None
    
    def _get_usd_cny(self) -> Optional[float]:
        """获取美元兑人民币汇率"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            
            df = self.pro.fx_daily(ts_code='USDCNY.FX', start_date=start_date, end_date=end_date)
            
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                return float(latest['close'])
            
        except Exception as e:
            logger.warning(f"⚠️ 获取USD/CNY失败: {e}")
        
        return None
    
    def get_gold_futures_data(self, days: int = 30) -> Optional[pd.DataFrame]:
        """获取上海黄金期货数据"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            df = self.pro.fut_daily(ts_code='AU.SHF', start_date=start_date, end_date=end_date)
            
            if df is not None and len(df) > 0:
                df = df.sort_values('trade_date')
                df = df.rename(columns={
                    'trade_date': 'date',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'vol': 'volume'
                })
                
                logger.info(f"📊 获取到 {len(df)} 天的黄金期货数据")
                return df[['date', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"❌ 获取黄金期货数据失败: {e}")
        
        return None


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("="*80)
    print("🔍 测试Tushare数据获取（一万积分版）")
    print("="*80)
    
    provider = TushareDataProvider()
    
    print("\n📊 获取宏观数据...")
    macro_data = provider.get_macro_data()
    
    print("\n" + "="*80)
    print("📊 宏观数据总结:")
    for key, value in macro_data.items():
        print(f"   {key}: {value}")
    print("="*80)
    
    print("\n📊 获取黄金期货数据...")
    gold_df = provider.get_gold_futures_data(days=30)
    if gold_df is not None:
        print(f"\n前5行数据:")
        print(gold_df.head())
