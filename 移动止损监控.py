"""
🛡️ 移动止损监控 - 保护您的利润
自动监控持仓，推送止损建议到飞书
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'

import asyncio
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv('.env.trading')

FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK_URL')


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
    except Exception as e:
        logger.error(f"飞书发送失败: {e}")


class TrailingStopMonitor:
    """移动止损监控"""
    
    def __init__(self):
        from okx_client import OKXClient
        self.client = OKXClient()
        self.last_alert_time = None
        self.alert_cooldown = 300  # 警告冷却5分钟
        self.highest_profit_ratio = 0  # 记录最高盈利
        
        # 移动止损规则
        self.stop_rules = [
            # (盈利比例, 止损比例)
            (0.15, 0.12),   # 盈利15%，止损锁定12%
            (0.10, 0.08),   # 盈利10%，止损锁定8%
            (0.05, 0.035),  # 盈利5%，止损锁定3.5%
            (0.03, 0.02),   # 盈利3%，止损锁定2%
            (0.02, 0.01),   # 盈利2%，止损锁定1%
            (0.01, 0.00),   # 盈利1%，保本
        ]
    
    def calculate_stop_loss(self, entry_price: float, pnl_ratio: float, is_long: bool) -> tuple:
        """
        计算移动止损价格
        返回：(止损价格, 锁定利润比例)
        """
        for profit_threshold, lock_ratio in self.stop_rules:
            if pnl_ratio >= profit_threshold:
                if is_long:
                    stop_price = entry_price * (1 + lock_ratio)
                else:
                    stop_price = entry_price * (1 - lock_ratio)
                return stop_price, lock_ratio
        
        # 默认止损3%
        if is_long:
            return entry_price * 0.97, -0.03
        else:
            return entry_price * 1.03, -0.03
    
    async def run(self):
        """运行监控"""
        await self.client.initialize()
        
        print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                 🛡️ 移动止损监控                               ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  止损规则（多头）:                                            ║
    ║    • 盈利 1%  → 止损移到保本                                  ║
    ║    • 盈利 2%  → 锁定 1% 利润                                  ║
    ║    • 盈利 3%  → 锁定 2% 利润                                  ║
    ║    • 盈利 5%  → 锁定 3.5% 利润                                ║
    ║    • 盈利 10% → 锁定 8% 利润                                  ║
    ║    • 盈利 15% → 锁定 12% 利润                                 ║
    ║                                                              ║
    ║  ⚠️ 只发通知，不自动平仓！                                    ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止监控
        """)
        
        send_feishu(
            "🛡️ 移动止损监控已启动",
            f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"监控中，接近止损位会发送通知！",
            "green"
        )
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                
                # 获取当前价格
                price = await self.client.get_ticker("XAU-USDT-SWAP")
                if not price:
                    await asyncio.sleep(10)
                    continue
                
                # 获取持仓
                positions = await self.client.get_positions()
                
                has_position = False
                for pos in (positions or []):
                    if pos.get('instId') != 'XAU-USDT-SWAP':
                        continue
                    
                    size = float(pos.get('pos', 0))
                    if size == 0:
                        continue
                    
                    has_position = True
                    entry_price = float(pos.get('avgPx', 0))
                    pnl = float(pos.get('upl', 0))
                    pnl_ratio = float(pos.get('uplRatio', 0))
                    is_long = size > 0
                    
                    # 更新最高盈利
                    if pnl_ratio > self.highest_profit_ratio:
                        self.highest_profit_ratio = pnl_ratio
                    
                    # 计算止损
                    stop_price, lock_ratio = self.calculate_stop_loss(entry_price, pnl_ratio, is_long)
                    
                    # 计算距离止损的百分比
                    if is_long:
                        distance = (price - stop_price) / stop_price
                    else:
                        distance = (stop_price - price) / stop_price
                    
                    # 日志
                    if check_count % 6 == 0:  # 每分钟打印一次
                        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] "
                                   f"价格:${price:.2f} | "
                                   f"持仓:{int(abs(size))}张{'多' if is_long else '空'} | "
                                   f"盈亏:{pnl_ratio:+.1%} | "
                                   f"止损:${stop_price:.2f}")
                    
                    # 检查是否接近止损
                    now = datetime.now()
                    can_alert = (self.last_alert_time is None or 
                                (now - self.last_alert_time).seconds > self.alert_cooldown)
                    
                    # 价格接近止损位（0.5%以内）
                    if distance < 0.005 and can_alert:
                        self.last_alert_time = now
                        send_feishu(
                            "⚠️ 接近止损位 - 请注意！",
                            f"**当前价格：** ${price:.2f}\n"
                            f"**止损价格：** ${stop_price:.2f}\n"
                            f"**距离：** {distance:.1%}\n"
                            f"**当前盈亏：** {pnl_ratio:+.1%} (${pnl:.2f})\n"
                            f"**锁定利润：** {lock_ratio:+.0%}\n\n"
                            f"⚡ 建议立即检查是否需要平仓！",
                            "red"
                        )
                    
                    # 已触发止损
                    elif ((is_long and price <= stop_price) or 
                          (not is_long and price >= stop_price)) and can_alert:
                        self.last_alert_time = now
                        send_feishu(
                            "🚨 已触发止损 - 请立即操作！",
                            f"**当前价格：** ${price:.2f}\n"
                            f"**止损价格：** ${stop_price:.2f}\n"
                            f"**当前盈亏：** {pnl_ratio:+.1%} (${pnl:.2f})\n"
                            f"**最高盈利：** {self.highest_profit_ratio:+.1%}\n\n"
                            f"🔴 建议立即平仓！",
                            "red"
                        )
                    
                    # 新高提醒
                    elif pnl_ratio > 0.10 and pnl_ratio == self.highest_profit_ratio and can_alert:
                        self.last_alert_time = now
                        send_feishu(
                            "🎉 利润新高 - 考虑止盈",
                            f"**当前价格：** ${price:.2f}\n"
                            f"**当前盈亏：** {pnl_ratio:+.1%} (${pnl:.2f})\n"
                            f"**止损已提升至：** ${stop_price:.2f}\n"
                            f"**锁定利润：** {lock_ratio:+.0%}\n\n"
                            f"💡 可考虑部分止盈，锁定利润！",
                            "green"
                        )
                
                if not has_position and check_count % 60 == 0:  # 10分钟提醒一次
                    logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 无持仓")
                
                await asyncio.sleep(10)  # 每10秒检查一次
                
        except KeyboardInterrupt:
            logger.info("\n👋 监控已停止")
        finally:
            await self.client.close()


async def main():
    monitor = TrailingStopMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
