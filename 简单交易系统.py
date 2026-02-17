"""
🎯 简单交易系统 - 只提示不自动交易
核心策略：RSI超卖 + 趋势突破 + 移动止损

特点：
1. 信号简单明确，不会互相抵消
2. 只发飞书通知，不自动下单
3. 提供一键下单工具，您确认后执行
4. 自动监控持仓，移动止损锁利润
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv('.env.trading')

# 配置
FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK_URL')
CNY_RATE = 6.94

def send_feishu(title: str, message: str, color: str = "blue"):
    """发送飞书通知"""
    if not FEISHU_WEBHOOK:
        logger.info(f"[飞书] {title}: {message[:100]}...")
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
        logger.info(f"✅ 飞书通知已发送: {title}")
    except Exception as e:
        logger.error(f"❌ 飞书发送失败: {e}")


class SimpleSignalGenerator:
    """简单信号生成器 - RSI + 趋势突破"""
    
    def __init__(self):
        self.last_signal_time = None
        self.signal_cooldown = 1800  # 信号冷却30分钟
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    def calculate_ma(self, prices: pd.Series, period: int) -> float:
        """计算均线"""
        return float(prices.rolling(period).mean().iloc[-1])
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        分析K线数据，生成交易信号
        
        信号逻辑（简单明确）：
        1. RSI < 30 = 超卖信号（做多）
        2. RSI > 70 = 超买信号（做空/平多）
        3. 价格突破20日均线 = 趋势信号
        4. 价格在均线上方 + RSI回调 = 回调做多
        """
        close = df['close']
        current_price = float(close.iloc[-1])
        
        # 计算指标
        rsi = self.calculate_rsi(close)
        ma20 = self.calculate_ma(close, 20)
        ma50 = self.calculate_ma(close, 50) if len(close) >= 50 else ma20
        
        # 趋势判断（价格高于MA20就是上涨趋势！）
        trend = "上涨" if current_price > ma20 else "下跌"
        strong_trend = current_price > ma50 and ma20 > ma50
        
        # 调试日志
        logger.info(f"   MA50: ${ma50:.2f}, 强趋势: {strong_trend}")
        
        # 信号生成
        signal = 0
        signal_type = ""
        reasons = []
        
        # 信号1：RSI超卖（强做多信号）
        if rsi < 35:  # 放宽到35
            signal = 1.0
            signal_type = "🟢 RSI超卖做多"
            reasons.append(f"RSI={rsi:.1f}<35（超卖）")
        
        # 信号2：RSI超买（平仓/做空信号）
        elif rsi > 75:  # 收紧到75，牛市RSI常在60-70
            signal = -0.5
            signal_type = "🔴 RSI超买警告"
            reasons.append(f"RSI={rsi:.1f}>75（超买）")
        
        # 信号3：趋势回调做多（关键改进！）
        elif trend == "上涨" and 35 <= rsi <= 50:  # 放宽区间
            signal = 0.7
            signal_type = "🟡 趋势回调做多"
            reasons.append(f"价格>${ma50:.0f}（上涨趋势）")
            reasons.append(f"RSI={rsi:.1f}（回调区间）")
        
        # 信号4：强趋势顺势做多
        elif strong_trend and rsi < 65:  # 放宽到65
            signal = 0.5
            signal_type = "🟢 强趋势顺势"
            reasons.append("MA20>MA50（强趋势）")
            reasons.append(f"RSI={rsi:.1f}（未超买）")
        
        # 无信号
        else:
            signal_type = "⚪ 观望"
            reasons.append(f"RSI={rsi:.1f}（中性区间）")
        
        return {
            'signal': signal,
            'signal_type': signal_type,
            'price': current_price,
            'rsi': rsi,
            'ma20': ma20,
            'trend': trend,
            'reasons': reasons,
            'should_notify': abs(signal) >= 0.5  # 信号强度>=50%才通知
        }


class PositionMonitor:
    """持仓监控 - 移动止损"""
    
    def __init__(self):
        from okx_client import OKXClient
        self.client = OKXClient()
        self.initialized = False
    
    async def check_positions(self, current_price: float) -> Optional[Dict]:
        """检查持仓，计算移动止损"""
        try:
            # 确保客户端已初始化
            if not self.initialized:
                await self.client.initialize()
                self.initialized = True
            
            positions = await self.client.get_positions()
            
            if not positions:
                return None
            
            for pos in positions:
                if pos.get('instId') != 'XAU-USDT-SWAP':
                    continue
                
                size = float(pos.get('pos', 0))
                if size == 0:
                    continue
                
                entry_price = float(pos.get('avgPx', 0))
                pnl = float(pos.get('upl', 0))
                pnl_ratio = float(pos.get('uplRatio', 0))
                
                # 计算建议止损位
                if size > 0:  # 多头
                    if pnl_ratio >= 0.10:
                        suggested_stop = entry_price * 1.08  # 锁定8%
                    elif pnl_ratio >= 0.05:
                        suggested_stop = entry_price * 1.035  # 锁定3.5%
                    elif pnl_ratio >= 0.03:
                        suggested_stop = entry_price * 1.02  # 锁定2%
                    elif pnl_ratio >= 0.02:
                        suggested_stop = entry_price * 1.01  # 锁定1%
                    elif pnl_ratio >= 0.01:
                        suggested_stop = entry_price  # 保本
                    else:
                        suggested_stop = entry_price * 0.97  # 初始止损3%
                else:  # 空头
                    suggested_stop = entry_price * 1.03
                
                return {
                    'size': size,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'pnl': pnl,
                    'pnl_ratio': pnl_ratio,
                    'suggested_stop': suggested_stop,
                    'is_long': size > 0
                }
        except Exception as e:
            logger.error(f"检查持仓失败: {e}")
        
        return None


class SimpleTradingSystem:
    """简单交易系统主类"""
    
    def __init__(self):
        from okx_client import OKXClient
        self.client = OKXClient()
        self.signal_gen = SimpleSignalGenerator()
        self.position_monitor = PositionMonitor()
        self.last_notify_time = None
        self.notify_cooldown = 900  # 通知冷却15分钟
    
    async def run(self):
        """运行系统"""
        await self.client.initialize()
        
        print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🎯 简单交易系统 - 安全模式                          ║
    ║                                                              ║
    ║  特点：                                                       ║
    ║    • 只发通知，不自动交易                                     ║
    ║    • RSI超卖/超买 + 趋势突破                                  ║
    ║    • 移动止损建议                                             ║
    ║    • 您有最终决定权                                           ║
    ║                                                              ║
    ║  🔔 信号会推送到飞书，请注意查看！                            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止系统
        """)
        
        # 启动通知
        send_feishu(
            "🎯 简单交易系统已启动",
            f"**模式：** 只通知，不自动交易\n"
            f"**策略：** RSI超卖/超买 + 趋势突破\n"
            f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"⚠️ 所有交易需要您手动确认！",
            "green"
        )
        
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {scan_count} 次扫描")
                logger.info(f"{'='*60}")
                
                # 1. 获取价格
                price = await self.client.get_ticker("XAU-USDT-SWAP")
                if not price:
                    logger.error("❌ 获取价格失败")
                    await asyncio.sleep(60)
                    continue
                
                logger.info(f"💰 当前价格: ${price:.2f}")
                
                # 2. 获取K线分析
                klines = await self.client.get_klines("XAU-USDT-SWAP", "15m", 100)
                if klines:
                    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = df[col].astype(float)
                    # OKX返回从新到旧，需要反转为从旧到新
                    df = df.iloc[::-1].reset_index(drop=True)
                    
                    # 3. 生成信号
                    signal = self.signal_gen.analyze(df)
                    
                    logger.info(f"📊 信号: {signal['signal_type']}")
                    logger.info(f"   RSI: {signal['rsi']:.1f}")
                    logger.info(f"   MA20: ${signal['ma20']:.2f}")
                    logger.info(f"   趋势: {signal['trend']}")
                    
                    # 4. 检查是否需要通知
                    if signal['should_notify']:
                        now = datetime.now()
                        if self.last_notify_time is None or (now - self.last_notify_time).seconds > self.notify_cooldown:
                            self._send_signal_notification(signal, price)
                            self.last_notify_time = now
                
                # 5. 检查持仓
                position = await self.position_monitor.check_positions(price)
                if position:
                    logger.info(f"\n📈 持仓监控:")
                    logger.info(f"   方向: {'多头' if position['is_long'] else '空头'}")
                    logger.info(f"   数量: {abs(position['size']):.0f}张")
                    logger.info(f"   入场: ${position['entry_price']:.2f}")
                    logger.info(f"   盈亏: {position['pnl_ratio']:.1%} (${position['pnl']:.2f})")
                    logger.info(f"   建议止损: ${position['suggested_stop']:.2f}")
                    
                    # 如果接近止损位，发警告
                    if position['is_long'] and price <= position['suggested_stop'] * 1.005:
                        send_feishu(
                            "⚠️ 接近止损位",
                            f"**当前价格：** ${price:.2f}\n"
                            f"**建议止损：** ${position['suggested_stop']:.2f}\n"
                            f"**盈亏：** {position['pnl_ratio']:.1%}\n\n"
                            f"请考虑是否平仓！",
                            "yellow"
                        )
                
                # 6. 等待下次扫描
                await asyncio.sleep(60)  # 每分钟扫描一次
                
        except KeyboardInterrupt:
            logger.info("\n👋 系统已停止")
        finally:
            await self.client.close()
    
    def _send_signal_notification(self, signal: Dict, price: float):
        """发送信号通知"""
        reasons = "\n".join([f"• {r}" for r in signal['reasons']])
        
        if signal['signal'] > 0:
            action = "📈 建议做多"
            color = "green"
        elif signal['signal'] < 0:
            action = "📉 建议观望/平仓"
            color = "red"
        else:
            action = "⚪ 观望"
            color = "blue"
        
        message = f"""**{signal['signal_type']}**

**当前价格：** ${price:.2f}
**信号强度：** {abs(signal['signal']):.0%}

**分析原因：**
{reasons}

**{action}**

⚠️ 请在OKX App手动操作！
系统不会自动下单。
"""
        
        send_feishu(f"🔔 交易信号 - {signal['signal_type']}", message, color)


async def main():
    system = SimpleTradingSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())

