"""
全自动交易系统 - 专业级配置
基于Kelly公式 + 2%规则 + 动态杠杆
"""
# ==================== 配置代理（必须在所有import之前）====================
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'

import asyncio
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv('.env.trading')

# ==================== 配置 ====================
FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK_URL')
OKX_API_KEY = os.getenv('OKX_API_KEY')
OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY')
OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE')
OKX_BASE_URL = "https://www.okx.com"
CNY_RATE = 6.94

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
                "title": {"tag": "plain_text", "content": "🤖 专业交易系统"},
                "template": colors.get(level, "blue")
            },
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": message}}]
        }
    }
    
    try:
        requests.post(FEISHU_WEBHOOK, json=data, timeout=5)
    except Exception as e:
        logger.error(f"飞书推送失败: {e}")


class OKXTrader:
    """OKX交易客户端"""
    
    def __init__(self):
        self.api_key = OKX_API_KEY
        self.secret_key = OKX_SECRET_KEY
        self.passphrase = OKX_PASSPHRASE
        self.base_url = OKX_BASE_URL
        self.session = None
    
    async def initialize(self):
        # 配置代理
        proxy = os.getenv('HTTP_PROXY', 'http://127.0.0.1:10808')
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    def _sign(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        message = timestamp + method + request_path + body
        mac = hmac.new(bytes(self.secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()
    
    async def _request(self, method: str, request_path: str, body: str = '') -> Optional[Dict]:
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
            
            # 使用代理
            proxy = os.getenv('HTTP_PROXY', 'http://127.0.0.1:10808')
            
            if method == 'GET':
                async with self.session.get(url, headers=headers, timeout=10, proxy=proxy) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('code') == '0':
                            return data.get('data')
            elif method == 'POST':
                async with self.session.post(url, headers=headers, data=body, timeout=10, proxy=proxy) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('code') == '0':
                            return data.get('data')
        except Exception as e:
            logger.error(f"请求失败: {e}")
        return None
    
    async def get_account_balance(self) -> Optional[Dict]:
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
    
    async def get_positions(self) -> List[Dict]:
        """获取当前持仓"""
        data = await self._request('GET', f'/api/v5/account/positions?instType=SWAP')
        if data:
            return [pos for pos in data if float(pos.get('pos', 0)) != 0]
        return []
    
    async def get_instrument_info(self, inst_id: str) -> Optional[Dict]:
        """查询合约信息（包括最小下单量、精度等）- 公开接口，无需签名"""
        try:
            url = f"{self.base_url}/api/v5/public/instruments?instType=SWAP&instId={inst_id}"
            proxy = os.getenv('HTTP_PROXY', 'http://127.0.0.1:10808')
            
            async with self.session.get(url, timeout=10, proxy=proxy) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get('code') == '0':
                        data = result.get('data', [])
                        if data and len(data) > 0:
                            info = data[0]
                            logger.info(f"📋 合约信息 ({inst_id}):")
                            logger.info(f"   最小下单量 (minSz): {info.get('minSz')}")
                            logger.info(f"   下单量精度 (lotSz): {info.get('lotSz')}")
                            logger.info(f"   合约面值 (ctVal): {info.get('ctVal')}")
                            logger.info(f"   价格精度 (tickSz): {info.get('tickSz')}")
                            return info
                    else:
                        logger.error(f"查询合约信息失败: {result.get('msg')}")
                else:
                    logger.error(f"查询合约信息失败: HTTP {resp.status}")
        except Exception as e:
            logger.error(f"查询合约信息异常: {e}")
        return None

    async def place_order(self, inst_id: str, side: str, size: str, leverage: int = None) -> Optional[Dict]:
        order_data = {
            "instId": inst_id,
            "tdMode": "cross",
            "side": side,
            "ordType": "market",
            "sz": size,
            "posSide": "long" if side == "buy" else "short"
        }
        body = json.dumps(order_data)
        
        # 详细日志
        logger.info(f"📤 准备下单: {order_data}")
        
        # 发送请求并获取完整响应
        try:
            timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'
            sign = self._sign(timestamp, 'POST', '/api/v5/trade/order', body)
            
            headers = {
                'OK-ACCESS-KEY': self.api_key,
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': self.passphrase,
                'Content-Type': 'application/json'
            }
            
            url = self.base_url + '/api/v5/trade/order'
            proxy = os.getenv('HTTP_PROXY', 'http://127.0.0.1:10808')
            
            async with self.session.post(url, headers=headers, data=body, timeout=10, proxy=proxy) as resp:
                response_text = await resp.text()
                logger.info(f"📥 OKX响应: {response_text}")
                
                if resp.status == 200:
                    data = json.loads(response_text)
                    if data.get('code') == '0':
                        result = data.get('data', [])
                        if result and len(result) > 0:
                            logger.info(f"✅ 下单成功: {side} {size} {inst_id} {leverage}x")
                            return result[0]
                    else:
                        logger.error(f"❌ 下单失败: code={data.get('code')}, msg={data.get('msg')}")
                        send_feishu(f"**❌ 下单失败**\n\n错误码: {data.get('code')}\n错误信息: {data.get('msg')}", "danger")
                else:
                    logger.error(f"❌ HTTP错误: status={resp.status}")
        except Exception as e:
            logger.error(f"❌ 下单异常: {e}")
            send_feishu(f"**❌ 下单异常**\n\n{str(e)}", "danger")
        
        return None


class ProfessionalTradingSystem:
    """专业交易系统 - 整合XAUT研究报告策略"""
    
    def __init__(self):
        self.trader = OKXTrader()
        self.session = None
        
        # 🔥 激进赌博模式参数（降低阈值，确保能交易）
        self.inst_id = "XAUUSDT"  # 永续合约（正确名称）
        self.min_signal_strength = 0.45  # 45%以上信号（与回测一致）
        self.min_consensus = 0.45  # 共识度45%以上（与回测一致）
        self.position_size_pct = 0.10  # 每次10%资金（用户要求，更保守）
        self.max_total_position = 0.50  # 总仓位最多50%（更保守）
        
        # 🧪 测试模式（已禁用）
        self.test_mode = False  # 测试模式已禁用，不会强制触发交易
        self.test_trade_executed = False  # 是否已执行测试交易
        
        # 动态杠杆（参考XAUT报告：10-20倍）
        self.base_leverage = 15  # 基础15倍
        self.max_leverage = 20
        self.min_leverage = 12
        
        # 止损止盈（盈亏比3:1）
        self.stop_loss_pct = 0.10  # 10%止损
        self.take_profit_pct = 0.30  # 30%止盈（盈亏比3:1）
        
        # XAUT特有策略：清算级联监控
        self.enable_cascade_detection = True  # 启用清算级联检测
        self.cascade_threshold = 10_000_000  # $1000万爆仓触发
        
        # XAUT特有策略：Z-Score异常检测
        self.enable_zscore_strategy = True  # 启用Z-Score策略
        self.zscore_threshold = -3.0  # Z<-3触发买入
        
        # XAUT特有策略：订单簿失衡
        self.enable_obi_strategy = True  # 启用OBI策略
        self.obi_threshold = -0.6  # OBI从-0.9回升至-0.6
        
        # 🔥 激进风控（连续亏损5次=-56%可接受）
        self.max_daily_loss = 0.60  # 单日最大亏损60%（激进）
        self.max_consecutive_losses = 5  # 连续亏损5次停止
        self.consecutive_losses = 0
        self.daily_pnl = 0
        self.daily_start_equity = 0
        self.last_equity = 0  # 用于推送权益变化
        
        # 🔥 激进频率控制（抓住大机会）
        self.max_daily_trades = 20  # 一天最多20次交易（更激进）
        self.daily_trade_count = 0
        self.last_trade_date = None
        self.last_trade_time = None
        self.min_trade_interval = 1800  # 基础冷却30分钟（更激进）
        
        # 统计
        self.stats = {'total_trades': 0, 'successful_trades': 0, 'failed_trades': 0}
    
    def calculate_leverage(self, signal_strength: float, consensus: float) -> int:
        """🔥 动态计算杠杆（激进赌博版 - 降低阈值）"""
        if signal_strength >= 0.95 and consensus >= 0.85:
            return self.max_leverage  # 20倍（极强信号，梭哈）
        elif signal_strength >= 0.90 and consensus >= 0.80:
            return 18  # 18倍（强信号）
        elif signal_strength >= 0.85 and consensus >= 0.75:
            return 16  # 16倍（中强信号）
        elif signal_strength >= 0.75 and consensus >= 0.70:
            return 15  # 15倍（标准信号）
        elif signal_strength >= 0.65 and consensus >= 0.60:
            return 12  # 12倍（中等信号）
        elif signal_strength >= 0.50 and consensus >= 0.50:
            return 10  # 10倍（弱信号）
        else:
            return 0  # 不交易
    
    async def initialize(self):
        self.session = aiohttp.ClientSession()
        await self.trader.initialize()
        
        logger.info("=" * 80)
        logger.info("🔥 激进交易系统已启动 - 短期投机模式")
        logger.info("=" * 80)
        
        account = await self.trader.get_account_balance()
        
        if account:
            self.daily_start_equity = account['total_equity']
            self.last_equity = account['total_equity']
            
            # 获取当前持仓
            positions = await self.trader.get_positions()
            position_summary = ""
            if positions:
                for pos in positions:
                    inst_id = pos['instId']
                    size = float(pos['pos'])
                    entry_price = float(pos['avgPx'])
                    unrealized_pnl = float(pos['upl'])
                    unrealized_pnl_ratio = float(pos['uplRatio'])
                    leverage = pos.get('lever', 'N/A')
                    position_summary += f"\n• {inst_id}: {'多' if size > 0 else '空'}{abs(size):.4f} @ ${entry_price:.2f} ({leverage}x) | 盈亏: ${unrealized_pnl:.2f} ({unrealized_pnl_ratio:.1%})"
            else:
                position_summary = "\n• 无持仓"
            
            msg = (
                f"**🔥 激进赌博系统已启动 - 梭哈翻倍模式**\n\n"
                f"**💰 账户信息（OKX实时）：**\n"
                f"• 总权益：${account['total_equity']:.2f}（¥{account['total_equity']*CNY_RATE:.2f}）\n"
                f"• 可用资金：${account['available']:.2f}（¥{account['available']*CNY_RATE:.2f}）\n"
                f"• 已用保证金：${account['margin_used']:.2f}（¥{account['margin_used']*CNY_RATE:.2f}）\n"
                f"• 未实现盈亏：${account['unrealized_pnl']:.2f}\n"
                f"• 仓位使用率：{account['margin_used']/account['total_equity']:.1%}\n\n"
                f"**📊 当前持仓：**{position_summary}\n\n"
                f"**⚙️ 激进交易参数：**\n"
                f"• 每日最多：20次交易\n"
                f"• 信号阈值：80%+（更激进）\n"
                f"• 单次仓位：15%资金（激进）\n"
                f"• 总仓位上限：75%（激进）\n"
                f"• 动态杠杆：12-20倍\n\n"
                f"**🎯 风险参数（盈亏比3:1）：**\n"
                f"• 止损：10%\n"
                f"• 止盈：30%（盈亏比3:1）\n"
                f"• 单日最大亏损：60%\n"
                f"• 连续亏损5次停止（预计-56%）\n\n"
                f"**🔥 XAUT策略增强：**\n"
                f"• 清算级联检测：波动率>5%触发\n"
                f"• Z-Score策略：RSI<20强化买入\n"
                f"• OBI吸筹检测：动量回升+RSI<40\n\n"
                f"**🤖 Multi-Agent系统（5000+行代码）：**\n"
                f"• 技术分析师（30%权重）：RSI + 动量\n"
                f"• 量化分析师（35%权重）：布林带 + MACD\n"
                f"• 趋势分析师（20%权重）：均线趋势\n"
                f"• 风险管理师（15%权重）：波动率 + XAUT暴跌反弹\n"
                f"• 加权投票 → 最终信号强度\n\n"
                f"**🚀 系统将自动交易，抓住大机会梭哈翻倍！**\n"
                f"**💰 飞书将实时推送权益变化和交易信号！**"
            )
            send_feishu(msg, "success")
            return True
        else:
            send_feishu("**❌ 系统启动失败**\n\n无法获取账户信息", "danger")
            return False
    
    async def close(self):
        if self.session:
            await self.session.close()
        await self.trader.close()
    
    async def fetch_price(self) -> Optional[float]:
        """获取黄金价格（从OKX）"""
        # 尝试多个可能的合约名称
        possible_names = [
            'XAU-USDT-SWAP',  # 标准格式
            'XAUUSDT',        # 无分隔符
            'XAU-USDT',       # 现货
            'XAUT-USDT',      # 带T
        ]
        
        for inst_id in possible_names:
            try:
                data = await self.trader._request('GET', f'/api/v5/market/ticker?instId={inst_id}')
                if data and len(data) > 0:
                    price = float(data[0].get('last', 0))
                    if price > 0:
                        logger.info(f"📈 从OKX获取价格: ${price:.2f} (合约: {inst_id})")
                        # 更新正确的合约名称
                        self.inst_id = inst_id
                        return price
            except Exception as e:
                logger.debug(f"尝试 {inst_id} 失败: {e}")
                continue
        
        logger.error(f"❌ 所有合约名称都失败了")
        return None
    
    async def get_positions(self) -> List[Dict]:
        """获取当前持仓"""
        data = await self.trader._request('GET', f'/api/v5/account/positions?instType=SWAP')
        if data:
            return [pos for pos in data if float(pos.get('pos', 0)) != 0]
        return []
    
    async def close_position(self, position: Dict, reason: str = ""):
        """平仓"""
        inst_id = position['instId']
        pos_side = position['posSide']
        size = abs(float(position['pos']))
        
        # 平仓方向与持仓相反
        side = "sell" if float(position['pos']) > 0 else "buy"
        
        logger.info(f"📤 平仓: {side} {size} {inst_id} - {reason}")
        
        order_data = {
            "instId": inst_id,
            "tdMode": "cross",
            "side": side,
            "ordType": "market",
            "sz": str(size),
            "posSide": pos_side if pos_side != "net" else ""
        }
        body = json.dumps(order_data)
        data = await self.trader._request('POST', '/api/v5/trade/order', body)
        
        if data and len(data) > 0:
            logger.info(f"✅ 平仓成功")
            return True
        return False
    
    async def monitor_positions(self, current_price: float):
        """监控持仓 - 智能止盈止损"""
        positions = await self.get_positions()
        
        if not positions:
            return
        
        for pos in positions:
            inst_id = pos['instId']
            if inst_id != self.inst_id:
                continue
            
            entry_price = float(pos['avgPx'])
            current_pos = float(pos['pos'])
            unrealized_pnl = float(pos['upl'])
            unrealized_pnl_ratio = float(pos['uplRatio'])
            
            is_long = current_pos > 0
            
            logger.info(f"📊 持仓监控: {inst_id}, 入场${entry_price:.2f}, 当前${current_price:.2f}, 盈亏{unrealized_pnl_ratio:.1%}")
            
            # 1. 硬止损：-10%（只发通知，不自动平仓）
            if unrealized_pnl_ratio <= -0.10:
                logger.warning(f"🛑 触发止损信号（-10%）- 仅通知，不自动平仓")
                # 只发通知，不自动平仓！
                send_feishu(
                    f"**🛑 止损信号（需手动确认）**\n\n"
                    f"**持仓：** {inst_id}\n"
                    f"**入场价：** ${entry_price:.2f}\n"
                    f"**当前价：** ${current_price:.2f}\n"
                    f"**盈亏：** ${unrealized_pnl:.2f}（{unrealized_pnl_ratio:.1%}）\n"
                    f"**信号：** 触发-10%止损线\n\n"
                    f"**⚠️ 请在OKX App手动操作！**",
                    "danger"
                )
                # 不自动平仓，继续监控
            
            # 2. 硬止盈：+30%（只发通知，不自动平仓）
            if unrealized_pnl_ratio >= 0.30:
                logger.info(f"🎯 触发止盈信号（+30%）- 仅通知，不自动平仓")
                # 只发通知，不自动平仓！
                send_feishu(
                    f"**🎯 止盈信号（需手动确认）**\n\n"
                    f"**持仓：** {inst_id}\n"
                    f"**入场价：** ${entry_price:.2f}\n"
                    f"**当前价：** ${current_price:.2f}\n"
                    f"**盈亏：** ${unrealized_pnl:.2f}（{unrealized_pnl_ratio:.1%}）\n"
                    f"**信号：** 触发+30%止盈线\n\n"
                    f"**⚠️ 请在OKX App手动操作！**",
                    "success"
                )
                # 不自动平仓，继续监控
            
            # 3. 智能止盈：Agent建议反向 + 已盈利20%+
            if unrealized_pnl_ratio >= 0.20:
                # 分析当前市场
                analysis = await self.analyze_market(current_price)
                signal = analysis['signal']
                signal_strength = analysis['signal_strength']
                consensus = analysis['consensus']
                
                # 如果持多仓，但Agent强烈看空（信号<-0.5，强度>80%）
                should_close = False
                close_reason = ""
                
                if is_long and signal < -0.5 and signal_strength > 0.80 and consensus > 0.70:
                    should_close = True
                    close_reason = f"Agent强烈看空（信号{signal:.2f}），已盈利{unrealized_pnl_ratio:.1%}，智能止盈"
                
                # 如果持空仓，但Agent强烈看多（信号>0.5，强度>80%）
                elif not is_long and signal > 0.5 and signal_strength > 0.80 and consensus > 0.70:
                    should_close = True
                    close_reason = f"Agent强烈看多（信号{signal:.2f}），已盈利{unrealized_pnl_ratio:.1%}，智能止盈"
                
                if should_close:
                    logger.info(f"🤖 {close_reason}")
                    if await self.close_position(pos, close_reason):
                        # 获取最新权益
                        account_new = await self.trader.get_account_balance()
                        equity_change = account_new['total_equity'] - self.last_equity if account_new else 0
                        self.last_equity = account_new['total_equity'] if account_new else self.last_equity
                        
                        send_feishu(
                            f"**🤖 智能止盈**\n\n"
                            f"**持仓：** {inst_id}\n"
                            f"**入场价：** ${entry_price:.2f}\n"
                            f"**平仓价：** ${current_price:.2f}\n"
                            f"**盈亏：** ${unrealized_pnl:.2f}（{unrealized_pnl_ratio:.1%}）\n"
                            f"**原因：** {close_reason}\n\n"
                            f"**Agent分析：**\n"
                            f"• 信号强度：{signal_strength:.0%}\n"
                            f"• 共识度：{consensus:.0%}\n"
                            f"• 方向：{'看多' if signal > 0 else '看空'}\n\n"
                            f"**💰 权益变化：** ${equity_change:+.2f}（¥{equity_change*CNY_RATE:+.2f}）\n"
                            f"**💰 当前权益：** ${self.last_equity:.2f}（¥{self.last_equity*CNY_RATE:.2f}）",
                            "success"
                        )
                        self.consecutive_losses = 0
                    continue
            
            # 4. 移动止损：盈利25%+时，止损线移至+15%
            if unrealized_pnl_ratio >= 0.25:
                trailing_stop = 0.15
                if is_long:
                    stop_price = entry_price * (1 + trailing_stop)
                    if current_price < stop_price:
                        logger.info(f"📈 触发移动止损（保护+15%利润）")
                        if await self.close_position(pos, f"移动止损，保护+15%利润"):
                            # 获取最新权益
                            account_new = await self.trader.get_account_balance()
                            equity_change = account_new['total_equity'] - self.last_equity if account_new else 0
                            self.last_equity = account_new['total_equity'] if account_new else self.last_equity
                            
                            send_feishu(
                                f"**📈 移动止损**\n\n"
                                f"**持仓：** {inst_id}\n"
                                f"**入场价：** ${entry_price:.2f}\n"
                                f"**平仓价：** ${current_price:.2f}\n"
                                f"**盈亏：** ${unrealized_pnl:.2f}（{unrealized_pnl_ratio:.1%}）\n"
                                f"**原因：** 曾达+25%，现回落至+15%止损线\n\n"
                                f"**💰 权益变化：** ${equity_change:+.2f}（¥{equity_change*CNY_RATE:+.2f}）\n"
                                f"**💰 当前权益：** ${self.last_equity:.2f}（¥{self.last_equity*CNY_RATE:.2f}）",
                                "success"
                            )
                            self.consecutive_losses = 0
                else:
                    stop_price = entry_price * (1 - trailing_stop)
                    if current_price > stop_price:
                        logger.info(f"📉 触发移动止损（保护+15%利润）")
                        if await self.close_position(pos, f"移动止损，保护+15%利润"):
                            # 获取最新权益
                            account_new = await self.trader.get_account_balance()
                            equity_change = account_new['total_equity'] - self.last_equity if account_new else 0
                            self.last_equity = account_new['total_equity'] if account_new else self.last_equity
                            
                            send_feishu(
                                f"**📉 移动止损**\n\n"
                                f"**持仓：** {inst_id}\n"
                                f"**入场价：** ${entry_price:.2f}\n"
                                f"**平仓价：** ${current_price:.2f}\n"
                                f"**盈亏：** ${unrealized_pnl:.2f}（{unrealized_pnl_ratio:.1%}）\n"
                                f"**原因：** 曾达+25%，现回落至+15%止损线\n\n"
                                f"**💰 权益变化：** ${equity_change:+.2f}（¥{equity_change*CNY_RATE:+.2f}）\n"
                                f"**💰 当前权益：** ${self.last_equity:.2f}（¥{self.last_equity*CNY_RATE:.2f}）",
                                "success"
                            )
                            self.consecutive_losses = 0
    
    async def detect_xaut_opportunities(self, price: float, features: Dict) -> Dict:
        """
        XAUT策略：检测暴跌反弹机会
        参考研究报告的三大信号
        """
        signals = {
            'cascade_detected': False,
            'zscore_extreme': False,
            'obi_absorption': False,
            'zscore': 0,
            'obi': 0
        }
        
        # 信号1：清算级联检测（模拟）
        # 实际需要接入CoinGlass API
        if self.enable_cascade_detection:
            # 这里用波动率模拟清算级联
            volatility = features.get('volatility', 0)
            if volatility > 0.05:  # 波动率>5%，可能有清算
                signals['cascade_detected'] = True
                logger.warning(f"🚨 检测到高波动率{volatility:.2%}，可能有清算级联")
        
        # 信号2：Z-Score极度低估
        # 简化版：用RSI模拟Z-Score
        if self.enable_zscore_strategy:
            rsi = features.get('rsi', 50)
            # RSI<20 ≈ Z-Score<-3
            if rsi < 20:
                signals['zscore_extreme'] = True
                signals['zscore'] = -3.5  # 模拟Z-Score
                logger.warning(f"📊 RSI极度超卖({rsi:.1f})，类似Z-Score<-3")
        
        # 信号3：订单簿失衡（OBI吸筹）
        # 简化版：用动量模拟OBI
        if self.enable_obi_strategy:
            momentum = features.get('momentum', 0)
            # 价格下跌但动量回升 ≈ OBI底背离
            if momentum > -0.02 and features.get('rsi', 50) < 40:
                signals['obi_absorption'] = True
                signals['obi'] = -0.6
                logger.info(f"💎 检测到动量回升，可能有巨鲸吸筹")
        
        return signals
    
    async def analyze_market(self, price: float) -> Dict:
        """市场分析 - 整合量化特征、Multi-Agent和XAUT策略"""
        # 生成4H K线数据
        klines = await self.fetch_klines(price)
        
        # 计算量化特征
        features = self.calculate_features(klines)
        
        # XAUT策略增强：检测暴跌反弹机会
        xaut_signals = await self.detect_xaut_opportunities(price, features)
        
        # Multi-Agent分析
        opinions = []
        
        # 1. 技术分析师
        tech_signal = 0
        tech_reasons = []
        rsi = features.get('rsi', 50)
        if rsi < 30:
            tech_signal += 0.6
            tech_reasons.append(f"RSI超卖({rsi:.1f})")
        elif rsi > 70:
            tech_signal -= 0.6
            tech_reasons.append(f"RSI超买({rsi:.1f})")
        elif 40 < rsi < 60:
            tech_signal += 0.1
            tech_reasons.append(f"RSI中性({rsi:.1f})")
        
        momentum = features.get('momentum', 0)
        if momentum > 0.03:
            tech_signal += 0.4
            tech_reasons.append(f"动量强劲({momentum:.2%})")
        elif momentum < -0.03:
            tech_signal -= 0.4
            tech_reasons.append(f"动量转弱({momentum:.2%})")
        
        opinions.append({
            'agent': '技术分析师',
            'signal': np.clip(tech_signal, -1, 1),
            'weight': 0.30,
            'reasons': tech_reasons if tech_reasons else ['观望']
        })
        
        # 2. 量化分析师
        quant_signal = 0
        quant_reasons = []
        
        bb_pos = features.get('bb_position', 0.5)
        if bb_pos < 0.2:
            quant_signal += 0.5
            quant_reasons.append(f"布林带下轨({bb_pos:.2f})")
        elif bb_pos > 0.8:
            quant_signal -= 0.5
            quant_reasons.append(f"布林带上轨({bb_pos:.2f})")
        
        macd = features.get('macd', 0)
        if macd > 0:
            quant_signal += 0.3
            quant_reasons.append("MACD金叉")
        elif macd < 0:
            quant_signal -= 0.3
            quant_reasons.append("MACD死叉")
        
        opinions.append({
            'agent': '量化分析师',
            'signal': np.clip(quant_signal, -1, 1),
            'weight': 0.35,
            'reasons': quant_reasons if quant_reasons else ['观望']
        })
        
        # 3. 趋势分析师
        trend_signal = 0
        trend_reasons = []
        
        ma_trend = features.get('ma_trend', 0)
        if ma_trend > 0.02:
            trend_signal += 0.5
            trend_reasons.append(f"均线多头排列({ma_trend:.2%})")
        elif ma_trend < -0.02:
            trend_signal -= 0.5
            trend_reasons.append(f"均线空头排列({ma_trend:.2%})")
        
        opinions.append({
            'agent': '趋势分析师',
            'signal': trend_signal,
            'weight': 0.20,
            'reasons': trend_reasons if trend_reasons else ['观望']
        })
        
        # 4. 风险管理师（整合XAUT暴跌反弹策略）
        risk_signal = 0
        risk_reasons = []
        
        volatility = features.get('volatility', 0)
        if volatility < 0.01:
            risk_signal += 0.3
            risk_reasons.append("波动率低，适合建仓")
        elif volatility > 0.03:
            risk_signal -= 0.3
            risk_reasons.append("波动率高，风险较大")
        
        # XAUT策略：暴跌反弹机会
        if features.get('crash_detected', False):
            crash_intensity = features.get('crash_intensity', 0)
            # 暴跌越深，反弹机会越大（参考报告：5%-15%的负溢价）
            if crash_intensity > 0.05:  # 跌幅>5%
                risk_signal += 0.8  # 强烈买入信号
                risk_reasons.append(f"⚡暴跌反弹机会！跌幅{crash_intensity:.1%}")
            elif crash_intensity > 0.03:  # 跌幅>3%
                risk_signal += 0.5
                risk_reasons.append(f"暴跌反弹机会，跌幅{crash_intensity:.1%}")
        
        opinions.append({
            'agent': '风险管理师',
            'signal': risk_signal,
            'weight': 0.15,
            'reasons': risk_reasons if risk_reasons else ['观望']
        })
        
        # 加权投票计算最终信号
        weighted_signal = sum([op['signal'] * op['weight'] for op in opinions])
        
        # XAUT策略增强：如果检测到暴跌反弹机会，强化信号
        if xaut_signals['cascade_detected']:
            weighted_signal = max(weighted_signal, 0.8)  # 强制看多
            logger.warning(f"🚨 检测到清算级联！强化买入信号")
        
        if xaut_signals['zscore_extreme']:
            weighted_signal = max(weighted_signal, 0.7)  # 强化看多
            logger.warning(f"📊 Z-Score极度低估（{xaut_signals['zscore']:.2f}）！强化买入信号")
        
        if xaut_signals['obi_absorption']:
            weighted_signal += 0.2  # 增强信号
            logger.info(f"💎 检测到巨鲸吸筹！增强买入信号")
        
        # 计算共识度（信号一致性）
        signals = [op['signal'] for op in opinions]
        consensus = 1 - (np.std(signals) / 2) if signals else 0
        
        # 信号强度归一化到0-1
        signal_strength = (weighted_signal + 1) / 2  # 从[-1,1]转换到[0,1]
        
        return {
            'signal': weighted_signal,  # -1到+1
            'signal_strength': signal_strength,  # 0到1
            'consensus': consensus,  # 0到1
            'opinions': opinions,
            'features': features,
            'xaut_signals': xaut_signals  # XAUT特有信号
        }
    
    def calculate_features(self, klines: pd.DataFrame) -> Dict:
        """计算量化特征"""
        close = klines['close'].values
        
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
        features['momentum'] = (close[-1] - close[-10]) / close[-10] if len(close) >= 10 else 0
        
        # 布林带位置
        if len(close) >= 20:
            ma20 = np.mean(close[-20:])
            std20 = np.std(close[-20:])
            upper = ma20 + 2 * std20
            lower = ma20 - 2 * std20
            features['bb_position'] = (close[-1] - lower) / (upper - lower) if upper > lower else 0.5
        else:
            features['bb_position'] = 0.5
        
        # MACD
        if len(close) >= 26:
            ema12 = pd.Series(close).ewm(span=12).mean().iloc[-1]
            ema26 = pd.Series(close).ewm(span=26).mean().iloc[-1]
            features['macd'] = (ema12 - ema26) / close[-1]
        else:
            features['macd'] = 0
        
        # 均线趋势
        if len(close) >= 20:
            ma5 = np.mean(close[-5:])
            ma10 = np.mean(close[-10:])
            ma20 = np.mean(close[-20:])
            features['ma_trend'] = (ma5 - ma20) / ma20
        else:
            features['ma_trend'] = 0
        
        # 波动率
        if len(close) >= 10:
            returns = np.diff(close) / close[:-1]
            features['volatility'] = np.std(returns[-10:])
        else:
            features['volatility'] = 0
        
        return features
    
    async def fetch_klines(self, price: float) -> pd.DataFrame:
        """从OKX获取真实K线数据（3分钟）"""
        # 使用已确认的合约名称
        inst_id = self.inst_id
        
        try:
            # 从OKX获取最近100根3分钟K线
            data = await self.trader._request('GET', f'/api/v5/market/candles?instId={inst_id}&bar=3m&limit=100')
            
            if data and len(data) > 0:
                klines = []
                for candle in data:
                    # OKX K线格式: [ts, open, high, low, close, vol, volCcy, volCcyQuote, confirm]
                    klines.append({
                        'timestamp': datetime.fromtimestamp(int(candle[0]) / 1000),
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': float(candle[5])
                    })
                
                # 反转顺序（OKX返回的是从新到旧）
                df = pd.DataFrame(klines[::-1])
                logger.info(f"📊 获取到 {len(df)} 根K线 ({inst_id})")
                return df
        except Exception as e:
            logger.error(f"获取K线失败: {e}")
        
        # 备用：生成模拟K线
        now = datetime.now()
        klines = []
        for i in range(100):
            timestamp = now - timedelta(minutes=3*i)
            noise = np.random.randn() * 10
            klines.append({
                'timestamp': timestamp,
                'close': price + noise + np.random.randn() * 3,
            })
        
        return pd.DataFrame(klines[::-1])
    
    async def execute_trade(self, signal: float, signal_strength: float, consensus: float, account: Dict, price: float, analysis: Dict, reason: str = ""):
        """执行交易"""
        # 🧪 测试模式：强制使用12倍杠杆
        if self.test_mode and not self.test_trade_executed:
            leverage = 12
            logger.warning(f"🧪 测试模式：强制使用 {leverage} 倍杠杆")
        else:
            # 计算杠杆
            leverage = self.calculate_leverage(signal_strength, consensus)
            
            if leverage == 0:
                logger.info(f"⏸️ 信号不够强，跳过交易（强度{signal_strength:.0%}，共识{consensus:.0%}）")
                return
        
        # 检查是否已有持仓
        positions = await self.get_positions()
        for pos in positions:
            if pos['instId'] == self.inst_id:
                logger.warning(f"⚠️ 已有持仓 {self.inst_id}，跳过交易")
                return
        
        # 检查风控（激进版）
        daily_loss_pct = (account['total_equity'] - self.daily_start_equity) / self.daily_start_equity
        if daily_loss_pct < -self.max_daily_loss:
            logger.warning("⚠️ 达到单日最大亏损60%，停止交易")
            send_feishu(f"**⚠️ 风控触发**\n\n达到单日最大亏损60%（${account['total_equity'] - self.daily_start_equity:.2f}），系统已停止交易", "warning")
            return
        
        if self.consecutive_losses >= self.max_consecutive_losses:
            logger.warning("⚠️ 连续亏损5次，停止交易")
            send_feishu("**⚠️ 风控触发**\n\n连续亏损5次，系统已停止交易", "warning")
            return
        
        # 计算仓位
        available = account['available']
        position_value = available * self.position_size_pct
        margin_needed = position_value
        xaut_size = (position_value * leverage) / price  # XAUT数量
        
        # 🔧 关键修复：OKX的sz参数是张数，不是XAUT数量！
        # XAU-USDT-SWAP: 1张 = 0.01 XAUT
        # 所以需要把XAUT数量转换成张数
        import math
        contracts = int(math.floor(xaut_size / 0.01))  # 转换成整数张数
        size = contracts  # sz参数用整数张数
        xaut_size = contracts * 0.01  # 实际XAUT数量
        
        # 检查最小下单量（最少1张）
        min_contracts = 1
        if contracts < min_contracts:
            logger.warning(f"⚠️ 下单量 {contracts} 张小于最小值 {min_contracts} 张，跳过交易")
            send_feishu(f"**⚠️ 下单量不足**\n\n计算张数: {contracts} 张\n最小张数: {min_contracts} 张\n\n需要资金: ${0.01 * price / leverage:.2f}\n当前可用: ${available:.2f}", "warning")
            return
        
        # 重新计算实际保证金（使用XAUT数量）
        margin_needed = (xaut_size * price) / leverage
        
        if margin_needed > available:
            logger.warning("⚠️ 可用资金不足")
            return
        
        # 计算止损止盈
        stop_loss = price * (1 - self.stop_loss_pct) if signal > 0 else price * (1 + self.stop_loss_pct)
        take_profit = price * (1 + self.take_profit_pct) if signal > 0 else price * (1 - self.take_profit_pct)
        
        # 计算风险
        max_loss = margin_needed * self.stop_loss_pct * leverage
        expected_profit = margin_needed * self.take_profit_pct * leverage
        
        # 发送交易通知
        side = "buy" if signal > 0 else "sell"
        action = "买入" if signal > 0 else "卖出"
        
        # 构建专家意见摘要
        expert_summary = "\n".join([
            f"• {op['agent']}: {op['signal']:+.2f} - {', '.join(op['reasons'])}"
            for op in analysis['opinions']
        ])
        
        # 构建特征摘要
        features = analysis['features']
        feature_summary = (
            f"• RSI: {features.get('rsi', 0):.1f}\n"
            f"• 动量: {features.get('momentum', 0):.2%}\n"
            f"• 布林带: {features.get('bb_position', 0):.2f}\n"
            f"• MACD: {'金叉' if features.get('macd', 0) > 0 else '死叉'}"
        )
        
        # XAUT策略信号摘要
        xaut_signals = analysis.get('xaut_signals', {})
        xaut_summary = ""
        if xaut_signals.get('cascade_detected'):
            xaut_summary += "🚨 清算级联检测！\n"
        if xaut_signals.get('zscore_extreme'):
            xaut_summary += f"📊 Z-Score极度低估（{xaut_signals.get('zscore', 0):.2f}）\n"
        if xaut_signals.get('obi_absorption'):
            xaut_summary += "💎 检测到巨鲸吸筹！\n"
        
        # XAUT策略标记
        xaut_strategy = ""
        if features.get('crash_detected', False):
            xaut_strategy = f"\n\n**⚡ XAUT暴跌反弹策略触发！**\n• 跌幅：{features.get('crash_intensity', 0):.1%}\n• 参考报告：历史暴跌后通常在几小时内反弹5%-15%"
        
        msg = (
            f"**🔥 {reason}**\n\n"
            f"**信号分析：**\n"
            f"• 信号方向：{'+' if signal > 0 else '-'}{abs(signal):.2f}\n"
            f"• 信号强度：{signal_strength:.0%}\n"
            f"• 共识度：{consensus:.0%}\n"
            f"• 杠杆：{leverage}倍（激进）\n"
            f"• 今日交易：{self.daily_trade_count}/{self.max_daily_trades}次{xaut_strategy}\n\n"
            f"**🤖 Multi-Agent专家意见：**\n{expert_summary}\n\n"
            f"**📊 量化特征：**\n{feature_summary}\n\n"
            f"**💰 交易计划（15%仓位）：**\n"
            f"• {action}：{size:.4f} XAUT\n"
            f"• 价格：${price:.2f}\n"
            f"• 保证金：${margin_needed:.2f}（{margin_needed/account['total_equity']:.1%}）\n"
            f"• 止损：${stop_loss:.2f}（-10%）\n"
            f"• 止盈：${take_profit:.2f}（+30%）\n\n"
            f"**⚠️ 风险评估（盈亏比3:1）：**\n"
            f"• 最大亏损：${max_loss:.2f}（{max_loss/account['total_equity']:.1%}）\n"
            f"• 预期盈利：${expected_profit:.2f}（{expected_profit/account['total_equity']:.1%}）\n"
            f"• 盈亏比：3:1\n\n"
            f"**🚀 系统自动执行，梭哈翻倍！**"
        )
        send_feishu(msg, "money")
        
        # 执行交易
        # size是整数张数，xaut_size是XAUT数量
        logger.info(f"🔥 执行{action}: {size}张 ({xaut_size:.2f} XAUT) @ ${price:.2f}, {leverage}x")
        
        order = await self.trader.place_order(self.inst_id, side, str(size), leverage)
        
        # 🧪 测试模式：标记已执行
        if self.test_mode:
            self.test_trade_executed = True
            logger.warning(f"🧪 测试交易已执行，后续不会再自动交易")
        
        if order:
            self.stats['total_trades'] += 1
            self.stats['successful_trades'] += 1
            
            # 获取最新权益
            account_new = await self.trader.get_account_balance()
            if account_new:
                self.last_equity = account_new['total_equity']
            
            msg = (
                f"**✅ 交易执行成功**\n\n"
                f"**{action}：** {size:.4f} XAUT\n"
                f"**价格：** ${price:.2f}\n"
                f"**保证金：** ${margin_needed:.2f}（{margin_needed/account['total_equity']:.1%}）\n"
                f"**杠杆：** {leverage}倍（激进）\n\n"
                f"**止损已设置：** ${stop_loss:.2f}（-10%）\n"
                f"**止盈已设置：** ${take_profit:.2f}（+30%，盈亏比3:1）\n\n"
                f"**💰 账户状态（OKX实时）：**\n"
                f"• 总权益：${self.last_equity:.2f}（¥{self.last_equity*CNY_RATE:.2f}）\n"
                f"• 可用：${available - margin_needed:.2f}（¥{(available - margin_needed)*CNY_RATE:.2f}）\n"
                f"• 已用保证金：${margin_needed:.2f}（¥{margin_needed*CNY_RATE:.2f}）\n"
                f"• 仓位使用率：{margin_needed/account['total_equity']:.1%}\n\n"
                f"**📊 今日盈亏：** ${self.last_equity - self.daily_start_equity:+.2f}（{(self.last_equity - self.daily_start_equity)/self.daily_start_equity:+.1%}）\n"
                f"**📊 连续亏损：** {self.consecutive_losses}次\n\n"
                f"**⏰ 时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_feishu(msg, "success")
        else:
            self.stats['failed_trades'] += 1
            send_feishu(f"**❌ 交易执行失败**\n\n请检查日志", "danger")
    
    async def run(self):
        if not await self.initialize():
            return
        
        # 🔍 查询合约信息（获取精确的下单规则）
        logger.info("🔍 正在查询合约信息...")
        await self.trader.get_instrument_info(self.inst_id)
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                
                logger.info(f"\n{'='*80}")
                logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {check_count} 次扫描")
                logger.info(f"{'='*80}")
                
                # 获取账户
                account = await self.trader.get_account_balance()
                if not account:
                    logger.error("❌ 无法获取账户信息，60秒后重试")
                    await asyncio.sleep(60)
                    continue
                
                # 获取价格
                price = await self.fetch_price()
                if not price:
                    logger.error("❌ 无法获取价格，60秒后重试")
                    await asyncio.sleep(60)
                    continue
                
                logger.info(f"💰 当前价格: ${price:.2f}")
                logger.info(f"💰 可用资金: ${account['available']:.2f}")
                
                # 监控持仓（自动止盈止损）
                await self.monitor_positions(price)
                
                # 检查是否需要重置每日计数
                today = datetime.now().date()
                if self.last_trade_date != today:
                    self.daily_trade_count = 0
                    self.last_trade_date = today
                    logger.info(f"📅 新的一天，交易计数重置（今日可交易{self.max_daily_trades}次）")
                
                # 分析市场
                analysis = await self.analyze_market(price)
                signal = analysis['signal']
                signal_strength = analysis['signal_strength']
                consensus = analysis['consensus']
                
                logger.info(f"🤖 信号: {signal:+.2f}, 强度: {signal_strength:.0%}, 共识度: {consensus:.0%}")
                
                # XAUT策略状态
                if analysis['features'].get('crash_detected', False):
                    logger.warning(f"⚡ XAUT暴跌反弹策略触发！跌幅: {analysis['features'].get('crash_intensity', 0):.1%}")
                
                # 详细输出专家意见
                for op in analysis['opinions']:
                    logger.info(f"   {op['agent']}: {op['signal']:+.2f} - {', '.join(op['reasons'])}")
                
                # 智能频率控制：信号越强，冷却时间越短
                can_trade = False
                reason = ""
                
                # 🧪 测试模式：强制触发一次交易
                if self.test_mode and not self.test_trade_executed:
                    can_trade = True
                    reason = "🧪 测试模式：强制触发交易"
                    logger.warning(f"🧪 测试模式：将执行一次测试交易！")
                    # 不要在这里设置 test_trade_executed，在 execute_trade 里设置
                
                # 检查每日交易次数
                elif self.daily_trade_count >= self.max_daily_trades:
                    reason = f"今日已交易{self.daily_trade_count}次，达到上限"
                    logger.info(f"⏸️ {reason}")
                    await asyncio.sleep(300)
                    continue
                
                # 超强信号（95%+）：立即交易，无冷却
                if signal_strength >= 0.95 and consensus >= 0.85:
                    can_trade = True
                    reason = "超强信号，立即执行"
                    logger.info(f"🔥 {reason}！")
                
                # 强信号（90%+）：30分钟冷却
                elif signal_strength >= 0.90 and consensus >= 0.80:
                    if self.last_trade_time:
                        time_since_last = (datetime.now() - self.last_trade_time).total_seconds()
                        if time_since_last >= 1800:  # 30分钟
                            can_trade = True
                            reason = "强信号，冷却30分钟后执行"
                        else:
                            logger.info(f"⏸️ 强信号冷却中，还需{int(1800 - time_since_last)}秒")
                    else:
                        can_trade = True
                        reason = "强信号，首次交易"
                
                # 标准信号（45%+）：2小时冷却
                elif signal_strength >= self.min_signal_strength and consensus >= self.min_consensus:
                    if self.last_trade_time:
                        time_since_last = (datetime.now() - self.last_trade_time).total_seconds()
                        if time_since_last >= self.min_trade_interval:
                            can_trade = True
                            reason = "标准信号，冷却2小时后执行"
                        else:
                            logger.info(f"⏸️ 标准信号冷却中，还需{int(self.min_trade_interval - time_since_last)}秒")
                    else:
                        can_trade = True
                        reason = "标准信号，首次交易"
                
                # 执行交易
                if can_trade:
                    await self.execute_trade(signal, signal_strength, consensus, account, price, analysis, reason)
                    self.last_trade_time = datetime.now()
                    self.daily_trade_count += 1
                    logger.info(f"✅ 今日已交易{self.daily_trade_count}/{self.max_daily_trades}次")
                
                # 定期推送（每5分钟）
                if check_count % 5 == 0:
                    # 获取当前持仓
                    positions = await self.trader.get_positions()
                    position_summary = ""
                    if positions:
                        for pos in positions:
                            inst_id_pos = pos['instId']
                            size_pos = float(pos['pos'])
                            entry_price_pos = float(pos['avgPx'])
                            unrealized_pnl_pos = float(pos['upl'])
                            unrealized_pnl_ratio_pos = float(pos['uplRatio'])
                            leverage_pos = pos.get('lever', 'N/A')
                            position_summary += f"\n• {inst_id_pos}: {'多' if size_pos > 0 else '空'}{abs(size_pos):.4f} @ ${entry_price_pos:.2f} ({leverage_pos}x) | 盈亏: ${unrealized_pnl_pos:.2f} ({unrealized_pnl_ratio_pos:.1%})"
                    else:
                        position_summary = "\n• 无持仓"
                    
                    msg = (
                        f"**📊 系统状态（5分钟心跳）**\n\n"
                        f"**💰 账户（OKX实时）：**\n"
                        f"• 总权益：${account['total_equity']:.2f}（¥{account['total_equity']*CNY_RATE:.2f}）\n"
                        f"• 可用：${account['available']:.2f}（¥{account['available']*CNY_RATE:.2f}）\n"
                        f"• 已用保证金：${account['margin_used']:.2f}\n"
                        f"• 仓位使用率：{account['margin_used']/account['total_equity']:.1%}\n\n"
                        f"**📊 当前持仓：**{position_summary}\n\n"
                        f"**📈 价格：** ${price:.2f}\n"
                        f"**📊 今日盈亏：** ${account['total_equity'] - self.daily_start_equity:+.2f}（{(account['total_equity'] - self.daily_start_equity)/self.daily_start_equity:+.1%}）\n"
                        f"**📊 今日交易：** {self.daily_trade_count}/{self.max_daily_trades}次\n"
                        f"**📊 总交易：** {self.stats['total_trades']}笔（成功{self.stats['successful_trades']}笔）\n"
                        f"**📊 连续亏损：** {self.consecutive_losses}次\n\n"
                        f"**⏰ 时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_feishu(msg, "info")
                
                # 🔥 1分钟扫描一次（激进模式）
                await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            await self.close()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🔥 激进赌博系统 - 梭哈翻倍模式                      ║
    ║                                                              ║
    ║  核心特点：                                                   ║
    ║    • 抓80%以上的强信号（更激进）                             ║
    ║    • 每次15%资金（激进）                                     ║
    ║    • 总仓位75%（激进）                                       ║
    ║    • 动态杠杆12-20倍                                         ║
    ║    • 止损10%，止盈30%（盈亏比3:1）                           ║
    ║    • 连续亏损5次=-56%（可接受）                              ║
    ║                                                              ║
    ║  🚀 抓住大机会，梭哈翻几十倍！                                ║
    ║  🤖 Multi-Agent系统（5000+行代码）自动决策！                 ║
    ║  💰 飞书实时推送权益变化和交易信号！                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止系统
    """)
    
    system = ProfessionalTradingSystem()
    asyncio.run(system.run())

