"""
狙击手智能体 (The Sniper)
职能：执行层 - 路由订单、延迟套利、分片执行、挂单管理
运行频率：< 10ms (毫秒级响应)
"""

import asyncio
import ccxt.async_support as ccxt
import redis
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("狙击手")


@dataclass
class Order:
    """订单数据结构"""
    exchange: str
    symbol: str
    side: str  # buy/sell
    type: str  # limit/market
    price: float
    amount: float
    order_id: Optional[str] = None
    status: str = "pending"
    filled: float = 0.0
    timestamp: float = 0.0


class 阶梯式接针策略:
    """技能7: 阶梯式接针策略 (Ladder Sniping)"""
    
    def __init__(self, total_capital_usdt: float = 100_000):
        self.total_capital = total_capital_usdt
        self.position_ratios = [0.10, 0.15, 0.20, 0.25, 0.30]  # 10%, 15%, 20%, 25%, 30%
        
    def calculate_ladder_orders(
        self, 
        current_price: float, 
        atr: float,
        signal_confidence: float
    ) -> List[Order]:
        """
        计算阶梯式挂单
        
        策略：
        - 将资金分成5份，按10%, 15%, 20%, 25%, 30%分配
        - 根据ATR设定挂单间隔
        - 越深的价位，仓位越重（金字塔加仓）
        
        参数:
            current_price: 当前价格
            atr: 平均真实波幅
            signal_confidence: 信号置信度 (0-1)
        """
        orders = []
        
        # 根据置信度调整资金使用率
        effective_capital = self.total_capital * signal_confidence
        
        # 挂单价位（基于ATR的动态间隔）
        price_levels = [
            current_price * 0.995,  # -0.5%
            current_price * 0.990,  # -1.0%
            current_price * 0.982,  # -1.8%
            current_price * 0.970,  # -3.0%
            current_price * 0.950   # -5.0% (深度价值买入)
        ]
        
        for i, (ratio, price) in enumerate(zip(self.position_ratios, price_levels)):
            capital_for_order = effective_capital * ratio
            amount = capital_for_order / price
            
            order = Order(
                exchange="okx",
                symbol="XAUT/USDT",
                side="buy",
                type="limit",
                price=round(price, 2),
                amount=round(amount, 4),
                timestamp=time.time()
            )
            orders.append(order)
            
            logger.info(f"📍 阶梯订单 #{i+1}: ${price:.2f} × {amount:.4f} XAUT (${capital_for_order:,.0f})")
        
        return orders
    
    def calculate_trailing_stop(
        self, 
        entry_price: float, 
        current_price: float,
        trailing_pct: float = 0.015
    ) -> float:
        """
        计算追踪止盈价格
        
        策略：
        - 价格反弹后，动态上移止盈线
        - 保护利润，避免"坐电梯"
        
        参数:
            entry_price: 入场价格
            current_price: 当前价格
            trailing_pct: 追踪百分比 (默认1.5%)
        """
        profit_pct = (current_price - entry_price) / entry_price
        
        if profit_pct > 0.03:  # 盈利超过3%时启动追踪止盈
            stop_price = current_price * (1 - trailing_pct)
            return stop_price
        
        return 0.0  # 未达到启动条件


class 延迟套利路由器:
    """技能8: 延迟套利路由 (Latency Arbitrage Routing)"""
    
    def __init__(self):
        self.exchange_latencies = {}  # 记录各交易所延迟
        
    async def measure_latency(self, exchange: ccxt.Exchange) -> float:
        """测量交易所API延迟"""
        start = time.time()
        try:
            await exchange.fetch_ticker('BTC/USDT')
            latency = (time.time() - start) * 1000  # 毫秒
            return latency
        except:
            return 9999.0
    
    async def detect_price_lag(
        self, 
        exchanges: Dict[str, ccxt.Exchange],
        symbol: str = "XAUT/USDT"
    ) -> Optional[Dict]:
        """
        检测交易所间的价格滞后
        
        策略：
        - OKX先跌，Gate.io滞后几百毫秒
        - 在滞后交易所挂低价买单，等待价格传导
        
        返回:
            {
                'fast_exchange': 'okx',
                'slow_exchange': 'gate',
                'price_diff': 0.015,  # 1.5%
                'opportunity': 'buy_on_slow'
            }
        """
        prices = {}
        
        # 并发获取所有交易所价格
        tasks = []
        for name, exchange in exchanges.items():
            tasks.append(self._fetch_price(name, exchange, symbol))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                prices.update(result)
        
        if len(prices) < 2:
            return None
        
        # 找出最高价和最低价
        sorted_prices = sorted(prices.items(), key=lambda x: x[1])
        lowest_exchange, lowest_price = sorted_prices[0]
        highest_exchange, highest_price = sorted_prices[-1]
        
        price_diff_pct = (highest_price - lowest_price) / lowest_price
        
        # 如果价差超过1%，存在套利机会
        if price_diff_pct > 0.01:
            logger.warning(f"⚡ 延迟套利机会: {highest_exchange}(${highest_price:.2f}) vs {lowest_exchange}(${lowest_price:.2f}), 价差{price_diff_pct:.2%}")
            return {
                'fast_exchange': lowest_exchange,  # 先跌的
                'slow_exchange': highest_exchange,  # 滞后的
                'price_diff': price_diff_pct,
                'opportunity': 'buy_on_fast_sell_on_slow'
            }
        
        return None
    
    async def _fetch_price(self, name: str, exchange: ccxt.Exchange, symbol: str) -> Dict:
        """获取单个交易所价格"""
        try:
            ticker = await exchange.fetch_ticker(symbol)
            return {name: ticker['last']}
        except Exception as e:
            logger.error(f"获取{name}价格失败: {e}")
            return {}


class 冰山订单执行器:
    """技能9: 冰山订单与TWAP (Iceberg & TWAP)"""
    
    def __init__(self):
        self.max_order_size = 10  # 单笔最大10 XAUT
        
    async def execute_twap(
        self,
        exchange: ccxt.Exchange,
        symbol: str,
        side: str,
        total_amount: float,
        duration_seconds: int = 60
    ) -> List[Order]:
        """
        时间加权平均价格执行
        
        策略：
        - 将大单拆分成小单
        - 在指定时间内均匀执行
        - 降低市场冲击
        
        参数:
            total_amount: 总数量
            duration_seconds: 执行时长（秒）
        """
        num_orders = int(total_amount / self.max_order_size) + 1
        amount_per_order = total_amount / num_orders
        interval = duration_seconds / num_orders
        
        orders = []
        
        logger.info(f"🧊 冰山订单: 将{total_amount:.2f} XAUT拆分为{num_orders}笔")
        
        for i in range(num_orders):
            try:
                # 获取当前市场价
                ticker = await exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # 市价单执行
                order = await exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=side,
                    amount=amount_per_order
                )
                
                orders.append(Order(
                    exchange=exchange.id,
                    symbol=symbol,
                    side=side,
                    type='market',
                    price=current_price,
                    amount=amount_per_order,
                    order_id=order['id'],
                    status='filled',
                    filled=amount_per_order,
                    timestamp=time.time()
                ))
                
                logger.info(f"✅ TWAP订单 {i+1}/{num_orders} 已执行")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"TWAP执行失败: {e}")
        
        return orders


class 狙击手智能体:
    """
    狙击手智能体主控制器
    
    职责：
    1. 接收分析师信号
    2. 执行阶梯式接针
    3. 管理订单生命周期
    4. 追踪止盈
    """
    
    def __init__(self, redis_host: str = 'localhost', api_keys: Dict = None):
        self.redis_client = redis.Redis(host=redis_host, decode_responses=True)
        
        # 初始化交易所
        self.exchanges = {}
        if api_keys:
            for name, keys in api_keys.items():
                if name == 'okx':
                    self.exchanges[name] = ccxt.okx({
                        'apiKey': keys['api_key'],
                        'secret': keys['secret'],
                        'password': keys['password'],
                        'enableRateLimit': True
                    })
                elif name == 'bybit':
                    self.exchanges[name] = ccxt.bybit({
                        'apiKey': keys['api_key'],
                        'secret': keys['secret'],
                        'enableRateLimit': True
                    })
        
        self.阶梯策略 = 阶梯式接针策略(total_capital_usdt=100_000)
        self.延迟套利 = 延迟套利路由器()
        self.冰山执行 = 冰山订单执行器()
        
        self.active_orders: List[Order] = []
        self.positions: Dict[str, float] = {}  # {symbol: amount}
        
    async def listen_for_signals(self):
        """监听分析师信号"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('signal:ANALYSIS')
        
        logger.info("🎯 狙击手就位，等待信号...")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    signal = data['signal']
                    market_data = data['market_data']
                    
                    if signal['action'] in ['STRONG_BUY', 'BUY']:
                        await self.execute_buy_strategy(signal, market_data)
                    elif signal['action'] in ['STRONG_SELL', 'SELL']:
                        await self.execute_sell_strategy(signal, market_data)
                        
                except Exception as e:
                    logger.error(f"处理信号失败: {e}")
    
    async def execute_buy_strategy(self, signal: Dict, market_data: Dict):
        """执行买入策略"""
        logger.info(f"🔫 收到买入信号: {signal['action']} (置信度: {signal['confidence']:.2%})")
        
        # 检查DEFCON等级
        defcon = int(self.redis_client.get('defcon_level') or 5)
        if defcon == 1:
            logger.critical("⛔ DEFCON 1: 拒绝执行买入（TETHER风险）")
            return
        
        current_price = market_data['xaut_price']
        
        # 计算ATR（简化版，实际需要历史数据）
        atr = current_price * 0.02  # 假设ATR为价格的2%
        
        # 生成阶梯订单
        orders = self.阶梯策略.calculate_ladder_orders(
            current_price=current_price,
            atr=atr,
            signal_confidence=signal['confidence']
        )
        
        # 执行订单
        for order in orders:
            try:
                if 'okx' in self.exchanges:
                    exchange = self.exchanges['okx']
                    result = await exchange.create_limit_buy_order(
                        symbol=order.symbol,
                        amount=order.amount,
                        price=order.price
                    )
                    order.order_id = result['id']
                    order.status = 'open'
                    self.active_orders.append(order)
                    logger.info(f"✅ 订单已挂: {order.price} × {order.amount}")
                else:
                    logger.warning("⚠️ 未配置交易所API，模拟执行")
                    
            except Exception as e:
                logger.error(f"订单执行失败: {e}")
    
    async def execute_sell_strategy(self, signal: Dict, market_data: Dict):
        """执行卖出策略"""
        logger.info(f"💰 收到卖出信号: {signal['action']}")
        
        # 检查持仓
        position = self.positions.get('XAUT/USDT', 0)
        if position == 0:
            logger.info("无持仓，跳过卖出")
            return
        
        # 使用TWAP执行大额卖出
        if position > 50:
            await self.冰山执行.execute_twap(
                exchange=self.exchanges.get('okx'),
                symbol='XAUT/USDT',
                side='sell',
                total_amount=position,
                duration_seconds=60
            )
        else:
            # 小额直接市价卖出
            try:
                if 'okx' in self.exchanges:
                    await self.exchanges['okx'].create_market_sell_order(
                        symbol='XAUT/USDT',
                        amount=position
                    )
                    logger.info(f"✅ 已卖出 {position} XAUT")
                    self.positions['XAUT/USDT'] = 0
            except Exception as e:
                logger.error(f"卖出失败: {e}")
    
    async def monitor_orders(self):
        """监控订单状态"""
        while True:
            try:
                for order in self.active_orders:
                    if order.status == 'open' and 'okx' in self.exchanges:
                        # 查询订单状态
                        result = await self.exchanges['okx'].fetch_order(
                            id=order.order_id,
                            symbol=order.symbol
                        )
                        
                        if result['status'] == 'closed':
                            order.status = 'filled'
                            order.filled = result['filled']
                            
                            # 更新持仓
                            current_position = self.positions.get(order.symbol, 0)
                            self.positions[order.symbol] = current_position + order.filled
                            
                            logger.info(f"🎉 订单成交: {order.price} × {order.filled} XAUT")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"订单监控错误: {e}")
                await asyncio.sleep(5)
    
    async def monitor_trailing_stop(self):
        """监控追踪止盈"""
        while True:
            try:
                for symbol, position in self.positions.items():
                    if position > 0 and 'okx' in self.exchanges:
                        # 获取当前价格
                        ticker = await self.exchanges['okx'].fetch_ticker(symbol)
                        current_price = ticker['last']
                        
                        # 计算平均入场价（简化）
                        filled_orders = [o for o in self.active_orders if o.status == 'filled']
                        if filled_orders:
                            avg_entry = np.average(
                                [o.price for o in filled_orders],
                                weights=[o.filled for o in filled_orders]
                            )
                            
                            # 计算追踪止盈价
                            stop_price = self.阶梯策略.calculate_trailing_stop(
                                entry_price=avg_entry,
                                current_price=current_price
                            )
                            
                            if stop_price > 0 and current_price < stop_price:
                                logger.info(f"🛑 触发追踪止盈: {current_price} < {stop_price}")
                                # 执行卖出
                                await self.execute_sell_strategy(
                                    {'action': 'SELL'},
                                    {'xaut_price': current_price}
                                )
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"追踪止盈错误: {e}")
                await asyncio.sleep(10)
    
    async def run(self):
        """启动狙击手"""
        logger.info("🎯 狙击手智能体启动")
        tasks = [
            self.listen_for_signals(),
            self.monitor_orders(),
            self.monitor_trailing_stop()
        ]
        await asyncio.gather(*tasks)
    
    async def close(self):
        """关闭交易所连接"""
        for exchange in self.exchanges.values():
            await exchange.close()


if __name__ == "__main__":
    # 示例：需要配置真实API密钥
    api_keys = {
        'okx': {
            'api_key': 'YOUR_API_KEY',
            'secret': 'YOUR_SECRET',
            'password': 'YOUR_PASSWORD'
        }
    }
    
    sniper = 狙击手智能体(api_keys=api_keys)
    try:
        asyncio.run(sniper.run())
    finally:
        asyncio.run(sniper.close())

