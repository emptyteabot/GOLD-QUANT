"""
配置管理模块
加载环境变量和系统配置
"""
import os
from dotenv import load_dotenv
from typing import List, Tuple

# 加载 .env 文件
load_dotenv()

class Config:
    """系统配置类"""
    
    # API 配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    FEISHU_WEBHOOK: str = os.getenv("FEISHU_WEBHOOK", "")
    
    # 预警阈值
    THRESHOLD_PRICE_DROP_1M: float = float(os.getenv("THRESHOLD_PRICE_DROP_1M", "-0.003"))
    THRESHOLD_PRICE_DROP_5M: float = float(os.getenv("THRESHOLD_PRICE_DROP_5M", "-0.008"))
    THRESHOLD_SENTIMENT: int = int(os.getenv("THRESHOLD_SENTIMENT", "-7"))
    
    # 监控频率
    PRICE_CHECK_INTERVAL: int = int(os.getenv("PRICE_CHECK_INTERVAL", "3"))
    NEWS_CHECK_INTERVAL: int = int(os.getenv("NEWS_CHECK_INTERVAL", "60"))
    
    # 高频时段
    HIGH_FREQUENCY_PERIODS: str = os.getenv("HIGH_FREQUENCY_PERIODS", "20:00-21:00,21:30-22:30")
    
    # 新闻源
    NEWS_FEEDS: List[str] = os.getenv(
        "NEWS_FEEDS", 
        "https://www.forexlive.com/feed/news,https://www.investing.com/rss/news_25.rss"
    ).split(",")
    
    # 交易对配置
    GOLD_SYMBOL: str = "PAXG/USDT"  # Binance 黄金代理
    DXY_SYMBOL: str = "DXY/USDT"    # 美元指数 (如果支持)
    
    @classmethod
    def validate(cls) -> bool:
        """验证必要配置是否存在"""
        if not cls.DEEPSEEK_API_KEY:
            print("❌ 错误: 未配置 DEEPSEEK_API_KEY")
            return False
        if not cls.FEISHU_WEBHOOK:
            print("❌ 错误: 未配置 FEISHU_WEBHOOK")
            return False
        return True
    
    @classmethod
    def parse_high_frequency_periods(cls) -> List[Tuple[int, int, int, int]]:
        """
        解析高频时段配置
        返回: [(start_hour, start_min, end_hour, end_min), ...]
        """
        periods = []
        for period in cls.HIGH_FREQUENCY_PERIODS.split(","):
            try:
                start, end = period.strip().split("-")
                start_h, start_m = map(int, start.split(":"))
                end_h, end_m = map(int, end.split(":"))
                periods.append((start_h, start_m, end_h, end_m))
            except:
                continue
        return periods
    
    @classmethod
    def is_high_frequency_time(cls) -> bool:
        """判断当前是否处于高频监控时段"""
        from datetime import datetime
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        for start_h, start_m, end_h, end_m in cls.parse_high_frequency_periods():
            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            if start_minutes <= current_minutes <= end_minutes:
                return True
        return False


# 全局配置实例
config = Config()




