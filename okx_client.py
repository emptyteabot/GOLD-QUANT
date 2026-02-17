"""
OKX API客户端
"""
import logging
import asyncio
import aiohttp
import hmac
import hashlib
import base64
import json
from datetime import datetime
from typing import Dict, List, Optional
import config

logger = logging.getLogger(__name__)


class OKXClient:
    """OKX交易客户端"""
    
    def __init__(self):
        self.api_key = config.OKX_API_KEY
        self.secret_key = config.OKX_SECRET_KEY
        self.passphrase = config.OKX_PASSPHRASE
        self.base_url = "https://www.okx.com"
        self.session = None
    
    async def initialize(self):
        """初始化会话"""
        self.session = aiohttp.ClientSession()
        logger.info("✅ OKX客户端已初始化")
    
    async def close(self):
        """关闭会话"""
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
        """发送请求"""
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
            proxy = config.HTTP_PROXY
            
            if method == 'GET':
                async with self.session.get(url, headers=headers, timeout=10, proxy=proxy) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('code') == '0':
                            return data.get('data')
                        else:
                            logger.error(f"API错误: {data.get('msg')}")
            elif method == 'POST':
                async with self.session.post(url, headers=headers, data=body, timeout=10, proxy=proxy) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('code') == '0':
                            return data.get('data')
                        else:
                            # 打印完整错误信息
                            logger.error(f"API错误: {data.get('msg')}")
                            logger.error(f"完整响应: {data}")
                    else:
                        logger.error(f"HTTP错误: {resp.status}")
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
    
    async def get_positions(self, inst_id: str = None) -> List[Dict]:
        """获取持仓（包括SWAP永续合约）"""
        path = '/api/v5/account/positions?instType=SWAP'
        if inst_id:
            path += f'&instId={inst_id}'
        
        data = await self._request('GET', path)
        if data:
            return [pos for pos in data if float(pos.get('pos', 0)) != 0]
        return []
    
    async def get_margin_balance(self) -> Optional[Dict]:
        """获取现货杠杆账户余额"""
        data = await self._request('GET', '/api/v5/account/balance')
        if data and len(data) > 0:
            # 查找所有币种的余额
            all_balances = {}
            for account in data:
                details = account.get('details', [])
                for detail in details:
                    ccy = detail.get('ccy')
                    eq_str = detail.get('eq', '0')
                    eq = float(eq_str) if eq_str else 0
                    if eq > 0.001:  # 只显示有余额的币种
                        # 安全转换，处理空字符串
                        def safe_float(val, default=0):
                            try:
                                return float(val) if val else default
                            except (ValueError, TypeError):
                                return default
                        
                        all_balances[ccy] = {
                            'equity': eq,
                            'available': safe_float(detail.get('availBal')),
                            'frozen': safe_float(detail.get('frozenBal')),
                            'borrowed': safe_float(detail.get('borrowed')),
                            'interest': safe_float(detail.get('interest'))
                        }
            return all_balances
        return None
    
    async def get_all_positions(self) -> Dict:
        """获取所有类型的持仓（SWAP + 现货杠杆）"""
        result = {
            'swap_positions': [],
            'margin_balances': {},
            'total_equity_usdt': 0
        }
        
        # 1. 获取SWAP永续合约持仓
        swap_positions = await self.get_positions()
        result['swap_positions'] = swap_positions
        
        # 2. 获取现货杠杆余额
        margin_balances = await self.get_margin_balance()
        if margin_balances:
            result['margin_balances'] = margin_balances
        
        # 3. 计算总权益（USDT计价）
        account = await self.get_account_balance()
        if account:
            result['total_equity_usdt'] = account['total_equity']
        
        return result
    
    async def get_ticker(self, inst_id: str) -> Optional[float]:
        """获取最新价格"""
        try:
            url = f"{self.base_url}/api/v5/market/ticker?instId={inst_id}"
            proxy = config.HTTP_PROXY
            
            async with self.session.get(url, timeout=10, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('code') == '0' and data.get('data'):
                        price = float(data['data'][0]['last'])
                        logger.info(f"📈 从OKX获取价格: ${price:.2f} (合约: {inst_id})")
                        return price
        except Exception as e:
            logger.error(f"获取价格失败: {e}")
        return None
    
    async def get_klines(self, inst_id: str, bar: str = '1H', limit: int = 100) -> Optional[List]:
        """
        获取K线数据（支持超过300根）
        
        OKX API单次最多300根，需要多次请求拼接
        """
        all_klines = []
        remaining = limit
        after = None  # 用于分页
        
        try:
            while remaining > 0:
                batch_size = min(remaining, 300)  # OKX最多300根
                url = f"{self.base_url}/api/v5/market/candles?instId={inst_id}&bar={bar}&limit={batch_size}"
                if after:
                    url += f"&after={after}"
                
                proxy = config.HTTP_PROXY
                
                async with self.session.get(url, timeout=15, proxy=proxy) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('code') == '0':
                            klines = data.get('data', [])
                            if not klines:
                                break  # 没有更多数据
                            
                            all_klines.extend(klines)
                            remaining -= len(klines)
                            
                            # 获取最后一根K线的时间戳，用于下一次请求
                            after = klines[-1][0]
                            
                            if len(klines) < batch_size:
                                break  # 数据不足，说明已经到头了
                        else:
                            break
                    else:
                        break
            
            logger.info(f"📊 获取到 {len(all_klines)} 根K线 ({inst_id}, {bar})")
            return all_klines if all_klines else None
            
        except Exception as e:
            logger.error(f"获取K线失败: {e}")
        return None
    
    async def get_instrument_info(self, inst_id: str) -> Optional[Dict]:
        """查询合约信息（公开接口）"""
        try:
            url = f"{self.base_url}/api/v5/public/instruments?instType=SWAP&instId={inst_id}"
            proxy = config.HTTP_PROXY
            
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
        except Exception as e:
            logger.error(f"查询合约信息异常: {e}")
        return None
    
    async def place_order(self, inst_id: str, side: str, size: float, leverage: int = None, reduce_only: bool = False, pos_side: str = None) -> Optional[Dict]:
        """
        下单
        
        Args:
            inst_id: 合约ID
            side: buy/sell
            size: 数量
            leverage: 杠杆（可选，不传则使用现有杠杆设置）
            reduce_only: 是否只减仓（平仓时使用）
            pos_side: 持仓方向 (long/short)，双向持仓模式必填
        """
        order_data = {
            "instId": inst_id,
            "tdMode": "cross",
            "side": side,
            "ordType": "market",
            "sz": str(int(size))
        }
        
        # 双向持仓模式需要指定持仓方向
        if pos_side:
            order_data["posSide"] = pos_side
        else:
            # 默认根据side推断：buy=long, sell=short（开仓）
            order_data["posSide"] = "long" if side == "buy" else "short"
        
        # 平仓时添加reduceOnly参数
        if reduce_only:
            order_data["reduceOnly"] = "true"
        
        body = json.dumps(order_data)
        
        logger.info(f"📤 准备下单: {order_data}")
        
        data = await self._request('POST', '/api/v5/trade/order', body)
        if data and len(data) > 0:
            order = data[0]
            if order.get('sCode') == '0':
                logger.info(f"✅ 下单成功: {order.get('ordId')}")
                return order
            else:
                logger.error(f"❌ 下单失败: {order.get('sMsg')}")
        return None
    
    async def set_leverage(self, inst_id: str, leverage: int, mode: str = 'cross'):
        """设置杠杆"""
        body = json.dumps({
            "instId": inst_id,
            "lever": str(leverage),
            "mgnMode": mode
        })
        
        data = await self._request('POST', '/api/v5/account/set-leverage', body)
        if data:
            logger.info(f"✅ 杠杆已设置为 {leverage}x")
            return True
        return False


if __name__ == "__main__":
    # 测试
    async def test():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        client = OKXClient()
        await client.initialize()
        
        # 测试获取价格
        price = await client.get_ticker(config.INST_ID)
        print(f"价格: ${price}")
        
        # 测试获取账户
        account = await client.get_account_balance()
        print(f"账户: {account}")
        
        await client.close()
    
    asyncio.run(test())

