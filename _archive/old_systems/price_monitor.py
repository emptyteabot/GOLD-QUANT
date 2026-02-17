"""
价格监控模块
实时监控黄金价格波动,检测异常跌幅
"""
import asyncio
import ccxt.async_support as ccxt
from collections import deque
from datetime import datetime
from typing import Optional, Deque, Tuple
from config import config
from notifier import notifier


class PriceData:
    """价格数据点"""
    def __init__(self, price: float, timestamp: float):
        self.price = price
        self.timestamp = timestamp


class PriceMonitor:
    """价格监控器"""
    
    def __init__(self, symbol: str = "PAXG/USDT"):
        self.symbol = symbol
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # 价格历史队列 (最多保存5分钟数据)
        self.price_history: Deque[PriceData] = deque(maxlen=100)
        
        # 上次警报时间 (防止重复推送)
        self.last_alert_time: float = 0
        self.alert_cooldown: int = 300  # 5分钟冷却
        
        # 统计数据
        self.check_count: int = 0
        self.alert_count: int = 0
    
    async def fetch_current_price(self) -> Optional[float]:
        """获取当前价格"""
        try:
            ticker = await self.exchange.fetch_ticker(self.symbol)
            return ticker['last']
        except Exception as e:
            print(f"❌ 获取价格失败: {e}")
            return None
    
    def calculate_change(self, seconds: int) -> Optional[float]:
        """
        计算指定时间段内的涨跌幅
        
        Args:
            seconds: 时间段(秒)
        
        Returns:
            涨跌幅 (小数形式, 如 -0.005 表示 -0.5%)
        """
        if len(self.price_history) < 2:
            return None
        
        current_time = datetime.now().timestamp()
        current_price = self.price_history[-1].price
        
        # 找到最接近目标时间的历史价格
        target_time = current_time - seconds
        
        for data in self.price_history:
            if data.timestamp >= target_time:
                old_price = data.price
                change = (current_price - old_price) / old_price
                return change
        
        return None
    
    async def check_alert_conditions(self, current_price: float) -> bool:
        """
        检查是否触发警报条件
        
        Returns:
            是否触发警报
        """
        # 检查冷却时间
        current_time = datetime.now().timestamp()
        if current_time - self.last_alert_time < self.alert_cooldown:
            return False
        
        # 计算1分钟和5分钟跌幅
        change_1m = self.calculate_change(60)
        change_5m = self.calculate_change(300)
        
        # 判断是否触发警报
        alert_triggered = False
        
        if change_1m is not None and change_1m <= config.THRESHOLD_PRICE_DROP_1M:
            print(f"🚨 触发1分钟跌幅警报: {change_1m:.2%}")
            alert_triggered = True
        
        if change_5m is not None and change_5m <= config.THRESHOLD_PRICE_DROP_5M:
            print(f"🚨 触发5分钟跌幅警报: {change_5m:.2%}")
            alert_triggered = True
        
        # 发送警报
        if alert_triggered:
            success = await notifier.send_price_alert(
                price=current_price,
                change_1m=change_1m if change_1m else 0,
                change_5m=change_5m
            )
            
            if success:
                self.last_alert_time = current_time
                self.alert_count += 1
                return True
        
        return False
    
    async def run(self):
        """主监控循环"""
        print(f"📊 价格监控器启动: {self.symbol}")
        print(f"⏱️  检查间隔: {config.PRICE_CHECK_INTERVAL}秒")
        print(f"📉 1分钟跌幅阈值: {config.THRESHOLD_PRICE_DROP_1M:.2%}")
        print(f"📉 5分钟跌幅阈值: {config.THRESHOLD_PRICE_DROP_5M:.2%}")
        print("-" * 60)
        
        while True:
            try:
                # 动态调整检查间隔 (高频时段更频繁)
                interval = config.PRICE_CHECK_INTERVAL
                if config.is_high_frequency_time():
                    interval = max(1, interval // 2)  # 高频时段加倍频率
                    if self.check_count % 20 == 0:  # 每20次提示一次
                        print("⚡ 当前处于高频监控时段")
                
                # 获取当前价格
                price = await self.fetch_current_price()
                
                if price is not None:
                    # 记录价格
                    self.price_history.append(
                        PriceData(price, datetime.now().timestamp())
                    )
                    
                    self.check_count += 1
                    
                    # 计算涨跌幅
                    change_1m = self.calculate_change(60)
                    change_5m = self.calculate_change(300)
                    
                    # 每10次检查输出一次状态
                    if self.check_count % 10 == 0:
                        status = f"[{datetime.now().strftime('%H:%M:%S')}] "
                        status += f"价格: ${price:.2f}"
                        
                        if change_1m is not None:
                            emoji = "📉" if change_1m < 0 else "📈"
                            status += f" | 1分钟: {emoji}{change_1m:+.2%}"
                        
                        if change_5m is not None:
                            emoji = "📉" if change_5m < 0 else "📈"
                            status += f" | 5分钟: {emoji}{change_5m:+.2%}"
                        
                        status += f" | 检查次数: {self.check_count} | 警报次数: {self.alert_count}"
                        print(status)
                    
                    # 检查警报条件
                    await self.check_alert_conditions(price)
                
                # 等待下次检查
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"❌ 价格监控异常: {e}")
                await asyncio.sleep(10)  # 出错后等待10秒
    
    async def close(self):
        """关闭交易所连接"""
        await self.exchange.close()


# 测试函数
async def test_price_monitor():
    """测试价格监控器"""
    monitor = PriceMonitor()
    try:
        # 测试获取价格
        price = await monitor.fetch_current_price()
        print(f"✅ 当前黄金价格: ${price:.2f}")
        
        # 模拟运行30秒
        print("\n开始监控 (30秒测试)...")
        task = asyncio.create_task(monitor.run())
        await asyncio.sleep(30)
        task.cancel()
        
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(test_price_monitor())




