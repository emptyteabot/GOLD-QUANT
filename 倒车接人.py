"""
🚗 倒车接人专用系统
整合所有能产生Alpha的逻辑：
1. RSI策略（回测+15.5%）
2. 暴跌检测
3. K线形态（锤子线、启明星、看涨吞没）
4. 移动止损
5. 飞书通知

只发通知，不自动交易！
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv('.env.trading')

# ============================================================
# 配置
# ============================================================
FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK_URL')
CNY_RATE = 7.2

# Tushare配置（可选，用于宏观数据）
TUSHARE_TOKEN = "2406c659bbbdd44678d8e864239efa6f7b3258fbdae026cc13dcb7d7f956"
TUSHARE_URL = "http://lianghua.nanyangqiankun.top"


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
        logger.info(f"✅ 飞书通知: {title}")
    except Exception as e:
        logger.error(f"❌ 飞书失败: {e}")


# ============================================================
# 核心策略：RSI + 暴跌检测 + K线形态
# ============================================================
class DipBuyingStrategy:
    """倒车接人策略"""
    
    def __init__(self):
        self.last_signal_time = None
        self.signal_cooldown = 900  # 15分钟冷却
    
    # -------------------- 技术指标计算 --------------------
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
    
    def calculate_ma(self, prices: pd.Series, period: int) -> float:
        """计算均线"""
        return float(prices.rolling(period).mean().iloc[-1])
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        """计算波动率"""
        returns = prices.pct_change()
        return float(returns.rolling(period).std().iloc[-1] * np.sqrt(24))  # 日化
    
    def calculate_z_score(self, price: float, prices: pd.Series, period: int = 50) -> float:
        """计算Z-Score"""
        mean = prices.rolling(period).mean().iloc[-1]
        std = prices.rolling(period).std().iloc[-1]
        if std > 0:
            return (price - mean) / std
        return 0
    
    # -------------------- 暴跌检测 --------------------
    
    def detect_crash(self, df: pd.DataFrame) -> Dict:
        """
        检测暴跌
        
        触发条件：
        - 最近5根K线跌幅 > 2%
        - RSI < 30
        - 成交量放大 > 1.5倍
        """
        close = df['close']
        volume = df['volume']
        
        # 计算跌幅
        drop_5 = (close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] * 100 if len(close) > 6 else 0
        drop_15 = (close.iloc[-1] - close.iloc[-16]) / close.iloc[-16] * 100 if len(close) > 16 else 0
        
        # RSI
        rsi = self.calculate_rsi(close)
        
        # 成交量比率
        vol_ratio = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1] if len(volume) > 20 else 1
        
        # 判断暴跌
        crash_score = 0
        reasons = []
        
        if drop_5 < -1.5:
            crash_score += 40
            reasons.append(f"5K跌{abs(drop_5):.1f}%")
        
        if drop_15 < -3:
            crash_score += 30
            reasons.append(f"15K跌{abs(drop_15):.1f}%")
        
        if rsi < 30:
            crash_score += 20
            reasons.append(f"RSI={rsi:.0f}超卖")
        
        if vol_ratio > 1.5:
            crash_score += 10
            reasons.append(f"放量{vol_ratio:.1f}x")
        
        return {
            'detected': crash_score >= 50,
            'score': crash_score,
            'drop_5': drop_5,
            'drop_15': drop_15,
            'rsi': rsi,
            'vol_ratio': vol_ratio,
            'reasons': reasons
        }
    
    # -------------------- K线形态识别 --------------------
    
    def detect_reversal_pattern(self, df: pd.DataFrame) -> Optional[str]:
        """
        检测反转K线形态
        
        识别：
        1. 锤子线（Hammer）
        2. 启明星（Morning Star）
        3. 看涨吞没（Bullish Engulfing）
        """
        if len(df) < 3:
            return None
        
        k1 = df.iloc[-3]
        k2 = df.iloc[-2]
        k3 = df.iloc[-1]
        
        # 锤子线
        if self._is_hammer(k3):
            return "🔨 锤子线"
        
        # 启明星
        if self._is_morning_star(k1, k2, k3):
            return "⭐ 启明星"
        
        # 看涨吞没
        if self._is_bullish_engulfing(k2, k3):
            return "🐂 看涨吞没"
        
        return None
    
    def _is_hammer(self, k: pd.Series) -> bool:
        """锤子线：下影线长，实体小，上影线短"""
        body = abs(k['close'] - k['open'])
        lower_shadow = min(k['open'], k['close']) - k['low']
        upper_shadow = k['high'] - max(k['open'], k['close'])
        
        return (lower_shadow >= body * 2 and 
                upper_shadow <= body * 0.3 and
                k['close'] > k['open'])
    
    def _is_morning_star(self, k1, k2, k3) -> bool:
        """启明星：大阴线 + 十字星 + 大阳线"""
        body1 = k1['open'] - k1['close']  # 第一根阴线
        body2 = abs(k2['close'] - k2['open'])  # 第二根小实体
        body3 = k3['close'] - k3['open']  # 第三根阳线
        
        return (body1 > 0 and  # 第一根是阴线
                body2 < body1 * 0.3 and  # 第二根小实体
                body3 > 0 and  # 第三根是阳线
                k3['close'] > (k1['open'] + k1['close']) / 2)  # 收盘超过第一根中点
    
    def _is_bullish_engulfing(self, k1, k2) -> bool:
        """看涨吞没：阴线被阳线完全包住"""
        return (k1['close'] < k1['open'] and  # 第一根阴线
                k2['close'] > k2['open'] and  # 第二根阳线
                k2['open'] < k1['close'] and  # 阳线开盘低于阴线收盘
                k2['close'] > k1['open'])  # 阳线收盘高于阴线开盘
    
    # -------------------- 主分析函数 --------------------
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        综合分析，生成倒车接人信号
        
        信号优先级：
        1. 暴跌 + K线反转形态 = 最强信号（100%）
        2. RSI < 30 = 强做多（80%）
        3. RSI < 40 + 上涨趋势 = 回调做多（60%）
        4. RSI 40-50 + 强趋势 = 顺势做多（40%）
        """
        close = df['close']
        current_price = float(close.iloc[-1])
        
        # 计算基础指标
        rsi = self.calculate_rsi(close)
        ma20 = self.calculate_ma(close, 20)
        ma50 = self.calculate_ma(close, 50) if len(close) >= 50 else ma20
        z_score = self.calculate_z_score(current_price, close)
        volatility = self.calculate_volatility(close)
        
        # 趋势判断
        trend = "上涨" if current_price > ma20 else "下跌"
        strong_trend = current_price > ma50 and ma20 > ma50
        
        # 检测暴跌
        crash = self.detect_crash(df)
        
        # 检测K线形态
        pattern = self.detect_reversal_pattern(df)
        
        # 生成信号
        signal = 0
        signal_type = ""
        reasons = []
        urgency = "LOW"
        
        # ========== 信号1：暴跌 + 反转形态（最强！） ==========
        if crash['detected'] and pattern:
            signal = 1.0
            signal_type = f"🚨 暴跌反转 {pattern}"
            urgency = "CRITICAL"
            reasons.extend(crash['reasons'])
            reasons.append(pattern)
        
        # ========== 信号2：RSI极度超卖 ==========
        elif rsi < 30:
            signal = 0.8
            signal_type = "🟢 RSI极度超卖"
            urgency = "HIGH"
            reasons.append(f"RSI={rsi:.1f} < 30")
            if z_score < -2:
                signal = 0.9
                reasons.append(f"Z-Score={z_score:.1f}（极度低估）")
        
        # ========== 信号3：暴跌中（等待反转） ==========
        elif crash['detected']:
            signal = 0.3
            signal_type = "⚠️ 暴跌检测中"
            urgency = "MEDIUM"
            reasons.extend(crash['reasons'])
            reasons.append("等待反转K线确认")
        
        # ========== 信号4：RSI超卖 + 上涨趋势 ==========
        elif rsi < 40 and trend == "上涨":
            signal = 0.6
            signal_type = "🟡 趋势回调做多"
            urgency = "MEDIUM"
            reasons.append(f"RSI={rsi:.1f}（超卖区）")
            reasons.append(f"价格>${ma20:.0f}（上涨趋势）")
        
        # ========== 信号5：强趋势顺势 ==========
        elif strong_trend and rsi < 60:
            signal = 0.4
            signal_type = "🟢 强趋势顺势"
            reasons.append("MA20 > MA50")
            reasons.append(f"RSI={rsi:.1f}（未超买）")
        
        # ========== 信号6：RSI超买警告 ==========
        elif rsi > 75:
            signal = -0.5
            signal_type = "🔴 RSI超买警告"
            urgency = "HIGH"
            reasons.append(f"RSI={rsi:.1f} > 75（考虑止盈）")
        
        # ========== 无信号 ==========
        else:
            signal_type = "⚪ 观望"
            reasons.append(f"RSI={rsi:.1f}（中性）")
        
        return {
            'signal': signal,
            'signal_type': signal_type,
            'urgency': urgency,
            'price': current_price,
            'rsi': rsi,
            'ma20': ma20,
            'ma50': ma50,
            'z_score': z_score,
            'trend': trend,
            'strong_trend': strong_trend,
            'crash': crash,
            'pattern': pattern,
            'reasons': reasons,
            'should_notify': abs(signal) >= 0.4 or crash['detected']
        }


# ============================================================
# 移动止损管理
# ============================================================
class TrailingStopManager:
    """移动止损管理器"""
    
    # 止损规则（多头）
    STOP_RULES = [
        (0.15, 0.12),   # 盈利15% → 锁定12%
        (0.10, 0.08),   # 盈利10% → 锁定8%
        (0.05, 0.035),  # 盈利5% → 锁定3.5%
        (0.03, 0.02),   # 盈利3% → 锁定2%
        (0.02, 0.01),   # 盈利2% → 锁定1%
        (0.01, 0.0),    # 盈利1% → 保本
    ]
    
    def calculate_stop(self, entry_price: float, current_price: float, is_long: bool) -> Dict:
        """计算建议止损位"""
        if is_long:
            pnl_ratio = (current_price - entry_price) / entry_price
        else:
            pnl_ratio = (entry_price - current_price) / entry_price
        
        # 默认止损3%
        stop_loss_pct = -0.03
        lock_profit_pct = 0
        
        # 根据盈利比例调整止损
        for profit_threshold, lock_pct in self.STOP_RULES:
            if pnl_ratio >= profit_threshold:
                stop_loss_pct = lock_pct
                lock_profit_pct = lock_pct
                break
        
        # 计算止损价
        if is_long:
            stop_price = entry_price * (1 + stop_loss_pct)
        else:
            stop_price = entry_price * (1 - stop_loss_pct)
        
        return {
            'pnl_ratio': pnl_ratio,
            'stop_price': stop_price,
            'lock_profit_pct': lock_profit_pct,
            'should_alert': is_long and current_price <= stop_price * 1.005
        }


# ============================================================
# 主系统
# ============================================================
class DipBuyingSystem:
    """倒车接人主系统"""
    
    def __init__(self):
        from okx_client import OKXClient
        self.client = OKXClient()
        self.strategy = DipBuyingStrategy()
        self.stop_manager = TrailingStopManager()
        self.last_notify_time = {}
        self.notify_cooldown = 600  # 10分钟冷却
    
    async def run(self):
        """运行系统"""
        await self.client.initialize()
        
        print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║              🚗 倒车接人专用系统                              ║
    ║                                                              ║
    ║  策略：                                                       ║
    ║    • RSI超卖做多（回测+15.5%）                                ║
    ║    • 暴跌反转检测                                             ║
    ║    • K线形态识别（锤子线/启明星/看涨吞没）                    ║
    ║    • 移动止损保护利润                                         ║
    ║                                                              ║
    ║  ⚠️ 只发通知，不自动交易！                                   ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止系统
        """)
        
        send_feishu(
            "🚗 倒车接人系统已启动",
            f"**策略：** RSI超卖 + 暴跌反转 + K线形态\n"
            f"**回测收益：** +15.5%\n"
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
                    await asyncio.sleep(30)
                    continue
                
                price_cny = price * CNY_RATE
                logger.info(f"💰 价格: ${price:.2f} (¥{price_cny:.0f})")
                
                # 2. 获取K线
                klines = await self.client.get_klines("XAU-USDT-SWAP", "15m", 100)
                if not klines:
                    logger.error("❌ 获取K线失败")
                    await asyncio.sleep(30)
                    continue
                
                # 解析K线
                df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                df = df.iloc[::-1].reset_index(drop=True)  # 反转为从旧到新
                
                # 3. 分析信号
                signal = self.strategy.analyze(df)
                
                # 显示结果
                logger.info(f"📊 信号: {signal['signal_type']}")
                logger.info(f"   RSI: {signal['rsi']:.1f}")
                logger.info(f"   趋势: {signal['trend']} | 强趋势: {signal['strong_trend']}")
                logger.info(f"   Z-Score: {signal['z_score']:.2f}")
                
                if signal['crash']['detected']:
                    logger.warning(f"   🚨 暴跌检测: {', '.join(signal['crash']['reasons'])}")
                
                if signal['pattern']:
                    logger.info(f"   📍 K线形态: {signal['pattern']}")
                
                # 4. 发送通知
                if signal['should_notify']:
                    self._send_signal_notification(signal, price)
                
                # 5. 检查持仓
                await self._check_positions(price)
                
                # 6. 等待
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("\n👋 系统已停止")
        finally:
            await self.client.close()
    
    def _send_signal_notification(self, signal: Dict, price: float):
        """发送信号通知"""
        # 检查冷却
        signal_key = signal['signal_type']
        now = datetime.now()
        
        if signal_key in self.last_notify_time:
            elapsed = (now - self.last_notify_time[signal_key]).seconds
            if elapsed < self.notify_cooldown:
                return
        
        self.last_notify_time[signal_key] = now
        
        # 构建消息
        reasons = "\n".join([f"• {r}" for r in signal['reasons']])
        
        if signal['signal'] >= 0.8:
            action = "🚀 **强烈建议做多！**"
            color = "green"
        elif signal['signal'] >= 0.5:
            action = "📈 **建议做多**"
            color = "green"
        elif signal['signal'] >= 0.3:
            action = "👀 **关注中，等待确认**"
            color = "yellow"
        elif signal['signal'] < 0:
            action = "📉 **考虑止盈/观望**"
            color = "red"
        else:
            action = "⚪ **观望**"
            color = "blue"
        
        message = f"""**{signal['signal_type']}**

**当前价格：** ${price:.2f} (¥{price * CNY_RATE:.0f})
**信号强度：** {abs(signal['signal']):.0%}
**紧急程度：** {signal['urgency']}

**分析原因：**
{reasons}

**技术指标：**
• RSI: {signal['rsi']:.1f}
• MA20: ${signal['ma20']:.2f}
• Z-Score: {signal['z_score']:.2f}
• 趋势: {signal['trend']}

{action}

⚠️ 请在OKX App手动操作！
"""
        
        send_feishu(f"🚗 倒车信号 - {signal['signal_type']}", message, color)
    
    async def _check_positions(self, current_price: float):
        """检查持仓，计算止损"""
        try:
            positions = await self.client.get_positions()
            
            if not positions:
                return
            
            for pos in positions:
                if pos.get('instId') != 'XAU-USDT-SWAP':
                    continue
                
                size = float(pos.get('pos', 0))
                if size == 0:
                    continue
                
                entry_price = float(pos.get('avgPx', 0))
                pnl = float(pos.get('upl', 0))
                is_long = size > 0
                
                # 计算止损
                stop_info = self.stop_manager.calculate_stop(entry_price, current_price, is_long)
                
                direction = "多头" if is_long else "空头"
                logger.info(f"\n📈 持仓: {direction} {abs(size):.0f}张")
                logger.info(f"   入场: ${entry_price:.2f}")
                logger.info(f"   盈亏: {stop_info['pnl_ratio']:.1%} (${pnl:.2f})")
                logger.info(f"   建议止损: ${stop_info['stop_price']:.2f}")
                
                if stop_info['lock_profit_pct'] > 0:
                    logger.info(f"   🔒 已锁定利润: {stop_info['lock_profit_pct']:.1%}")
                
                # 接近止损发警告
                if stop_info['should_alert']:
                    send_feishu(
                        "⚠️ 接近止损位！",
                        f"**当前价格：** ${current_price:.2f}\n"
                        f"**止损价：** ${stop_info['stop_price']:.2f}\n"
                        f"**盈亏：** {stop_info['pnl_ratio']:.1%}\n\n"
                        f"请考虑是否平仓！",
                        "red"
                    )
        except Exception as e:
            logger.error(f"检查持仓失败: {e}")


# ============================================================
# 入口
# ============================================================
async def main():
    system = DipBuyingSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())
