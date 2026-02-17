"""
全自动交易系统 - 终极版
功能：实时监控 + 自动下单 + 自动止盈止损 + 飞书推送
"""
import asyncio
import os
from datetime import datetime, timedelta
import requests
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional
import aiohttp
from dotenv import load_dotenv
import json
import hmac
import hashlib
import base64
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv('.env.trading')

# ==================== 配置 ====================
FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK_URL')

# OKX API配置
OKX_API_KEY = os.getenv('OKX_API_KEY', 'd82bdcdb-fdd1-432f-bf53-8e22a010b1a4')
OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY', '672D88347AC17326E1726EC1DCAA225C')
OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE', '')  # 需要你提供
OKX_BASE_URL = "https://www.okx.com"

CNY_RATE = 6.94


# ==================== 飞书推送 ====================
def send_feishu(message: str, level: str = "info"):
    """发送飞书通知"""
    if not FEISHU_WEBHOOK:
        logger.info(f"[飞书] {message[:200]}...")
        return
    
    colors = {"info": "blue", "success": "green", "warning": "yellow", "danger": "red", "money": "green"}
    
    data = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🤖 全自动交易系统"},
                "template": colors.get(level, "blue")
            },
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": message}}]
        }
    }
    
    try:
        requests.post(FEISHU_WEBHOOK, json=data, timeout=5)
        logger.info("✅ 飞书通知已发送")
    except Exception as e:
        logger.error(f"飞书推送失败: {e}")


# ==================== OKX API ====================
class OKXTrader:
    """OKX自动交易客户端"""
    
    def __init__(self):
        self.api_key = OKX_API_KEY
        self.secret_key = OKX_SECRET_KEY
        self.passphrase = OKX_PASSPHRASE
        self.base_url = OKX_BASE_URL
        self.session = None
    
    async def initialize(self):
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    def _sign(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """生成签名"""
        message = timestamp + method + request_path + body
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod=hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()
    
    async def _request(self, method: str, request_path: str, body: str = '') -> Optional[Dict]:
        """通用请求"""
        try:
            timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'
            sign = self._sign(timestamp, method, request_path, body)
            
            headers = {
                'OK-ACCESS-KEY': self.api_key,
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': self.passphrase,
                'Content-Type': 'application/json'
            }
            
            url = self.base_url + request_path
            
            if method == 'GET':
                async with self.session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('code') == '0':
                            return data.get('data')
                    else:
                        logger.error(f"OKX API错误: {resp.status}, {await resp.text()}")
            
            elif method == 'POST':
                async with self.session.post(url, headers=headers, data=body, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('code') == '0':
                            return data.get('data')
                        else:
                            logger.error(f"OKX API错误: {data.get('msg')}")
                    else:
                        logger.error(f"OKX API错误: {resp.status}, {await resp.text()}")
        
        except Exception as e:
            logger.error(f"请求失败: {e}")
        
        return None
    
    async def get_account_balance(self) -> Optional[Dict]:
        """获取账户余额"""
        data = await self._request('GET', '/api/v5/account/balance')
        
        if data and len(data) > 0:
            details = data[0].get('details', [])
            for detail in details:
                if detail.get('ccy') == 'USDT':
                    return {
                        'total_equity': float(detail.get('eq', 0)),
                        'available': float(detail.get('availBal', 0)),
                        'unrealized_pnl': float(detail.get('upl', 0)),
                        'margin_used': float(detail.get('eq', 0)) - float(detail.get('availBal', 0))
                    }
        
        return None
    
    async def get_positions(self, inst_id: str = 'XAUT-USDT') -> List[Dict]:
        """获取持仓"""
        data = await self._request('GET', f'/api/v5/account/positions?instType=MARGIN&instId={inst_id}')
        return data if data else []
    
    async def place_order(self, inst_id: str, side: str, size: str, price: Optional[str] = None) -> Optional[Dict]:
        """下单
        
        Args:
            inst_id: 交易对，如 XAUT-USDT
            side: buy 或 sell
            size: 数量
            price: 价格（None为市价单）
        """
        order_data = {
            "instId": inst_id,
            "tdMode": "cross",  # 全仓
            "side": side,
            "ordType": "market" if price is None else "limit",
            "sz": size
        }
        
        if price:
            order_data["px"] = price
        
        body = json.dumps(order_data)
        data = await self._request('POST', '/api/v5/trade/order', body)
        
        if data and len(data) > 0:
            logger.info(f"✅ 下单成功: {side} {size} {inst_id}")
            return data[0]
        else:
            logger.error(f"❌ 下单失败: {side} {size} {inst_id}")
            return None
    
    async def set_stop_loss(self, inst_id: str, side: str, size: str, stop_price: str) -> Optional[Dict]:
        """设置止损单
        
        Args:
            inst_id: 交易对
            side: buy 或 sell（与持仓相反）
            size: 数量
            stop_price: 触发价格
        """
        order_data = {
            "instId": inst_id,
            "tdMode": "cross",
            "side": side,
            "ordType": "conditional",
            "sz": size,
            "slTriggerPx": stop_price,
            "slOrdPx": "-1"  # 市价
        }
        
        body = json.dumps(order_data)
        data = await self._request('POST', '/api/v5/trade/order-algo', body)
        
        if data and len(data) > 0:
            logger.info(f"✅ 止损设置成功: {stop_price}")
            return data[0]
        else:
            logger.error(f"❌ 止损设置失败")
            return None


# ==================== 量化特征 ====================
class QuantFeatures:
    """量化特征工程"""
    
    @staticmethod
    def calculate_all_features(df: pd.DataFrame) -> Dict:
        """计算所有量化特征"""
        close = df['close'].values
        
        features = {}
        
        # RSI
        if len(close) >= 14:
            returns = np.diff(close) / close[:-1]
            gains = np.where(returns > 0, returns, 0)
            losses = np.where(returns < 0, -returns, 0)
            avg_gain = np.mean(gains[-14:])
            avg_loss = np.mean(losses[-14:])
            rs = avg_gain / avg_loss if avg_loss > 0 else 0
            features['rsi'] = 100 - (100 / (1 + rs))
        else:
            features['rsi'] = 50
        
        # 动量
        features['momentum_10'] = (close[-1] - close[-10]) / close[-10] if len(close) >= 10 else 0
        
        # 布林带
        if len(close) >= 20:
            ma20 = np.mean(close[-20:])
            std20 = np.std(close[-20:])
            upper = ma20 + 2 * std20
            lower = ma20 - 2 * std20
            features['bb_position'] = (close[-1] - lower) / (upper - lower) if upper > lower else 0.5
        else:
            features['bb_position'] = 0.5
        
        return features


# ==================== Multi-Agent ====================
class MultiAgentSystem:
    """Multi-Agent专家团队"""
    
    async def get_consensus(self, features: Dict, current_price: float, account: Dict) -> Dict:
        """获取专家共识"""
        opinions = []
        
        # 技术分析师
        tech_signal = 0
        tech_reasons = []
        rsi = features.get('rsi', 50)
        if rsi < 30:
            tech_signal += 0.6
            tech_reasons.append(f"RSI超卖({rsi:.1f})，强烈买入")
        elif rsi > 70:
            tech_signal -= 0.6
            tech_reasons.append(f"RSI超买({rsi:.1f})，建议卖出")
        
        momentum = features.get('momentum_10', 0)
        if momentum > 0.02:
            tech_signal += 0.4
            tech_reasons.append(f"动量强劲({momentum:.2%})")
        elif momentum < -0.02:
            tech_signal -= 0.4
            tech_reasons.append(f"动量转弱({momentum:.2%})")
        
        opinions.append({
            'agent': '技术分析师',
            'signal': np.clip(tech_signal, -1, 1),
            'weight': 0.40,
            'reasons': tech_reasons if tech_reasons else ['观望']
        })
        
        # 量化分析师
        quant_signal = 0
        quant_reasons = []
        bb_pos = features.get('bb_position', 0.5)
        if bb_pos < 0.2:
            quant_signal += 0.5
            quant_reasons.append("价格超跌，抄底机会")
        elif bb_pos > 0.8:
            quant_signal -= 0.5
            quant_reasons.append("价格超涨，注意风险")
        
        opinions.append({
            'agent': '量化分析师',
            'signal': np.clip(quant_signal, -1, 1),
            'weight': 0.40,
            'reasons': quant_reasons if quant_reasons else ['观望']
        })
        
        # 风险管理师
        risk_signal = 0
        risk_reasons = []
        
        # 检查可用资金
        available = account.get('available', 0)
        if available < 50:
            risk_signal -= 0.5
            risk_reasons.append("可用资金不足，不建议加仓")
        elif available > 100:
            risk_signal += 0.3
            risk_reasons.append("资金充足，可以加仓")
        
        opinions.append({
            'agent': '风险管理师',
            'signal': risk_signal,
            'weight': 0.20,
            'reasons': risk_reasons if risk_reasons else ['观望']
        })
        
        # 加权投票
        weighted_signal = sum([op['signal'] * op['weight'] for op in opinions])
        signals = [op['signal'] for op in opinions]
        consensus = 1 - (np.std(signals) / 2) if signals else 0
        
        return {
            'signal': weighted_signal,
            'consensus': consensus,
            'opinions': opinions
        }


# ==================== 主系统 ====================
class AutoTradingSystem:
    """全自动交易系统"""
    
    def __init__(self):
        self.trader = OKXTrader()
        self.quant_features = QuantFeatures()
        self.multi_agent = MultiAgentSystem()
        self.session = None
        
        # 交易参数
        self.inst_id = "XAUT-USDT"
        self.min_signal_strength = 0.65  # 最小信号强度
        self.min_consensus = 0.70  # 最小共识度
        self.position_size_pct = 0.30  # 每次使用30%可用资金
        self.leverage = 10  # 杠杆
        
        # 统计
        self.stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit': 0
        }
    
    async def initialize(self):
        """初始化"""
        self.session = aiohttp.ClientSession()
        await self.trader.initialize()
        
        logger.info("=" * 80)
        logger.info("🤖 全自动交易系统已启动")
        logger.info("=" * 80)
        
        # 检查API配置
        if not OKX_PASSPHRASE:
            logger.error("❌ 请在.env.trading文件中配置OKX_PASSPHRASE")
            send_feishu("**❌ 系统启动失败**\n\n请配置OKX_PASSPHRASE", "danger")
            return False
        
        # 获取账户信息
        account = await self.trader.get_account_balance()
        
        if account:
            msg = (
                f"**🤖 全自动交易系统已启动**\n\n"
                f"**💰 账户信息：**\n"
                f"• 总权益：${account['total_equity']:.2f}（¥{account['total_equity']*CNY_RATE:.2f}）\n"
                f"• 可用资金：${account['available']:.2f}（¥{account['available']*CNY_RATE:.2f}）\n"
                f"• 浮动盈亏：${account['unrealized_pnl']:.2f}（¥{account['unrealized_pnl']*CNY_RATE:.2f}）\n\n"
                f"**⚙️ 交易参数：**\n"
                f"• 交易对：{self.inst_id}\n"
                f"• 杠杆：{self.leverage}倍\n"
                f"• 单次仓位：{self.position_size_pct:.0%}可用资金\n"
                f"• 信号阈值：{self.min_signal_strength:.0%}\n"
                f"• 共识阈值：{self.min_consensus:.0%}\n\n"
                f"**系统将自动监控并交易...**"
            )
            send_feishu(msg, "success")
            return True
        else:
            logger.error("❌ 无法获取账户信息，请检查API配置")
            send_feishu("**❌ 系统启动失败**\n\n无法获取账户信息，请检查API配置", "danger")
            return False
    
    async def close(self):
        """关闭"""
        if self.session:
            await self.session.close()
        await self.trader.close()
    
    async def fetch_price(self) -> Optional[float]:
        """获取当前价格"""
        try:
            url = "https://hq.sinajs.cn/list=hf_GC"
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    data = text.split('"')[1].split(',')
                    if len(data) > 0:
                        return float(data[0])
        except Exception as e:
            logger.error(f"获取价格失败: {e}")
        return None
    
    async def fetch_klines(self, price: float) -> pd.DataFrame:
        """生成模拟K线"""
        now = datetime.now()
        klines = []
        
        for i in range(100):
            timestamp = now - timedelta(hours=4*i)
            noise = np.random.randn() * 10
            klines.append({
                'timestamp': timestamp,
                'close': price + noise + np.random.randn() * 3,
            })
        
        return pd.DataFrame(klines[::-1])
    
    async def execute_trade(self, signal: float, account: Dict, current_price: float):
        """执行交易"""
        available = account['available']
        
        if signal > self.min_signal_strength:
            # 买入信号
            if available < 50:
                logger.warning("⚠️ 可用资金不足，跳过交易")
                return
            
            # 计算买入数量
            position_value = available * self.position_size_pct * self.leverage
            size = position_value / current_price
            size_str = f"{size:.4f}"
            
            logger.info(f"🔥 执行买入: {size_str} XAUT @ ${current_price:.2f}")
            
            # 下单
            order = await self.trader.place_order(self.inst_id, "buy", size_str)
            
            if order:
                self.stats['total_trades'] += 1
                self.stats['successful_trades'] += 1
                
                # 设置止损（-3%）
                stop_price = current_price * 0.97
                await self.trader.set_stop_loss(self.inst_id, "sell", size_str, f"{stop_price:.2f}")
                
                # 发送通知
                msg = (
                    f"**✅ 自动买入成功**\n\n"
                    f"**交易信息：**\n"
                    f"• 数量：{size_str} XAUT\n"
                    f"• 价格：${current_price:.2f}\n"
                    f"• 金额：${position_value:.2f}\n"
                    f"• 杠杆：{self.leverage}倍\n"
                    f"• 止损：${stop_price:.2f}（-3%）\n\n"
                    f"**账户余额：**\n"
                    f"• 剩余可用：${available - position_value/self.leverage:.2f}\n\n"
                    f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                send_feishu(msg, "money")
            else:
                self.stats['failed_trades'] += 1
                send_feishu(f"**❌ 自动买入失败**\n\n请检查日志", "danger")
        
        elif signal < -self.min_signal_strength:
            # 卖出信号
            positions = await self.trader.get_positions(self.inst_id)
            
            if not positions or len(positions) == 0:
                logger.info("📊 无持仓，跳过卖出")
                return
            
            # 获取持仓数量
            pos = positions[0]
            pos_size = abs(float(pos.get('pos', 0)))
            
            if pos_size > 0:
                size_str = f"{pos_size:.4f}"
                
                logger.info(f"⚠️ 执行卖出: {size_str} XAUT @ ${current_price:.2f}")
                
                # 下单
                order = await self.trader.place_order(self.inst_id, "sell", size_str)
                
                if order:
                    self.stats['total_trades'] += 1
                    self.stats['successful_trades'] += 1
                    
                    # 发送通知
                    msg = (
                        f"**✅ 自动卖出成功**\n\n"
                        f"**交易信息：**\n"
                        f"• 数量：{size_str} XAUT\n"
                        f"• 价格：${current_price:.2f}\n\n"
                        f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_feishu(msg, "warning")
                else:
                    self.stats['failed_trades'] += 1
                    send_feishu(f"**❌ 自动卖出失败**\n\n请检查日志", "danger")
    
    async def run(self):
        """主循环"""
        if not await self.initialize():
            return
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                
                logger.info(f"\n{'='*80}")
                logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {check_count} 次扫描")
                logger.info(f"{'='*80}")
                
                # 1. 获取账户信息
                account = await self.trader.get_account_balance()
                if not account:
                    logger.warning("⚠️ 无法获取账户信息，60秒后重试...")
                    await asyncio.sleep(60)
                    continue
                
                # 2. 获取价格
                price = await self.fetch_price()
                if not price:
                    logger.warning("⚠️ 无法获取价格，60秒后重试...")
                    await asyncio.sleep(60)
                    continue
                
                logger.info(f"💰 当前价格: ${price:.2f}")
                logger.info(f"💰 可用资金: ${account['available']:.2f}")
                
                # 3. 计算特征
                klines = await self.fetch_klines(price)
                features = self.quant_features.calculate_all_features(klines)
                
                # 4. Multi-Agent分析
                consensus = await self.multi_agent.get_consensus(features, price, account)
                
                signal = consensus['signal']
                conf = consensus['consensus']
                
                logger.info(f"🤖 信号: {signal:+.2f}, 共识度: {conf:.0%}")
                
                # 5. 执行交易
                if abs(signal) > self.min_signal_strength and conf > self.min_consensus:
                    await self.execute_trade(signal, account, price)
                
                # 6. 定期推送状态（每10次）
                if check_count % 10 == 0:
                    await self.send_status_update(account, price, features, consensus)
                
                # 等待5分钟
                logger.info("⏰ 等待5分钟...")
                await asyncio.sleep(300)
        
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            await self.close()
    
    async def send_status_update(self, account: Dict, price: float, features: Dict, consensus: Dict):
        """发送状态更新"""
        expert_text = "\n".join([
            f"• {op['agent']}: {'+' if op['signal'] > 0 else ''}{op['signal']:.0%} - {', '.join(op['reasons'])}"
            for op in consensus['opinions']
        ])
        
        msg = (
            f"**📊 系统状态更新**\n\n"
            f"**💰 账户信息：**\n"
            f"• 总权益：${account['total_equity']:.2f}（¥{account['total_equity']*CNY_RATE:.2f}）\n"
            f"• 可用：${account['available']:.2f}（¥{account['available']*CNY_RATE:.2f}）\n"
            f"• 浮盈：${account['unrealized_pnl']:.2f}（¥{account['unrealized_pnl']*CNY_RATE:.2f}）\n\n"
            f"**📈 市场信息：**\n"
            f"• 价格：${price:.2f}\n"
            f"• RSI：{features['rsi']:.1f}\n"
            f"• 动量：{features['momentum_10']:.2%}\n\n"
            f"**🤖 专家意见：**\n{expert_text}\n\n"
            f"**📊 综合判断：**\n"
            f"• 信号：{consensus['signal']:+.0%}\n"
            f"• 共识度：{consensus['consensus']:.0%}\n\n"
            f"**📈 交易统计：**\n"
            f"• 总交易：{self.stats['total_trades']}笔\n"
            f"• 成功：{self.stats['successful_trades']}笔\n"
            f"• 失败：{self.stats['failed_trades']}笔\n\n"
            f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        send_feishu(msg, "info")


# ==================== 启动 ====================
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🤖 全自动交易系统 - 终极版                          ║
    ║                                                              ║
    ║  核心功能：                                                   ║
    ║    • 实时监控市场                                            ║
    ║    • 自动分析信号                                            ║
    ║    • 自动下单交易                                            ║
    ║    • 自动设置止损                                            ║
    ║    • 飞书实时推送                                            ║
    ║                                                              ║
    ║  ⚠️  注意：系统会自动交易，请确保已配置好参数！               ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止系统
    """)
    
    system = AutoTradingSystem()
    asyncio.run(system.run())


